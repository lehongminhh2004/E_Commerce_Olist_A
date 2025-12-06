import streamlit as st

st.set_page_config(
    page_title="Olist E-commerce Analytics",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Olist E-commerce Analytics")
st.markdown(
    """
    Đây là ứng dụng Streamlit phân tích dữ liệu sàn thương mại điện tử Olist (Brazil)

    - **Overview**: Tình hình kinh doanh tổng quan  
    - **Sales & Product**: Phân tích doanh thu theo sản phẩm & seller  
    - **Delivery & Logistics**: Hiệu suất giao hàng & vận hành  
    - **Customer & Reviews**: Trải nghiệm & đánh giá khách hàng  

    Hãy chọn từng tab ở sidebar để xem chi tiết.
    """
)
