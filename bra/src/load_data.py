from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


@st.cache_data(show_spinner="Đang load dữ liệu Olist...")
def load_customers() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_customers_dataset.csv")


@st.cache_data
def load_orders() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_orders_dataset.csv")


@st.cache_data
def load_order_items() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_order_items_dataset.csv")


@st.cache_data
def load_order_payments() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_order_payments_dataset.csv")


@st.cache_data
def load_order_reviews() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_order_reviews_dataset.csv")


@st.cache_data
def load_products() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_products_dataset.csv")


@st.cache_data
def load_sellers() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_sellers_dataset.csv")


@st.cache_data
def load_geolocation() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "olist_geolocation_dataset.csv")


@st.cache_data
def load_category_translation() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_DIR / "product_category_name_translation.csv")


@st.cache_data(show_spinner=False)
def load_all_data() -> dict:
    """Trả về dict chứa toàn bộ bảng gốc."""
    return {
        "customers": load_customers(),
        "orders": load_orders(),
        "order_items": load_order_items(),
        "payments": load_order_payments(),
        "reviews": load_order_reviews(),
        "products": load_products(),
        "sellers": load_sellers(),
        "geolocation": load_geolocation(),
        "category_translation": load_category_translation(),
    }
