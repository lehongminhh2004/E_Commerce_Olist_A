import streamlit as st
import plotly.express as px

from src.data_processing import get_overview_data, get_filter_metadata
from src.utils import kpi_card

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

st.title("📊 Overview – Business Summary")

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


data = get_overview_data(start_date=start_date, end_date=end_date, states=states_filter)

kpis = data["kpis"]

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Total Orders", kpis["total_orders"], format_str="{:,.0f}")
with col2:
    kpi_card("Total Revenue (BRL)", kpis["total_revenue"], format_str="{:,.2f}")
with col3:
    kpi_card("Avg Order Value", kpis["avg_order_value"], format_str="{:,.2f}")
with col4:
    kpi_card("Avg Review Score", kpis["avg_review_score"], format_str="{:.2f}")

st.caption(
    f"Time range: {kpis['time_min'].date()} → {kpis['time_max'].date()}"
)

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Doanh thu theo tháng")
    df_rev = data["revenue_by_month"]
    fig = px.line(df_rev, x="purchase_month", y="revenue", labels={
        "purchase_month": "Month",
        "revenue": "Revenue",
    })
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Số đơn theo trạng thái")
    df_status = data["orders_by_status"]
    fig2 = px.bar(df_status, x="order_status", y="n_orders", labels={
        "order_status": "Status",
        "n_orders": "Number of orders",
    })
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Doanh thu theo category (Top N)")
top_n = st.slider("Chọn số category hiển thị", min_value=5, max_value=30, value=10, step=5)
df_cat = data["revenue_by_category"].head(top_n)
fig3 = px.bar(df_cat, x="category_name", y="revenue")
fig3.update_layout(xaxis_title="Category", yaxis_title="Revenue")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.header("🧭 Business Funnel & Repeat Customers")

# ===== FUNNEL =====
funnel = data["funnel"]

col_f1, col_f2 = st.columns([2, 1])

with col_f1:
    st.subheader("Order Funnel: Created → Approved → Delivered → Reviewed")
    # Dùng bar đơn giản cho chắc, không phụ thuộc px.funnel
    fig_funnel = px.bar(
        funnel,
        x="stage",
        y="count",
        text="count",
        labels={"stage": "Stage", "count": "Number of Orders"},
    )
    fig_funnel.update_traces(textposition="outside")
    st.plotly_chart(fig_funnel, use_container_width=True)

with col_f2:
    st.subheader("Tỷ lệ giữ được qua từng bước")
    funnel_pct = funnel.copy()
    funnel_pct["pct_label"] = (funnel_pct["pct_of_prev"] * 100).round(1).astype(str) + "%"
    st.table(
        funnel_pct[["stage", "count", "pct_label"]].rename(
            columns={
                "stage": "Stage",
                "count": "Orders",
                "pct_label": "% vs previous",
            }
        )
    )

# ===== REPEAT CUSTOMERS =====
st.subheader("Customer Retention Overview")

cust = data["customer_summary"]
c1, c2, c3 = st.columns(3)

with c1:
    kpi_card("Số lượng khách hàng", cust["n_customers"], format_str="{:,.0f}")
with c2:
    kpi_card(
        "% khách hàng mua nhiều lần",
        cust["repeat_pct"] * 100 if cust["repeat_pct"] is not None else None,
        format_str="{:.1f}%",
    )
with c3:
    kpi_card(
        "Tỷ lệ doanh thu từ repeat customers",
        cust["repeat_revenue_share"] * 100
        if cust["repeat_revenue_share"] is not None
        else None,
        format_str="{:.1f}%",
    )
