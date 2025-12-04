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
---

** 2️⃣ Install Required Dependencies

-pip install streamlit pandas plotly sqlalchemy pyodbc

3️⃣ Configure SQL Server Connection
odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=VASI\\SQLEXPRESS;"
    "DATABASE=phonepe;"
    "Trusted_Connection=yes;"
 )

4️⃣ Add Local GeoJSON File

Place india_states.geojson in the same directory as phonepe.py.

5️⃣Run App
streamlit run phonepe.py


Open in browser:
👉 http://localhost:8501

🗂 SQL Data Tables Used
| Table Name | Description                                |
| ---------- | ------------------------------------------ |
| Agg_trans  | Aggregated transaction amounts and counts  |
| Agg_user   | Aggregated user statistics                 |
| Agg_insu   | Aggregated insurance transactions          |
| top_tran   | Top district-level transactions            |
| top_user   | Top user-based metrics                     |
| top_insu   | Top insurance metrics                      |
| map_user   | Registered users and app opens by district |
| map_tran   | Transaction amounts by district            |
| map_insu   | Insurance mapping metrics                  |

🧱 Project Structure

📂 phonepe-dashboard/
│
├── phonepe.py                       # Main Streamlit application
├── Data_Extraction_and_Transformation.ipynb   # Jupyter notebook for ETL
├── india_states.geojson             # India states shape file for map
├── README.md                        # Project documentation
└── requirements.txt                 # Python dependencies

📊 Sample SQL Queries
SELECT TOP 5 * FROM Agg_trans;
SELECT TOP 5 * FROM map_user;
SELECT TOP 5 * FROM map_tran;
SELECT TOP 5 * FROM top_tran;
SELECT TOP 5 * FROM Agg_insu;

🙌 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
git checkout -b feature/AmazingFeature
3. Commit your changes
git commit -m "Add some AmazingFeature"
4. Push to the branch
git push origin feature/AmazingFeature
5. Open a Pull Request

📜 License

This project is open-source and available under the MIT License.

📬 Contact

Author: Nithish Kumar
📧 Email: (vasifootball007@gmail.com)

🔗 GitHub: 

