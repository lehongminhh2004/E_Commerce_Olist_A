import streamlit as st
import plotly.express as px
import pandas as pd

from src.data_processing import (
    get_delivery_data,
    get_filter_metadata,
    get_sla_simulation_data,
)
from src.utils import kpi_card


st.set_page_config(page_title="Delivery & Logistics", page_icon="🚚", layout="wide")

st.title("🚚 Delivery & Logistics")

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

# ====== LOAD DATA ======
data = get_delivery_data(
    start_date=start_date,
    end_date=end_date,
    states=states_filter,
)

kpis = data["kpis"]
profit_by_state = data.get("profit_by_state")

# ====== KPI: DELIVERY ======
st.subheader("🚚 Delivery KPIs")
col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card(
        "Avg Delivery Time (days)",
        kpis["avg_delivery_time"],
        format_str="{:.1f}",
    )
with col2:
    kpi_card(
        "Median Delivery Time",
        kpis["median_delivery_time"],
        format_str="{:.1f}",
    )
with col3:
    kpi_card(
        "% Late Delivery",
        kpis["late_rate"] * 100
        if kpis["late_rate"] is not None
        else None,
        format_str="{:.1f}%",
    )
with col4:
    kpi_card(
        "Avg Freight Value",
        kpis["avg_freight"],
        format_str="{:,.2f}",
    )

# ====== KPI: COST & PROFIT (NEW) ======
st.markdown("### 💰 Shipping Cost & Profit")
c5, c6, c7, c8 = st.columns(4)
with c5:
    kpi_card(
        "Total Shipping Cost",
        kpis.get("total_shipping_cost"),
        format_str="{:,.0f}",
    )
with c6:
    shipping_share = kpis.get("shipping_cost_share")
    kpi_card(
        "Shipping / Revenue",
        shipping_share * 100 if shipping_share is not None else None,
        format_str="{:.1f}%",
    )
with c7:
    kpi_card(
        "Profit After Shipping",
        kpis.get("total_profit_after_shipping"),
        format_str="{:,.0f}",
    )
with c8:
    margin = kpis.get("profit_margin_after_shipping")
    kpi_card(
        "Profit Margin (After Shipping)",
        margin * 100 if margin is not None else None,
        format_str="{:.1f}%",
    )

# ====== DISTRIBUTION & STATE PERFORMANCE ======
col1, col2 = st.columns(2)

with col1:
    st.subheader("Phân bố thời gian giao hàng (days)")
    df_dist = data["delivery_distribution"]
    if df_dist.empty:
        st.warning("Không có dữ liệu delivery_distribution với bộ lọc hiện tại.")
    else:
        fig_hist = px.histogram(df_dist, x="delivery_time_days", nbins=40)
        fig_hist.update_layout(
            xaxis_title="Delivery time (days)",
            yaxis_title="Count",
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    st.subheader("Delivery Performance by State")
    df_state = data["delivery_by_state"]
    if df_state.empty:
        st.warning("Không có dữ liệu delivery_by_state với bộ lọc hiện tại.")
    else:
        fig_state = px.bar(
            df_state,
            x="customer_state",
            y="avg_delivery_time",
            hover_data=["late_rate", "n_orders"],
        )
        fig_state.update_layout(
            xaxis_title="Customer State",
            yaxis_title="Avg Delivery Time (days)",
        )
        st.plotly_chart(fig_state, use_container_width=True)

st.subheader("Top States có thời gian giao hàng lâu nhất")
df_state = data["delivery_by_state"]
if df_state.empty:
    st.info("Không có dữ liệu để hiển thị top state.")
else:
    st.dataframe(df_state.head(10))

# ====== BUBBLE CHART: DELIVERY RISK ======
st.markdown("---")
st.header("📍 Delivery performance theo bang (bubble chart)")

df_state = data["delivery_by_state"].copy()
if df_state.empty:
    st.warning("Không có dữ liệu để hiển thị với bộ lọc hiện tại.")
else:
    df_state["late_rate_pct"] = df_state["late_rate"] * 100

    st.caption(
        "Mỗi điểm = 1 bang. Trục X: thời gian giao hàng trung bình (ngày), "
        "Trục Y: % đơn giao trễ. Kích thước bong bóng ~ số lượng đơn."
    )

    fig_bubble = px.scatter(
        df_state,
        x="avg_delivery_time",
        y="late_rate_pct",
        size="n_orders",
        hover_name="customer_state",
        labels={
            "avg_delivery_time": "Avg delivery time (days)",
            "late_rate_pct": "Late delivery rate (%)",
            "n_orders": "Number of orders",
        },
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

# ====== NEW: PROFIT MARGIN BY STATE ======
st.markdown("---")
st.header("💹 Profit margin sau shipping theo bang")

if profit_by_state is None or profit_by_state.empty:
    st.warning("Không có dữ liệu profit_by_state với bộ lọc hiện tại.")
else:
    df_profit_state = profit_by_state.copy()
    df_profit_state["profit_margin_pct"] = (
        df_profit_state["profit_margin_after_shipping"] * 100
    )

    fig_profit_state = px.bar(
        df_profit_state.sort_values("profit_margin_pct", ascending=True),
        x="customer_state",
        y="profit_margin_pct",
        labels={
            "customer_state": "Bang (state)",
            "profit_margin_pct": "Profit margin sau shipping (%)",
        },
        title="Profit margin sau shipping theo bang",
    )
    st.plotly_chart(fig_profit_state, use_container_width=True)

    st.caption(
        "Biểu đồ cho thấy sự khác biệt về lợi nhuận sau khi trừ chi phí vận chuyển (freight) "
        "giữa các bang. Các bang xa trung tâm thường có freight cao → profit margin thấp hơn."
    )

# ====== SLA SIMULATOR ======
st.markdown("---")
st.header("⚙️ What-if: Cải thiện SLA giao hàng")

sla_data = get_sla_simulation_data(
    start_date=start_date,
    end_date=end_date,
    states=states_filter,
)
baseline = sla_data["baseline"]

if baseline is None:
    st.warning("Không đủ dữ liệu để mô phỏng SLA với bộ lọc hiện tại.")
else:
    slope = sla_data["review_slope_per_day"]
    max_delta = sla_data["max_reduction_days"]

    st.caption(
        "Giả định: nếu giảm thời gian giao hàng trung bình, tỷ lệ giao trễ sẽ giảm "
        "tuyến tính và điểm review thay đổi theo mối quan hệ hiện tại giữa delay và rating."
    )

    delta_days = st.slider(
        "Giảm thời gian giao hàng trung bình (ngày)",
        min_value=0.0,
        max_value=float(max_delta),
        value=2.0,
        step=0.5,
    )

    cur_time = baseline["avg_delivery_time"]
    cur_late = baseline["late_rate"]
    cur_review = baseline["avg_review"]

    new_time = max(cur_time - delta_days, 0)

    k = cur_late / max_delta if max_delta > 0 else 0
    new_late = max(cur_late - k * delta_days, 0)

    new_review = cur_review + slope * (new_time - cur_time)
    new_review = min(max(new_review, 1.0), 5.0)

    col_cur, col_new = st.columns(2)

    with col_cur:
        st.subheader("Hiện tại")
        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card("Avg delivery (days)", cur_time, format_str="{:.1f}")
        with c2:
            kpi_card("Late rate", cur_late * 100, format_str="{:.1f}%")
        with c3:
            kpi_card("Avg review", cur_review, format_str="{:.2f}")

    with col_new:
        st.subheader("Sau cải thiện (mô phỏng)")
        n1, n2, n3 = st.columns(3)
        with n1:
            kpi_card("Avg delivery (days)", new_time, format_str="{:.1f}")
        with n2:
            kpi_card("Late rate", new_late * 100, format_str="{:.1f}%")
        with n3:
            kpi_card("Avg review", new_review, format_str="{:.2f}")

    st.subheader("So sánh Before vs After")

    comp_df = pd.DataFrame(
        {
            "metric": [
                "Avg delivery time (days)",
                "Late rate (%)",
                "Avg review score",
            ],
            "Current": [cur_time, cur_late * 100, cur_review],
            "Simulated": [new_time, new_late * 100, new_review],
        }
    )

    fig_comp = px.bar(
        comp_df,
        x="metric",
        y=["Current", "Simulated"],
        barmode="group",
        labels={"value": "Value", "metric": ""},
    )
    st.plotly_chart(fig_comp, use_container_width=True)
