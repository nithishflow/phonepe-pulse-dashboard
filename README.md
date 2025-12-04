# 📊 PhonePe Pulse — Data Visualization Dashboard

An interactive Streamlit dashboard for analyzing PhonePe Pulse transaction data stored in SQL Server. This project provides actionable insights into digital payments across Indian states, districts, years, quarters, and transaction categories.

---

## 📁 Table of Contents
- Introduction  
- Features  
- Technologies Used  
- Installation & Setup  
- Usage  
- SQL Data Tables  
- Project Structure  
- Queries  
- Contributing  
- License  
- Contact  

---

## 📌 Introduction
This project reads PhonePe Pulse transactional data from Microsoft SQL Server, performs aggregation using pandas, and visualizes the results using Plotly and Streamlit.  
It includes multiple pages with business perspectives — growth, users, transaction dynamics, insurance penetration, market expansion, and mapping insights using an India GeoJSON file.

---

## 🚀 Features
✔️ Live India state choropleth map (2D interactive)  
✔️ Multi-page dashboard with sidebar navigation  
✔️ Real SQL data connection using `pyodbc` + SQLAlchemy  
✔️ Filters — Year and State  
✔️ KPIs including total value, transaction volume & average ticket size  
✔️ Top 5 queries for each business scenario  
✔️ Bar charts, pie charts, line charts, scatter plots  
✔️ Local GeoJSON file — no API required  
✔️ Designed for PhonePe data analytics projects  

---

## 🛠 Technologies Used
- Python 3  
- Streamlit  
- Pandas  
- Plotly  
- SQLAlchemy  
- pyodbc  
- SQL Server  
- GeoJSON  

---

## 🧩 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/nithishflow/phonepe-pulse-dashboard.git
cd phonepe-pulse-dashboard

2️⃣ Install Required Dependencies

