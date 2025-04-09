import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import os
import time

st.set_page_config(page_title="Instacart Dashboard", layout="wide")
st.title("🛒 Instacart User Purchase Trends Dashboard")

st.markdown("""
Welcome to the interactive dashboard built on the Instacart dataset! 

This dashboard helps you explore:
- Top reordered products
- Basket size trends
- Shopping patterns by time and department
- Reorder behavior across departments

Use the sidebar to filter and interact with the data.
""")

# Load data
@st.cache_data(show_spinner=False)
def load_data():
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "instacart.db"))
    products = pd.read_sql("SELECT * FROM products", conn)
    orders = pd.read_sql("SELECT * FROM orders", conn)
    order_products = pd.read_sql("SELECT * FROM order_products__prior", conn)
    departments = pd.read_sql("SELECT * FROM departments", conn)
    conn.close()
    return products, orders, order_products, departments

start = time.time()
products, orders, order_products, departments = load_data()
load_time = time.time() - start

# Merge datasets
@st.cache_data(show_spinner=False)
def prepare_merged(products, orders, order_products, departments):
    merged = order_products.merge(products, on='product_id')
    merged = merged.merge(orders, on='order_id')
    merged = merged.merge(departments, on='department_id')
    return merged

merged = prepare_merged(products, orders, order_products, departments)

# Sidebar Filters
st.sidebar.header("🔍 Filter Options")
top_n = st.sidebar.slider("Top N Products", min_value=5, max_value=30, value=10)
dept_options = merged["department"].unique()
selected_dept = st.sidebar.selectbox("Select Department", sorted(dept_options))
hour_range = st.sidebar.slider("Order Hour Range", 0, 23, (0, 23))

# Filter data
@st.cache_data(show_spinner=False)
def filter_data(merged, selected_dept, hour_range):
    return merged[(merged["department"] == selected_dept) & (merged["order_hour_of_day"].between(hour_range[0], hour_range[1]))]

filtered_df = filter_data(merged, selected_dept, hour_range)

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Orders", f"{filtered_df['order_id'].nunique():,}")
col2.metric("Avg. Basket Size", f"{filtered_df.groupby('order_id')['product_id'].count().mean():.2f}")
top_product = filtered_df[filtered_df['reordered'] == 1]['product_name'].value_counts().idxmax()
col3.metric("Top Reordered Product", top_product)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Top Products",
    "🛍️ Basket Size",
    "🕒 Hourly Trends",
    "📅 Weekly Trends",
    "🏷️ Department Reorders"
])

with tab1:
    st.subheader("🔝 Top Reordered Products")
    top_products = filtered_df[filtered_df["reordered"] == 1]["product_name"].value_counts().head(top_n)
    fig, ax = plt.subplots()
    top_products.plot(kind="barh", ax=ax, color="skyblue")
    ax.set_xlabel("Reorder Count")
    ax.set_ylabel("Product Name")
    ax.set_title("Top Reordered Products")
    st.pyplot(fig)

with tab2:
    st.subheader("🧺 Basket Size Distribution")
    basket_sizes = filtered_df.groupby("order_id")["product_id"].count()
    fig, ax = plt.subplots()
    sns.histplot(basket_sizes, bins=30, kde=True, color="orange", ax=ax)
    ax.set_title("Distribution of Basket Sizes")
    ax.set_xlabel("Items per Order")
    st.pyplot(fig)

with tab3:
    st.subheader("🕒 Orders by Hour of Day")
    fig, ax = plt.subplots()
    sns.countplot(x="order_hour_of_day", data=filtered_df, palette="Blues", ax=ax)
    ax.set_title("Orders by Hour")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Order Count")
    st.pyplot(fig)

with tab4:
    st.subheader("📆 Orders by Day of Week")
    fig, ax = plt.subplots()
    sns.countplot(x="order_dow", data=filtered_df, palette="Greens", ax=ax)
    ax.set_title("Orders by Day of Week (0 = Sunday)")
    ax.set_xlabel("Day of Week")
    st.pyplot(fig)

with tab5:
    st.subheader("📦 Reorder Ratio by Department")
    reorder_ratio = filtered_df.groupby("department")["reordered"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 10))
    reorder_ratio.plot(kind="barh", ax=ax, color="salmon")
    ax.set_xlabel("Reorder Ratio")
    ax.set_title("Average Reorder Ratio by Department")
    st.pyplot(fig)

# Footer: Show loading time
st.caption(f"⏱️ Page loaded in {load_time:.2f} seconds")
