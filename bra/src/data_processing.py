import pandas as pd
import numpy as np
import streamlit as st

from .load_data import load_all_data


@st.cache_data(show_spinner="Đang xử lý dữ liệu Olist...")
def get_base_tables() -> dict:
    """
    Chuẩn hóa kiểu dữ liệu + tạo các bảng cơ bản để dùng cho nhiều tab.
    """
    data = load_all_data()

    orders = data["orders"].copy()
    customers = data["customers"].copy()
    order_items = data["order_items"].copy()
    payments = data["payments"].copy()
    reviews = data["reviews"].copy()
    products = data["products"].copy()
    sellers = data["sellers"].copy()
    cat_trans = data["category_translation"].copy()

    # ----- Chuẩn hóa datetime -----
    datetime_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in datetime_cols:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col])

    # ----- Tạo ngày & tháng mua -----
    orders["purchase_date"] = orders["order_purchase_timestamp"].dt.date
    orders["purchase_month"] = orders["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()

    # ----- Join order_items với products + category translation -----
    items_prod = order_items.merge(products, on="product_id", how="left")

    items_prod = items_prod.merge(
        cat_trans,
        on="product_category_name",
        how="left",
        suffixes=("", "_en"),
    )

    # Tên category “đẹp”
    items_prod["category_name"] = items_prod["product_category_name_english"].fillna(
        items_prod["product_category_name"]
    )

    # ----- Agg theo order_id để lấy tổng price + freight + quantity -----
    items_by_order = (
        items_prod.groupby("order_id", as_index=False)
        .agg(
            n_items=("order_item_id", "count"),
            n_products=("product_id", "nunique"),
            price_total=("price", "sum"),
            freight_total=("freight_value", "sum"),
        )
    )

    # ----- Agg payments theo order_id -----
    payments_by_order = (
        payments.groupby("order_id", as_index=False)
        .agg(
            payment_value=("payment_value", "sum"),
            main_payment_type=("payment_type", lambda x: x.iloc[0]),
        )
    )

    # ----- Agg reviews theo order_id -----
    reviews_by_order = (
        reviews.groupby("order_id", as_index=False)
        .agg(
            review_score=("review_score", "mean"),
            n_reviews=("review_id", "count"),
        )
    )

    # ----- Join orders + customers + items + payments + reviews -----
    orders_enriched = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(items_by_order, on="order_id", how="left")
        .merge(payments_by_order, on="order_id", how="left")
        .merge(reviews_by_order, on="order_id", how="left")
    )

    # Doanh thu = price + freight
    orders_enriched["revenue"] = (
        orders_enriched["price_total"].fillna(0) + orders_enriched["freight_total"].fillna(0)
    )

    # Thời gian giao hàng (days)
    orders_enriched["delivery_time_days"] = (
        orders_enriched["order_delivered_customer_date"]
        - orders_enriched["order_purchase_timestamp"]
    ).dt.days

    # Flag giao trễ
    orders_enriched["is_late"] = (
        orders_enriched["order_delivered_customer_date"]
        > orders_enriched["order_estimated_delivery_date"]
    )

    # Customer repeat
    cust_order_counts = (
        orders_enriched.groupby("customer_unique_id")["order_id"]
        .nunique()
        .rename("customer_order_count")
    )
    orders_enriched = orders_enriched.merge(
        cust_order_counts, on="customer_unique_id", how="left"
    )
    orders_enriched["is_repeat_customer"] = orders_enriched["customer_order_count"] > 1

    # Lưu thêm bảng items_prod để dùng cho phân tích category/seller
    return {
        "orders_enriched": orders_enriched,
        "items_prod": items_prod,
        "sellers": sellers,
        "payments": payments,
        "reviews": reviews,
    }

@st.cache_data(show_spinner=False)
def get_filter_metadata():
    """
    Trả về thông tin dùng để tạo bộ lọc chung:
    - min/max ngày mua
    - list state
    """
    base = get_base_tables()
    df = base["orders_enriched"].copy()

    min_date = df["order_purchase_timestamp"].min().date()
    max_date = df["order_purchase_timestamp"].max().date()
    states = sorted(df["customer_state"].dropna().unique().tolist())

    return {
        "min_date": min_date,
        "max_date": max_date,
        "states": states,
    }


# ========== HÀM CHO TỪNG TAB ==========

def get_overview_data(start_date=None, end_date=None, states=None):
    base = get_base_tables()
    df = base["orders_enriched"].copy()
    items = base["items_prod"].copy()

    # ----- ÁP DỤNG BỘ LỌC -----
    if start_date is not None:
        df = df[df["order_purchase_timestamp"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        # +1 ngày để inclusive end_date
        df = df[df["order_purchase_timestamp"] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    if states:
        df = df[df["customer_state"].isin(states)]

    # Filter items theo order còn lại
    order_ids = df["order_id"].unique().tolist()
    items = items[items["order_id"].isin(order_ids)]

    # Bỏ những dòng không có status
    df_valid = df[~df["order_status"].isna()].copy()

    # Delivered orders
    delivered = df_valid[df_valid["order_status"] == "delivered"].copy()

    # ----- KPI chính -----
    total_orders_delivered = delivered["order_id"].nunique()
    total_revenue = delivered["revenue"].sum()
    avg_order_value = (
        total_revenue / total_orders_delivered if total_orders_delivered else 0
    )
    avg_review_score = delivered["review_score"].mean()

    time_min = delivered["order_purchase_timestamp"].min()
    time_max = delivered["order_purchase_timestamp"].max()

    kpis = {
        "total_orders": int(total_orders_delivered),
        "total_revenue": float(total_revenue),
        "avg_order_value": float(avg_order_value),
        "avg_review_score": float(avg_review_score)
        if not np.isnan(avg_review_score)
        else None,
        "time_min": time_min,
        "time_max": time_max,
    }

    # ----- Revenue theo tháng -----
    revenue_by_month = (
        delivered.groupby("purchase_month", as_index=False)
        .agg(revenue=("revenue", "sum"))
    )

    # ----- Orders theo status -----
    orders_by_status = (
        df_valid.groupby("order_status", as_index=False)
        .agg(n_orders=("order_id", "nunique"))
        .sort_values("n_orders", ascending=False)
    )

    # ----- Revenue theo category -----
    items["revenue"] = items["price"] + items["freight_value"]
    revenue_by_category = (
        items.groupby("category_name", as_index=False)
        .agg(revenue=("revenue", "sum"))
        .sort_values("revenue", ascending=False)
    )

    # ===== BUSINESS FUNNEL =====
    total_orders_all = df_valid["order_id"].nunique()
    approved_orders = df_valid[~df_valid["order_approved_at"].isna()][
        "order_id"
    ].nunique()
    delivered_orders = delivered["order_id"].nunique()
    reviewed_orders = df_valid[~df_valid["review_score"].isna()][
        "order_id"
    ].nunique()

    stages = ["Created", "Approved", "Delivered", "Reviewed"]
    counts = [
        total_orders_all,
        approved_orders,
        delivered_orders,
        reviewed_orders,
    ]

    funnel = pd.DataFrame({"stage": stages, "count": counts})
    funnel["pct_of_prev"] = funnel["count"] / funnel["count"].shift(1)
    funnel.loc[0, "pct_of_prev"] = 1.0  # 100% ở bước đầu

    # ===== CUSTOMER SUMMARY (Retention / Repeat) =====
    n_customers = df_valid["customer_unique_id"].nunique()

    repeat_pct = df_valid["is_repeat_customer"].mean()
    total_rev = total_revenue
    repeat_rev = delivered[delivered["is_repeat_customer"]]["revenue"].sum()
    repeat_rev_share = repeat_rev / total_rev if total_rev > 0 else np.nan

    customer_summary = {
        "n_customers": int(n_customers),
        "repeat_pct": float(repeat_pct) if not np.isnan(repeat_pct) else None,
        "repeat_revenue_share": float(repeat_rev_share)
        if not np.isnan(repeat_rev_share)
        else None,
    }

    return {
        "kpis": kpis,
        "revenue_by_month": revenue_by_month,
        "orders_by_status": orders_by_status,
        "revenue_by_category": revenue_by_category,
        "funnel": funnel,
        "customer_summary": customer_summary,
    }



def get_sales_product_data(start_date=None, end_date=None, states=None):
    base = get_base_tables()
    orders = base["orders_enriched"].copy()
    items = base["items_prod"].copy()
    payments = base["payments"].copy()

    # ----- FILTER -----
    if start_date is not None:
        orders = orders[orders["order_purchase_timestamp"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        orders = orders[orders["order_purchase_timestamp"] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    if states:
        orders = orders[orders["customer_state"].isin(states)]

    order_ids = orders["order_id"].unique().tolist()
    items = items[items["order_id"].isin(order_ids)]
    payments = payments[payments["order_id"].isin(order_ids)]

    # Revenue cho từng item
    items["revenue"] = items["price"] + items["freight_value"]

    # Top category
    revenue_by_category = (
        items.groupby("category_name", as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_qty=("order_item_id", "count"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    # Top sellers
    revenue_by_seller = (
        items.groupby("seller_id", as_index=False)
        .agg(
            total_revenue=("revenue", "sum"),
            total_orders=("order_id", "nunique"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    # Payment type
    revenue_by_payment = (
        payments.groupby("payment_type", as_index=False)
        .agg(
            total_payment=("payment_value", "sum"),
            n_orders=("order_id", "nunique"),
        )
        .sort_values("total_payment", ascending=False)
    )

    # Bảng top products
    top_products = (
        items.groupby(["product_id", "category_name"], as_index=False)
        .agg(
            total_qty=("order_item_id", "count"),
            total_revenue=("revenue", "sum"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    # Avg items per order (chỉ delivered)
    delivered = orders[orders["order_status"] == "delivered"].copy()
    avg_items_per_order = delivered["n_items"].mean()

    kpis = {
        "avg_items_per_order": float(avg_items_per_order) if not np.isnan(avg_items_per_order) else None,
    }

    return {
        "kpis": kpis,
        "revenue_by_category": revenue_by_category,
        "revenue_by_seller": revenue_by_seller,
        "revenue_by_payment": revenue_by_payment,
        "top_products": top_products,
    }



def get_delivery_data(start_date=None, end_date=None, states=None):
    base = get_base_tables()
    df = base["orders_enriched"].copy()

    # FILTER
    if start_date is not None:
        df = df[df["order_purchase_timestamp"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        df = df[df["order_purchase_timestamp"] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    if states:
        df = df[df["customer_state"].isin(states)]

    delivered = df[df["order_status"] == "delivered"].copy()
    delivered = delivered[~delivered["delivery_time_days"].isna()].copy()

    avg_delivery_time = delivered["delivery_time_days"].mean()
    median_delivery_time = delivered["delivery_time_days"].median()
    late_rate = delivered["is_late"].mean()  # 0–1
    avg_freight = delivered["freight_total"].mean()

    kpis = {
        "avg_delivery_time": float(avg_delivery_time) if not np.isnan(avg_delivery_time) else None,
        "median_delivery_time": float(median_delivery_time) if not np.isnan(median_delivery_time) else None,
        "late_rate": float(late_rate) if not np.isnan(late_rate) else None,
        "avg_freight": float(avg_freight) if not np.isnan(avg_freight) else None,
    }

    # Histogram data
    delivery_distribution = delivered[["delivery_time_days"]].copy()

    # Delivery by state
    delivery_by_state = (
        delivered.groupby("customer_state", as_index=False)
        .agg(
            avg_delivery_time=("delivery_time_days", "mean"),
            late_rate=("is_late", "mean"),
            n_orders=("order_id", "nunique"),
        )
        .sort_values("avg_delivery_time", ascending=False)
    )

    return {
        "kpis": kpis,
        "delivery_distribution": delivery_distribution,
        "delivery_by_state": delivery_by_state,
    }



def get_customer_reviews_data(start_date=None, end_date=None, states=None):
    base = get_base_tables()
    orders = base["orders_enriched"].copy()
    items = base["items_prod"].copy()

    # FILTER
    if start_date is not None:
        orders = orders[orders["order_purchase_timestamp"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        orders = orders[orders["order_purchase_timestamp"] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
    if states:
        orders = orders[orders["customer_state"].isin(states)]

    order_ids = orders["order_id"].unique().tolist()
    items = items[items["order_id"].isin(order_ids)]

    # Chỉ lấy delivered có review
    df = orders[
        (orders["order_status"] == "delivered")
        & (~orders["review_score"].isna())
    ].copy()

    if df.empty:
        return {
            "kpis": {"avg_review_score": None, "pct_negative": None, "pct_positive": None},
            "review_dist": pd.DataFrame(),
            "review_by_category": pd.DataFrame(),
            "review_by_bucket": pd.DataFrame(),
            "low_review_categories": pd.DataFrame(),
        }

    avg_review_score = df["review_score"].mean()
    pct_neg = (df["review_score"] <= 2).mean()
    pct_pos = (df["review_score"] >= 4).mean()

    kpis = {
        "avg_review_score": float(avg_review_score),
        "pct_negative": float(pct_neg),
        "pct_positive": float(pct_pos),
    }

    # Distribution
    review_dist = (
        df.groupby("review_score", as_index=False)
        .agg(n_orders=("order_id", "nunique"))
        .sort_values("review_score")
    )

    # Review by category
    items_rev = items.merge(
        df[["order_id", "review_score"]], on="order_id", how="inner"
    )
    review_by_category = (
        items_rev.groupby("category_name", as_index=False)
        .agg(
            avg_review=("review_score", "mean"),
            n_orders=("order_id", "nunique"),
        )
        .sort_values("avg_review", ascending=True)
    )

    # Bucket theo delivery time
    df_bucket = df.copy()
    bins = [-1, 5, 15, 9999]
    labels = ["Fast (<5d)", "Normal (5–15d)", "Slow (>15d)"]
    df_bucket["delivery_bucket"] = pd.cut(
        df_bucket["delivery_time_days"], bins=bins, labels=labels
    )
    review_by_bucket = (
        df_bucket.groupby("delivery_bucket", as_index=False)
        .agg(
            avg_review=("review_score", "mean"),
            n_orders=("order_id", "nunique"),
        )
    )

    # Top 10 category review thấp
    low_review_categories = review_by_category.nsmallest(10, "avg_review")

    return {
        "kpis": kpis,
        "review_dist": review_dist,
        "review_by_category": review_by_category,
        "review_by_bucket": review_by_bucket,
        "low_review_categories": low_review_categories,
    }



@st.cache_data(show_spinner="Đang chuẩn bị dữ liệu bản đồ giao hàng...")
def get_delivery_geo_data(start_date=None, end_date=None, states=None):
    """
    Trả về dữ liệu đã tổng hợp theo bang để vẽ bản đồ:
    - lat/lng trung bình của khách hàng trong bang
    - avg_delivery_time
    - late_rate
    - n_orders
    """
    base = get_base_tables()
    orders = base["orders_enriched"].copy()
    data = load_all_data()

    customers = data["customers"].copy()
    geo = data["geolocation"].copy()

    # ===== FILTER THEO THỜI GIAN + STATE =====
    if start_date is not None:
        orders = orders[
            orders["order_purchase_timestamp"] >= pd.to_datetime(start_date)
        ]
    if end_date is not None:
        orders = orders[
            orders["order_purchase_timestamp"]
            < pd.to_datetime(end_date) + pd.Timedelta(days=1)
        ]
    if states:
        orders = orders[orders["customer_state"].isin(states)]

    delivered = orders[orders["order_status"] == "delivered"].copy()
    delivered = delivered[~delivered["delivery_time_days"].isna()].copy()

    if delivered.empty:
        return {"state_map": pd.DataFrame()}

    # ===== LẤY TOẠ ĐỘ KHÁCH HÀNG =====
    # Gộp geolocation theo zip prefix để giảm trùng
    geo_zip = (
        geo.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            lat=("geolocation_lat", "mean"),
            lng=("geolocation_lng", "mean"),
        )
    )

    cust_geo = customers.merge(
        geo_zip,
        left_on="customer_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
    )[
        ["customer_id", "lat", "lng"]
    ]

    # Join vào đơn hàng
    delivered_geo = delivered.merge(
        cust_geo, on="customer_id", how="left"
    )

    # Bỏ những dòng không có lat/lng
    delivered_geo = delivered_geo.dropna(subset=["lat", "lng"])

    if delivered_geo.empty:
        return {"state_map": pd.DataFrame()}

    # ===== AGG THEO BANG =====
    state_map = (
        delivered_geo.groupby("customer_state", as_index=False)
        .agg(
            lat=("lat", "mean"),
            lng=("lng", "mean"),
            avg_delivery_time=("delivery_time_days", "mean"),
            late_rate=("is_late", "mean"),
            n_orders=("order_id", "nunique"),
        )
        .sort_values("n_orders", ascending=False)
    )

    return {"state_map": state_map}



@st.cache_data(show_spinner="Đang phân tích ảnh hưởng giao trễ lên review...")
def get_delay_impact_data(start_date=None, end_date=None, states=None):
    """
    Phân tích ảnh hưởng của giao trễ (is_late) lên review_score.
    Trả về:
    - df_by_late: bảng avg review theo Late / On-time
    """
    base = get_base_tables()
    orders = base["orders_enriched"].copy()

    # Lọc theo thời gian + state giống các hàm khác
    if start_date is not None:
        orders = orders[
            orders["order_purchase_timestamp"] >= pd.to_datetime(start_date)
        ]
    if end_date is not None:
        orders = orders[
            orders["order_purchase_timestamp"]
            < pd.to_datetime(end_date) + pd.Timedelta(days=1)
        ]
    if states:
        orders = orders[orders["customer_state"].isin(states)]

    df = orders[
        (orders["order_status"] == "delivered")
        & (~orders["review_score"].isna())
        & (~orders["is_late"].isna())
    ].copy()

    if df.empty:
        return {"df_by_late": pd.DataFrame()}

    df_by_late = (
        df.groupby("is_late", as_index=False)
        .agg(
            avg_review=("review_score", "mean"),
            n_orders=("order_id", "nunique"),
        )
    )

    # Đổi True/False thành label dễ hiểu
    df_by_late["delivery_status"] = df_by_late["is_late"].map(
        {False: "On-time", True: "Late"}
    )

    # Sắp xếp để On-time lên trước
    df_by_late = df_by_late.sort_values("delivery_status")

    return {"df_by_late": df_by_late}



@st.cache_data(show_spinner="Đang chuẩn bị dữ liệu SLA simulator...")
def get_sla_simulation_data(start_date=None, end_date=None, states=None, max_reduction_days: int = 5):
    """
    Chuẩn bị dữ liệu cho mô phỏng cải thiện SLA giao hàng.

    Trả về:
    - baseline: các chỉ số hiện tại (avg_delivery_time, late_rate, avg_review)
    - review_slope_per_day: ước lượng mức thay đổi review khi delivery_time thay đổi 1 ngày
    - max_reduction_days: số ngày tối đa cho slider mô phỏng
    """
    base = get_base_tables()
    orders = base["orders_enriched"].copy()

    # Lọc giống các hàm khác
    if start_date is not None:
        orders = orders[orders["order_purchase_timestamp"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        orders = orders[
            orders["order_purchase_timestamp"]
            < pd.to_datetime(end_date) + pd.Timedelta(days=1)
        ]
    if states:
        orders = orders[orders["customer_state"].isin(states)]

    df = orders[
        (orders["order_status"] == "delivered")
        & (~orders["delivery_time_days"].isna())
        & (~orders["review_score"].isna())
        & (~orders["is_late"].isna())
    ].copy()

    if df.empty:
        return {
            "baseline": None,
            "review_slope_per_day": 0.0,
            "max_reduction_days": max_reduction_days,
        }

    # ===== CHỈ SỐ HIỆN TẠI (BASELINE) =====
    baseline_avg_delivery = df["delivery_time_days"].mean()
    baseline_late_rate = df["is_late"].mean()
    baseline_avg_review = df["review_score"].mean()
    n_orders = df["order_id"].nunique()

    baseline = {
        "avg_delivery_time": float(baseline_avg_delivery),
        "late_rate": float(baseline_late_rate),
        "avg_review": float(baseline_avg_review),
        "n_orders": int(n_orders),
    }

    # ===== ƯỚC LƯỢNG TÁC ĐỘNG DELAY -> REVIEW (SLOPE) =====
    on_time = df[df["is_late"] == False].copy()
    late = df[df["is_late"] == True].copy()

    if not on_time.empty and not late.empty:
        avg_time_on = on_time["delivery_time_days"].mean()
        avg_time_late = late["delivery_time_days"].mean()
        avg_review_on = on_time["review_score"].mean()
        avg_review_late = late["review_score"].mean()

        dt = avg_time_late - avg_time_on  # chênh thời gian
        dr = avg_review_late - avg_review_on  # chênh điểm (thường là âm)

        if dt != 0:
            review_slope_per_day = dr / dt  # thay đổi review / 1 ngày delivery
        else:
            review_slope_per_day = 0.0
    else:
        review_slope_per_day = 0.0

    return {
        "baseline": baseline,
        "review_slope_per_day": float(review_slope_per_day),
        "max_reduction_days": max_reduction_days,
    }



@st.cache_data(show_spinner="Đang tính toán RFM segmentation...")
def get_rfm_data():
    """
    Tính RFM (Recency, Frequency, Monetary) cho từng customer_unique_id.
    Dùng toàn bộ lịch sử delivered order.
    """
    base = get_base_tables()
    orders = base["orders_enriched"].copy()

    # Chỉ lấy đơn đã giao + có revenue hợp lệ
    df = orders[
        (orders["order_status"] == "delivered")
        & (~orders["revenue"].isna())
    ].copy()

    if df.empty:
        return {
            "rfm": pd.DataFrame(),
            "summary": {},
        }

    # Ngày tham chiếu = ngày mua gần nhất trong dataset
    max_date = df["order_purchase_timestamp"].max().normalize()

    rfm = (
        df.groupby("customer_unique_id")
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("revenue", "sum"),
        )
        .reset_index()
    )

    # Recency (số ngày kể từ lần mua gần nhất đến max_date)
    rfm["recency_days"] = (max_date - rfm["last_purchase"].dt.normalize()).dt.days

    # Tính score theo quantile 5 mức (1–5)
    def _score_quantile(series, reverse=False):
        # reverse=True cho Recency (ít ngày → điểm cao)
        try:
            q = series.quantile([0.2, 0.4, 0.6, 0.8]).to_list()
        except Exception:
            # Trường hợp data quá nhỏ
            return pd.Series([3] * len(series), index=series.index)

        def _assign(val):
            if val <= q[0]:
                s = 1
            elif val <= q[1]:
                s = 2
            elif val <= q[2]:
                s = 3
            elif val <= q[3]:
                s = 4
            else:
                s = 5
            if reverse:
                return 6 - s
            return s

        return series.apply(_assign)

    rfm["R_score"] = _score_quantile(rfm["recency_days"], reverse=True)
    rfm["F_score"] = _score_quantile(rfm["frequency"], reverse=False)
    rfm["M_score"] = _score_quantile(rfm["monetary"], reverse=False)

    rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

    # Segment rule đơn giản
    def _segment(row):
        if row["RFM_score"] >= 13:
            return "VIP"
        if row["RFM_score"] >= 10:
            return "Loyal"
        if row["RFM_score"] >= 7:
            return "Regular"
        if row["RFM_score"] >= 5:
            return "At Risk"
        return "Lost"

    rfm["segment"] = rfm.apply(_segment, axis=1)

    # Summary cho KPI
    total_customers = len(rfm)
    vip_pct = (rfm["segment"] == "VIP").mean() if total_customers else 0
    at_risk_pct = (rfm["segment"] == "At Risk").mean() if total_customers else 0

    summary = {
        "total_customers": int(total_customers),
        "vip_pct": float(vip_pct),
        "at_risk_pct": float(at_risk_pct),
    }

    return {
        "rfm": rfm,
        "summary": summary,
    }
