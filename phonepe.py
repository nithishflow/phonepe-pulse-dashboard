import os
import json
import urllib

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

# =========================================
# PAGE CONFIG
# =========================================
st.set_page_config(
    layout="wide",
    page_title="PhonePe Pulse Dashboard",
)

# =========================================
# DB CONNECTION
# =========================================
odbc_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=VASI\SQLEXPRESS;"
    "DATABASE=phonepe;"
    "Trusted_Connection=yes;"
)
params = urllib.parse.quote_plus(odbc_str)
engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={params}",
    fast_executemany=True,
)

# =========================================
# TABLE MAP
# =========================================
TABLES = {
    "agg_trans": "Agg_trans",
    "agg_insu": "Agg_insu",
    "map_user": "map_user",
    "map_tran": "map_tran",
    "top_tran": "top_tran",
}

# =========================================
# LOCAL INDIA GEOJSON
# =========================================
@st.cache_data(ttl=86400)
def load_india_geojson():
    geo_path = os.path.join(os.path.dirname(__file__), "india_states.geojson")
    with open(geo_path, "r", encoding="utf-8") as f:
        return json.load(f)

india_geo = load_india_geojson()

# DB state -> GeoJSON properties.NAME_1
STATE_FIX = {
    "Andaman & Nicobar": "Andaman and Nicobar",
    "Andhra Pradesh": "Andhra Pradesh",
    "Arunachal Pradesh": "Arunachal Pradesh",
    "Assam": "Assam",
    "Bihar": "Bihar",
    "Chandigarh": "Chandigarh",
    "Chhattisgarh": "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi": "NCT of Delhi",
    "Goa": "Goa",
    "Gujarat": "Gujarat",
    "Haryana": "Haryana",
    "Himachal Pradesh": "Himachal Pradesh",
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Jharkhand": "Jharkhand",
    "Karnataka": "Karnataka",
    "Kerala": "Kerala",
    "Ladakh": "Ladakh",
    "Lakshadweep": "Lakshadweep",
    "Madhya Pradesh": "Madhya Pradesh",
    "Maharashtra": "Maharashtra",
    "Manipur": "Manipur",
    "Meghalaya": "Meghalaya",
    "Mizoram": "Mizoram",
    "Nagaland": "Nagaland",
    "Odisha": "Orissa",
    "Puducherry": "Puducherry",
    "Punjab": "Punjab",
    "Rajasthan": "Rajasthan",
    "Sikkim": "Sikkim",
    "Tamil Nadu": "Tamil Nadu",
    "Telangana": "Telangana",
    "Tripura": "Tripura",
    "Uttar Pradesh": "Uttar Pradesh",
    "Uttarakhand": "Uttarakhand",
    "West Bengal": "West Bengal",
}

# =========================================
# HELPERS
# =========================================
@st.cache_data(ttl=300)
def run_sql(sql: str):
    """Run SQL and return (df, error_or_None)."""
    try:
        df = pd.read_sql(text(sql), engine)
        return df, None
    except Exception as e:
        return None, e


def detect_column(df: pd.DataFrame, candidates):
    """Pick first existing column name from candidate list."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


# =========================================
# SIDEBAR
# =========================================
st.sidebar.title("📊 PhonePe Pulse Dashboard")
page = st.sidebar.radio(
    "Select Page",
    [
        "🏠 Home",
        "📈 Transaction Dynamics",
        "👥 User Engagement",
        "🛡 Insurance Analysis",
        "🌍 Market Expansion",
        "🚀 Growth Strategy",
    ],
)

# global filters
years_df, _ = run_sql(f"SELECT DISTINCT [Year] FROM {TABLES['agg_trans']} ORDER BY [Year];")
years = sorted(years_df["Year"].astype(str).tolist()) if years_df is not None else []

states_df, _ = run_sql(f"SELECT DISTINCT [State] FROM {TABLES['agg_trans']} ORDER BY [State];")
states = sorted(states_df["State"].astype(str).tolist()) if states_df is not None else []

selected_year = st.sidebar.selectbox("Year", ["All"] + years)
selected_state = st.sidebar.selectbox("State", ["All"] + states)


def sql_filters():
    conds = []
    if selected_year != "All":
        conds.append(f"[Year] = '{selected_year}'")
    if selected_state != "All":
        conds.append(f"[State] = '{selected_state}'")
    return (" AND " + " AND ".join(conds)) if conds else ""


# =========================================
# 🏠 HOME  (MAP + KPIs)
# =========================================
if page == "🏠 Home":
    st.title("📍 India — State-wise Transaction Amount")

    # ---- KPIs (1 query) ----
    q_kpi = f"""
        SELECT
            SUM(CAST([Transacion_count] AS BIGINT))  AS total_tx,
            SUM(CAST([Transacion_amount] AS BIGINT)) AS total_amt
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()};
    """
    df_kpi, err = run_sql(q_kpi)
    if err or df_kpi is None or df_kpi.empty:
        st.error("Could not load KPI data.")
    else:
        total_tx = int(df_kpi.loc[0, "total_tx"])
        total_amt = int(df_kpi.loc[0, "total_amt"])
        avg_ticket = total_amt // total_tx if total_tx else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Transactions", f"{total_tx:,}")
        c2.metric("Total Value (₹)", f"{total_amt:,}")
        c3.metric("Avg Ticket Size (₹)", f"{avg_ticket:,}")

    st.markdown("---")

    # ---- State-level aggregation for MAP (2nd query) ----
    q_state = f"""
        SELECT [State],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS total_amount,
               SUM(CAST([Transacion_count]  AS BIGINT)) AS total_count
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [State]
        ORDER BY total_amount DESC;
    """
    df_state, err = run_sql(q_state)

    if err or df_state is None or df_state.empty:
        st.error("No transaction data available for map.")
    else:
        df_state["State_geo"] = df_state["State"].map(STATE_FIX)
        df_state["avg_ticket"] = (
            df_state["total_amount"] / df_state["total_count"]
        ).replace([np.inf, -np.inf], 0).fillna(0).round(2)

        unmatched = df_state[df_state["State_geo"].isna()]
        if not unmatched.empty:
            st.warning("Unmatched states")
            st.dataframe(unmatched)

        fig = px.choropleth(
            df_state,
            geojson=india_geo,
            featureidkey="properties.NAME_1",
            locations="State_geo",
            color="total_amount",
            color_continuous_scale="Viridis",
            hover_data=["State", "total_amount", "total_count", "avg_ticket"],
            title="State-wise Transaction Amount (All Years)" if selected_year == "All"
            else f"State-wise Transaction Amount ({selected_year})",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=550)
        st.plotly_chart(fig, use_container_width=True)

# =========================================
# 📈 TRANSACTION DYNAMICS (5 QUERIES)
# =========================================
elif page == "📈 Transaction Dynamics":
    st.title("📈 Transaction Dynamics")

    # 1) Top states by transaction amount
    q1 = f"""
        SELECT [State],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [State]
        ORDER BY amt DESC;
    """
    df1, e1 = run_sql(q1)
    st.subheader("1️⃣ Top States by Transaction Amount")
    if e1 or df1 is None or df1.empty:
        st.warning("No data for top states.")
    else:
        st.plotly_chart(
            px.bar(df1.head(20), x="State", y="amt"),
            use_container_width=True,
        )

    # 2) Quarterly trend (amount)
    q2 = f"""
        SELECT [Year], [Quater],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [Year], [Quater]
        ORDER BY [Year], [Quater];
    """
    df2, e2 = run_sql(q2)
    st.subheader("2️⃣ Quarterly Transaction Amount Trend")
    if e2 or df2 is None or df2.empty:
        st.warning("No quarterly data.")
    else:
        df2["label"] = df2["Year"].astype(str) + "-Q" + df2["Quater"].astype(str)
        st.plotly_chart(
            px.line(df2, x="label", y="amt", markers=True),
            use_container_width=True,
        )

    # 3) Transaction type split (amount)
    q3 = f"""
        SELECT [Transacion_type],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [Transacion_type]
        ORDER BY amt DESC;
    """
    df3, e3 = run_sql(q3)
    st.subheader("3️⃣ Transaction Type Split (by Amount)")
    if e3 or df3 is None or df3.empty:
        st.warning("No type-wise data.")
    else:
        st.plotly_chart(
            px.pie(df3, names="Transacion_type", values="amt", hole=0.35),
            use_container_width=True,
        )

    # 4) State x Type heatmap (count)
    q4 = f"""
        SELECT [State], [Transacion_type],
               SUM(CAST([Transacion_count] AS BIGINT)) AS cnt
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [State], [Transacion_type];
    """
    df4, e4 = run_sql(q4)
    st.subheader("4️⃣ State vs Transaction Type (Heatmap)")
    if e4 or df4 is None or df4.empty:
        st.warning("No data for heatmap.")
    else:
        pivot = df4.pivot(index="State", columns="Transacion_type", values="cnt").fillna(0)
        st.plotly_chart(
            px.imshow(
                pivot,
                labels=dict(x="Type", y="State", color="Txn Count"),
            ),
            use_container_width=True,
        )

    # 5) YoY growth by state (count)
    q5 = f"""
        WITH yearly AS (
            SELECT [State], [Year],
                   SUM(CAST([Transacion_count] AS BIGINT)) AS cnt
            FROM {TABLES['agg_trans']}
            GROUP BY [State], [Year]
        )
        SELECT a.[State], a.[Year],
               a.cnt AS curr_cnt,
               b.cnt AS prev_cnt,
               (a.cnt - ISNULL(b.cnt,0)) AS delta
        FROM yearly a
        LEFT JOIN yearly b
               ON a.[State] = b.[State]
              AND a.[Year]  = b.[Year] + 1
        WHERE 1=1 {"" if selected_state == "All" else f"AND a.State = '{selected_state}'"}
        ORDER BY delta DESC;
    """
    df5, e5 = run_sql(q5)
    st.subheader("5️⃣ Year-on-Year Transaction Growth (Count)")
    if e5 or df5 is None or df5.empty:
        st.warning("No YoY growth data.")
    else:
        st.dataframe(df5.head(50))

# =========================================
# 👥 USER ENGAGEMENT (map_user + map_tran)
# Uses pandas agg to be robust to column typos/variants
# =========================================
elif page == "👥 User Engagement":
    st.title("👥 User Engagement")

    # Load raw map_user (no column names in SQL, to avoid invalid-column errors)
    q_mu = f"SELECT * FROM {TABLES['map_user']} WHERE 1=1 {sql_filters()};"
    mu, e_mu = run_sql(q_mu)

    # Utility: detect correct column names
    state_col = detect_column(mu, ["State", "state"])
    year_col = detect_column(mu, ["Year", "year"])
    district_col = detect_column(mu, ["Districts", "District", "districts"])
    ru_col = detect_column(mu, ["RegisteredUsers", "RegisteredUserst", "registeredusers"])
    opens_col = detect_column(mu, ["AppOpens", "appopens"])

    if e_mu or mu is None or mu.empty or not all([state_col, ru_col, opens_col]):
        st.error(
            "Could not read `map_user` properly. "
            "Check columns State / RegisteredUsers / AppOpens (or RegisteredUserst)."
        )
    else:
        # 1) Registered users by state
        st.subheader("1️⃣ Registered Users by State")
        df1 = (
            mu.groupby(state_col, as_index=False)[ru_col]
            .sum()
            .rename(columns={state_col: "State", ru_col: "users"})
            .sort_values("users", ascending=False)
        )
        st.bar_chart(df1.set_index("State")["users"])

        # 2) App opens by state
        st.subheader("2️⃣ App Opens by State")
        df2 = (
            mu.groupby(state_col, as_index=False)[opens_col]
            .sum()
            .rename(columns={state_col: "State", opens_col: "opens"})
            .sort_values("opens", ascending=False)
        )
        st.bar_chart(df2.set_index("State")["opens"])

        # 3) Opens per registered user
        st.subheader("3️⃣ Opens per Registered User (State)")
        df3 = pd.merge(df1, df2, on="State", how="inner")
        df3["opens_per_user"] = (df3["opens"] / df3["users"]).replace(
            [np.inf, -np.inf], 0
        )
        st.plotly_chart(
            px.bar(df3, x="State", y="opens_per_user"),
            use_container_width=True,
        )

        # 4) Top districts by users
        st.subheader("4️⃣ Top Districts by Registered Users")
        if district_col and district_col in mu.columns:
            df4 = (
                mu.groupby(district_col, as_index=False)[ru_col]
                .sum()
                .rename(columns={district_col: "Districts", ru_col: "users"})
                .sort_values("users", ascending=False)
            )
            st.plotly_chart(
                px.bar(df4.head(25), x="Districts", y="users"),
                use_container_width=True,
            )
        else:
            st.warning("No `Districts` column in map_user, skipping district chart.")

        # 5) Users vs Opens scatter
        st.subheader("5️⃣ Users vs Opens (State Bubble Plot)")
        st.plotly_chart(
            px.scatter(
                df3,
                x="users",
                y="opens",
                size="opens_per_user",
                hover_name="State",
            ),
            use_container_width=True,
        )

# =========================================
# 🛡 INSURANCE ANALYSIS (agg_insu)
# =========================================
elif page == "🛡 Insurance Analysis":
    st.title("🛡 Insurance Analysis")

    # 1) Insurance transactions by state
    st.subheader("1️⃣ Insurance Transaction Count by State")
    q1 = f"""
        SELECT [State],
               SUM(CAST([Transacion_count] AS BIGINT)) AS cnt
        FROM {TABLES['agg_insu']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [State]
        ORDER BY cnt DESC;
    """
    df1, e1 = run_sql(q1)
    if e1 or df1 is None or df1.empty:
        st.warning("No insurance data by state.")
    else:
        st.plotly_chart(
            px.bar(df1.head(25), x="State", y="cnt"),
            use_container_width=True,
        )

    # 2) Insurance amount by state
    st.subheader("2️⃣ Insurance Amount by State")
    q2 = f"""
        SELECT [State],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['agg_insu']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [State]
        ORDER BY amt DESC;
    """
    df2, e2 = run_sql(q2)
    if e2 or df2 is None or df2.empty:
        st.warning("No insurance amount data.")
    else:
        st.plotly_chart(
            px.bar(df2.head(25), x="State", y="amt"),
            use_container_width=True,
        )

    # 3) Yearly insurance trend
    st.subheader("3️⃣ Insurance Amount Trend by Year")
    q3 = f"""
        SELECT [Year],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['agg_insu']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [Year]
        ORDER BY [Year];
    """
    df3, e3 = run_sql(q3)
    if e3 or df3 is None or df3.empty:
        st.warning("No yearly insurance trend.")
    else:
        st.plotly_chart(
            px.line(df3, x="Year", y="amt", markers=True),
            use_container_width=True,
        )

    # 4) Insurance penetration vs all transactions
    st.subheader("4️⃣ Insurance Penetration vs Total Transactions")
    q4 = f"""
        WITH insu AS (
            SELECT [State],
                   SUM(CAST([Transacion_count] AS BIGINT)) AS insu_cnt
            FROM {TABLES['agg_insu']}
            WHERE 1=1 {sql_filters()}
            GROUP BY [State]
        ),
        all_tx AS (
            SELECT [State],
                   SUM(CAST([Transacion_count] AS BIGINT)) AS all_cnt
            FROM {TABLES['agg_trans']}
            WHERE 1=1 {sql_filters()}
            GROUP BY [State]
        )
        SELECT a.[State],
               insu_cnt,
               all_cnt,
               CASE WHEN all_cnt=0 THEN 0
                    ELSE 1.0*insu_cnt/all_cnt
               END AS penetration
        FROM insu a
        JOIN all_tx b
          ON a.[State] = b.[State]
        ORDER BY penetration DESC;
    """
    df4, e4 = run_sql(q4)
    if e4 or df4 is None or df4.empty:
        st.warning("No penetration data.")
    else:
        st.plotly_chart(
            px.bar(df4, x="State", y="penetration"),
            use_container_width=True,
        )

    # 5) Insurance type mix
    st.subheader("5️⃣ Insurance Transaction Type Mix")
    q5 = f"""
        SELECT [Transacion_type],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['agg_insu']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [Transacion_type]
        ORDER BY amt DESC;
    """
    df5, e5 = run_sql(q5)
    if e5 or df5 is None or df5.empty:
        st.warning("No type-wise insurance data.")
    else:
        st.plotly_chart(
            px.pie(df5, names="Transacion_type", values="amt", hole=0.3),
            use_container_width=True,
        )

# =========================================
# 🌍 MARKET EXPANSION (agg_trans + map_tran)
# =========================================
elif page == "🌍 Market Expansion":
    st.title("🌍 Market Expansion Opportunities")

    # 1) Highest value states
    st.subheader("1️⃣ Top States by Transaction Amount")
    q1 = f"""
        SELECT [State],
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [State]
        ORDER BY amt DESC;
    """
    df1, e1 = run_sql(q1)
    if e1 or df1 is None or df1.empty:
        st.warning("No state-level value data.")
    else:
        st.plotly_chart(
            px.bar(df1.head(20), x="State", y="amt"),
            use_container_width=True,
        )

    # 2) Quarter-wise volume trend
    st.subheader("2️⃣ Quarter-wise Transaction Volume")
    q2 = f"""
        SELECT [Year], [Quater],
               SUM(CAST([Transacion_count] AS BIGINT)) AS cnt
        FROM {TABLES['agg_trans']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [Year], [Quater]
        ORDER BY [Year], [Quater];
    """
    df2, e2 = run_sql(q2)
    if e2 or df2 is None or df2.empty:
        st.warning("No quarter-wise volume data.")
    else:
        df2["label"] = df2["Year"].astype(str) + "-Q" + df2["Quater"].astype(str)
        st.plotly_chart(
            px.line(df2, x="label", y="cnt", markers=True),
            use_container_width=True,
        )

    # 3) Top districts by transactions (map_tran)
    st.subheader("3️⃣ Top Districts by Transactions")
    q3 = f"""
        SELECT TOP 30 [Districts],
               SUM(CAST([Transacion_count] AS BIGINT)) AS cnt
        FROM {TABLES['map_tran']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [Districts]
        ORDER BY cnt DESC;
    """
    df3, e3 = run_sql(q3)
    if e3 or df3 is None or df3.empty:
        st.warning("No district-level data from map_tran.")
    else:
        st.plotly_chart(
            px.bar(df3, x="Districts", y="cnt"),
            use_container_width=True,
        )

    # 4) District opportunity map: amount vs count
    st.subheader("4️⃣ District Opportunity: Value vs Volume")
    q4 = f"""
        SELECT [Districts],
               SUM(CAST([Transacion_count] AS BIGINT))  AS cnt,
               SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
        FROM {TABLES['map_tran']}
        WHERE 1=1 {sql_filters()}
        GROUP BY [Districts];
    """
    df4, e4 = run_sql(q4)
    if e4 or df4 is None or df4.empty:
        st.warning("No detailed district metrics.")
    else:
        st.plotly_chart(
            px.scatter(
                df4,
                x="cnt",
                y="amt",
                size="amt",
                hover_name="Districts",
            ),
            use_container_width=True,
        )

    # 5) Top potential states: high growth, medium base
    st.subheader("5️⃣ High-Growth States (YoY Amount)")
    q5 = f"""
        WITH yearly AS (
            SELECT [State], [Year],
                   SUM(CAST([Transacion_amount] AS BIGINT)) AS amt
            FROM {TABLES['agg_trans']}
            GROUP BY [State], [Year]
        )
        SELECT a.[State], a.[Year],
               a.amt AS curr_amt,
               b.amt AS prev_amt,
               (a.amt - ISNULL(b.amt,0)) AS delta
        FROM yearly a
        LEFT JOIN yearly b
               ON a.[State] = b.[State]
              AND a.[Year]  = b.[Year] + 1
        WHERE 1=1 {"" if selected_year == "All" else f"AND a.Year = {selected_year}"}
        ORDER BY delta DESC;
    """
    df5, e5 = run_sql(q5)
    if e5 or df5 is None or df5.empty:
        st.warning("No YoY amount data for expansion.")
    else:
        st.dataframe(df5.head(50))

# =========================================
# 🚀 GROWTH STRATEGY (map_user + map_tran)
# =========================================
elif page == "🚀 Growth Strategy":
    st.title("🚀 Growth Strategy")

    # load map_user & map_tran raw
    q_mu = f"SELECT * FROM {TABLES['map_user']} WHERE 1=1 {sql_filters()};"
    mu, e_mu = run_sql(q_mu)

    q_mt = f"SELECT * FROM {TABLES['map_tran']} WHERE 1=1 {sql_filters()};"
    mt, e_mt = run_sql(q_mt)

    if e_mu or e_mt or mu is None or mt is None or mu.empty or mt.empty:
        st.error("Could not load map_user / map_tran for growth strategy.")
    else:
        # detect columns again
        state_mu = detect_column(mu, ["State"])
        year_mu = detect_column(mu, ["Year"])
        qtr_mu = detect_column(mu, ["Quater"])
        dist_mu = detect_column(mu, ["Districts", "District"])
        ru_col = detect_column(mu, ["RegisteredUsers", "RegisteredUserst"])
        opens_col = detect_column(mu, ["AppOpens"])

        state_mt = detect_column(mt, ["State"])
        year_mt = detect_column(mt, ["Year"])
        qtr_mt = detect_column(mt, ["Quater"])
        dist_mt = detect_column(mt, ["Districts", "District"])
        tx_cnt = detect_column(mt, ["Transacion_count"])
        tx_amt = detect_column(mt, ["Transacion_amount"])

        if not all(
            [
                state_mu,
                year_mu,
                qtr_mu,
                dist_mu,
                ru_col,
                opens_col,
                state_mt,
                year_mt,
                qtr_mt,
                dist_mt,
                tx_cnt,
                tx_amt,
            ]
        ):
            st.error("Missing expected columns in map_user / map_tran.")
        else:
            # join on State + Year + Quater + Districts
            key_cols_mu = [state_mu, year_mu, qtr_mu, dist_mu]
            key_cols_mt = [state_mt, year_mt, qtr_mt, dist_mt]

            merged = pd.merge(
                mu[key_cols_mu + [ru_col, opens_col]],
                mt[key_cols_mt + [tx_cnt, tx_amt]],
                left_on=key_cols_mu,
                right_on=key_cols_mt,
                how="inner",
            )

            merged = merged.rename(
                columns={
                    state_mu: "State",
                    dist_mu: "Districts",
                    ru_col: "users",
                    opens_col: "opens",
                    tx_cnt: "tx_cnt",
                    tx_amt: "tx_amt",
                }
            )

            # 1) Users vs Opens vs Tx (district level scatter)
            st.subheader("1️⃣ Users vs Opens vs Tx (Districts)")
            df1 = (
                merged.groupby("Districts", as_index=False)[["users", "opens", "tx_cnt"]]
                .sum()
                .sort_values("tx_cnt", ascending=False)
            )
            st.plotly_chart(
                px.scatter(
                    df1,
                    x="users",
                    y="opens",
                    size="tx_cnt",
                    hover_name="Districts",
                ),
                use_container_width=True,
            )

            # 2) State-level engagement vs volume
            st.subheader("2️⃣ State-level Users vs Transactions")
            df2 = (
                merged.groupby("State", as_index=False)[["users", "tx_cnt"]]
                .sum()
                .sort_values("tx_cnt", ascending=False)
            )
            st.plotly_chart(
                px.scatter(
                    df2,
                    x="users",
                    y="tx_cnt",
                    hover_name="State",
                    size="tx_cnt",
                ),
                use_container_width=True,
            )

            # 3) Opens per user vs tx per user (state)
            st.subheader("3️⃣ Opens/User vs Tx/User (State)")
            df3 = (
                merged.groupby("State", as_index=False)[["users", "opens", "tx_cnt"]]
                .sum()
            )
            df3["opens_per_user"] = df3["opens"] / df3["users"]
            df3["tx_per_user"] = df3["tx_cnt"] / df3["users"]
            st.plotly_chart(
                px.scatter(
                    df3,
                    x="opens_per_user",
                    y="tx_per_user",
                    hover_name="State",
                    size="users",
                ),
                use_container_width=True,
            )

            # 4) High-potential districts: many users, low opens
            st.subheader("4️⃣ High-Potential Districts (Low Opens/User)")
            df4 = (
                merged.groupby("Districts", as_index=False)[["users", "opens"]]
                .sum()
                .query("users > 0")
            )
            df4["opens_per_user"] = df4["opens"] / df4["users"]
            df4 = df4.sort_values("opens_per_user").head(25)
            st.dataframe(df4)

            # 5) High-value districts: high tx_amt
            st.subheader("5️⃣ High-Value Districts (Tx Amount)")
            df5 = (
                merged.groupby("Districts", as_index=False)[["tx_amt"]]
                .sum()
                .sort_values("tx_amt", ascending=False)
                .head(25)
            )
            st.plotly_chart(
                px.bar(df5, x="Districts", y="tx_amt"),
                use_container_width=True,
            )

# =========================================
# FOOTER
# =========================================
st.sidebar.markdown("---")
st.sidebar.caption("Database: phonepe @ VASI\\SQLEXPRESS  ·  All pages use 5 query blocks.")










