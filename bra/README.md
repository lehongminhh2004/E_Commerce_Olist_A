# 🛒 Olist E-Commerce Analytics Dashboard

### *Streamlit Dashboard for Business, Logistics & Customer Insights*

## 📌 1. Giới thiệu dự án

Dự án xây dựng một **Streamlit Dashboard** phân tích dữ liệu từ **Olist
-- Brazilian E-commerce Public Dataset** với hơn 100k đơn hàng, 70k
khách hàng, 3k sellers và dữ liệu logistics thực tế.

**Mục tiêu:** - Phân tích hiệu suất kinh doanh - Đánh giá vận hành giao
hàng - Phân tích trải nghiệm khách hàng

## 🎯 2. Mục tiêu phân tích (Business Questions)

### 1. Tình hình kinh doanh tổng quan

-   Revenue trend\
-   Order status\
-   Top categories & sellers\
-   Retention / repeat customers

### 2. Hiệu suất vận chuyển

-   Delivery time\
-   Late delivery rate\
-   Hiệu suất theo state\
-   Impact delivery → reviews\
-   **SLA Simulator (What-if Model)**

### 3. Trải nghiệm khách hàng

-   Review distribution\
-   Review theo category\
-   Review theo tốc độ giao hàng\
-   **RFM segmentation**

## 📂 3. Cấu trúc thư mục

    project/
    │── app.py
    │── README.md
    │── requirements.txt
    │
    ├── data/
    │   └── raw/
    │
    ├── src/
    │   ├── data_loader.py
    │   ├── data_processing.py
    │   ├── utils.py
    │
    └── pages/
        ├── 01_Overview.py
        ├── 02_Sales_Product.py
        ├── 03_Delivery_Logistics.py
        └── 04_Customer_Reviews.py

## 🧠 4. Pipeline xử lý dữ liệu

1.  Load toàn bộ 9 file Olist\
2.  Merge thành bảng chính: `orders_enriched`\
3.  Tính: delivery_time_days, is_late\
4.  Chuẩn hóa timestamp\
5.  Chuẩn bị bảng phân tích theo chủ đề\
6.  Cache cải thiện tốc độ

## 🖥 5. Mô tả Dashboard

### 🟦 TAB 1 -- Overview

-   KPI\
-   Revenue trend\
-   Order status\
-   Top categories\
-   Funnel & retention

### 🟧 TAB 2 -- Sales & Product Analytics

-   Top categories\
-   Top sellers\
-   Payment method\
-   Avg items/order\
-   Top products table

### 🟥 TAB 3 -- Delivery & Logistics

-   Delivery time\
-   Late rate\
-   Histogram & state chart\
-   Bubble performance\
-   **SLA Simulator (What-if Analysis)**

### 🟩 TAB 4 -- Customer & Reviews

-   Review distribution\
-   Review by category\
-   Delivery speed bucket\
-   RFM segmentation\
-   Impact delivery → review

## 🚀 6. Điểm nổi bật (Tính mới)

### ✔ Delivery SLA Simulator

Mô phỏng "Nếu giảm thời gian giao hàng X ngày → review & late rate đổi
thế nào".

### ✔ RFM Customer Segmentation

Phân loại khách hàng: VIP, Loyal, Regular, At-Risk, Lost.

### ✔ Impact Analysis

Phân tích mối liên hệ giữa giao trễ và review score.

## ⚙️ 7. Cách chạy dự án

### 1. Cài đặt thư viện

    pip install -r requirements.txt

### 2. Chạy app

    streamlit run app.py

### 3. Truy cập

    http://localhost:8501

## 📦 8. requirements.txt

    streamlit
    pandas
    numpy
    plotly
    scikit-learn

## 📝 9. Hướng phát triển

-   Thêm machine learning dự đoán late delivery\
-   Anomaly detection logistics\
-   Dự báo doanh thu\
-   Giao diện custom theme
