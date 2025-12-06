import streamlit as st
import plotly.express as px

from src.data_processing import (
    get_customer_reviews_data,
    get_rfm_data,
    get_filter_metadata,
    get_delay_impact_data,
)
from src.utils import kpi_card

st.set_page_config(page_title="Customer & Reviews", page_icon="🧑‍💼", layout="wide")

st.title("🧑‍💼 Customer & Reviews")

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


data = get_customer_reviews_data(start_date=start_date, end_date=end_date, states=states_filter)

kpis = data["kpis"]

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Avg Review Score", kpis["avg_review_score"], format_str="{:.2f}")
with col2:
    kpi_card("% Negative (1–2★)", kpis["pct_negative"] * 100, format_str="{:.1f}%")
with col3:
    kpi_card("% Positive (4–5★)", kpis["pct_positive"] * 100, format_str="{:.1f}%")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribution of Review Scores")
    df_dist = data["review_dist"]
    fig_dist = px.bar(df_dist, x="review_score", y="n_orders")
    fig_dist.update_layout(xaxis_title="Review Score", yaxis_title="Number of Orders")
    st.plotly_chart(fig_dist, use_container_width=True)

with col2:
    st.subheader("Avg Review by Delivery Speed")
    df_bucket = data["review_by_bucket"]
    fig_bucket = px.bar(df_bucket, x="delivery_bucket", y="avg_review")
    fig_bucket.update_layout(xaxis_title="Delivery Bucket", yaxis_title="Avg Review Score")
    st.plotly_chart(fig_bucket, use_container_width=True)

# ===== IMPACT: DELAY vs REVIEW =====
st.markdown("---")
st.header("⏱️ Ảnh hưởng của giao trễ lên điểm đánh giá")

delay_data = get_delay_impact_data(
    start_date=start_date, end_date=end_date, states=states_filter
)
df_late = delay_data["df_by_late"]

if df_late.empty:
    st.warning("Không có dữ liệu review để phân tích giao trễ trong bộ lọc hiện tại.")
else:
    # Tính chênh lệch điểm trung bình
    if set(df_late["delivery_status"]) == {"On-time", "Late"}:
        avg_on_time = float(
            df_late[df_late["delivery_status"] == "On-time"]["avg_review"].iloc[0]
        )
        avg_late = float(
            df_late[df_late["delivery_status"] == "Late"]["avg_review"].iloc[0]
        )
        diff = avg_late - avg_on_time  # thường là số âm
    else:
        avg_on_time = avg_late = diff = None

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card(
            "Avg review – On-time",
            avg_on_time,
            format_str="{:.2f}" if avg_on_time is not None else None,
        )
    with c2:
        kpi_card(
            "Avg review – Late",
            avg_late,
            format_str="{:.2f}" if avg_late is not None else None,
        )
    with c3:
        kpi_card(
            "Chênh lệch (Late - On-time)",
            diff,
            format_str="{:.2f}" if diff is not None else None,
            help_text="Số âm nghĩa là giao trễ làm điểm review giảm.",
        )

    st.subheader("So sánh review theo trạng thái giao hàng")
    fig_late = px.bar(
        df_late,
        x="delivery_status",
        y="avg_review",
        color="delivery_status",
        text="avg_review",
        labels={
            "delivery_status": "Delivery status",
            "avg_review": "Average review score",
        },
    )
    fig_late.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    st.plotly_chart(fig_late, use_container_width=True)

st.subheader("Categories có review thấp nhất")
st.dataframe(data["low_review_categories"].head(10))


st.markdown("---")
st.header("👥 Customer Segmentation – RFM")

rfm_data = get_rfm_data()
rfm = rfm_data["rfm"]
rfm_summary = rfm_data["summary"]

if rfm.empty:
    st.warning("Không đủ dữ liệu để tính RFM.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card(
            "Số lượng khách hàng",
            rfm_summary["total_customers"],
            format_str="{:,.0f}",
        )
    with col2:
        kpi_card(
            "% khách hàng VIP",
            rfm_summary["vip_pct"] * 100,
            format_str="{:.1f}%",
        )
    with col3:
        kpi_card(
            "% khách hàng At Risk",
            rfm_summary["at_risk_pct"] * 100,
            format_str="{:.1f}%",
        )

    st.subheader("Phân bố khách hàng theo phân khúc")
    seg_counts = (
        rfm.groupby("segment", as_index=False)
        .agg(n_customers=("customer_unique_id", "count"))
        .sort_values("n_customers", ascending=False)
    )
    fig_seg = px.bar(seg_counts, x="segment", y="n_customers")
    fig_seg.update_layout(
        xaxis_title="Segment",
        yaxis_title="Số lượng khách hàng",
    )
    st.plotly_chart(fig_seg, use_container_width=True)

    st.subheader("Giá trị khách hàng theo Frequency & Monetary")
    # Lấy mẫu nếu quá nhiều điểm để vẽ nhẹ hơn
    rfm_sample = rfm.copy()
    if len(rfm_sample) > 5000:
        rfm_sample = rfm_sample.sample(5000, random_state=42)

    fig_scatter = px.scatter(
        rfm_sample,
        x="frequency",
        y="monetary",
        color="segment",
        hover_data=["recency_days"],
    )
    fig_scatter.update_layout(
        xaxis_title="Frequency (số đơn)",
        yaxis_title="Monetary (tổng doanh thu)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("Top khách hàng VIP (theo Monetary)")
    top_vip = (
        rfm[rfm["segment"] == "VIP"]
        .sort_values("monetary", ascending=False)
        .head(20)
    )
    st.dataframe(
        top_vip[
            [
                "customer_unique_id",
                "recency_days",
                "frequency",
                "monetary",
                "RFM_score",
            ]
        ]
    )
