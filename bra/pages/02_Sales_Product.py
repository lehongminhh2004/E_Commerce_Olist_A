import streamlit as st
import plotly.express as px

from src.data_processing import get_sales_product_data, get_filter_metadata
from src.utils import kpi_card


st.set_page_config(page_title="Sales & Product", page_icon="📈", layout="wide")

st.title("📈 Sales & Product Analytics")

# ====== SIDEBAR FILTER ======
meta = get_filter_metadata()
with st.sidebar:
    st.markdown("### 🔍 Bộ lọc chung")
    date_range = st.date_input(
        "Khoảng thời gian",
        value=(meta["min_date"], meta["max_date"]),
    )
    if isinstance(date_range, tuple):
        start_date, end_date = date_range
    else:
        start_date = meta["min_date"]
        end_date = meta["max_date"]

    state_options = ["All"] + meta["states"]
    state_sel = st.multiselect("Customer State", state_options, default=["All"])

    if "All" in state_sel:
        states_filter = None
    else:
        states_filter = state_sel


data = get_sales_product_data(start_date=start_date, end_date=end_date, states=states_filter)

kpis = data["kpis"]

col1, = st.columns(1)
with col1:
    kpi_card("Avg Items per Order", kpis["avg_items_per_order"], format_str="{:.2f}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue by Category (Top 15)")
    df_cat = data["revenue_by_category"].head(15)
    fig_cat = px.bar(df_cat, x="category_name", y="total_revenue")
    fig_cat.update_layout(xaxis_title="Category", yaxis_title="Revenue")
    st.plotly_chart(fig_cat, use_container_width=True)

with col2:
    st.subheader("Revenue by Seller (Top 10)")
    df_seller = data["revenue_by_seller"].head(10)
    fig_seller = px.bar(df_seller, x="seller_id", y="total_revenue")
    fig_seller.update_layout(xaxis_title="Seller", yaxis_title="Revenue")
    st.plotly_chart(fig_seller, use_container_width=True)

st.subheader("Revenue by Payment Type")
df_pay = data["revenue_by_payment"]
fig_pay = px.bar(df_pay, x="payment_type", y="total_payment")
fig_pay.update_layout(xaxis_title="Payment Type", yaxis_title="Total Payment")
st.plotly_chart(fig_pay, use_container_width=True)

st.subheader("Top Products")
df_prod = data["top_products"].head(20)
st.dataframe(df_prod)
