"""Credit Risk Analysis dashboard – Streamlit + PostgreSQL/MySQL.
Run:  streamlit run app.py
DB:   set DB_URL env var, e.g. postgresql+psycopg2://postgres:password@localhost:5432/credit_risk_db
"""
import os, re
import pandas as pd, plotly.express as px, streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Credit Risk Analysis", page_icon="💳", layout="wide")
DB_URL = os.getenv("DB_URL", "postgresql+psycopg2://postgres:password@localhost:5432/credit_risk_db")

@st.cache_resource
def engine(url): return create_engine(url)

@st.cache_data(ttl=600, show_spinner="Running SQL…")
def run(sql, params=None, url=DB_URL):
    with engine(url).connect() as c:
        return pd.read_sql(text(sql), c, params=params or {})

try:
    run("SELECT 1")
except Exception as e:
    st.error(f"Cannot connect to the database. Check DB_URL / MySQL server.\n\n{e}"); st.stop()

# ---------- sidebar filters (built from SQL) ----------
st.sidebar.header("Filters")
def opts(col): return run(f"SELECT DISTINCT {col} AS v FROM loan_data ORDER BY 1")["v"].dropna().tolist()
contract = st.sidebar.multiselect("Contract type", opts("NAME_CONTRACT_TYPE"))
client = st.sidebar.multiselect("Client type", opts("NAME_CLIENT_TYPE"))
band = st.sidebar.multiselect("Credit band", opts("CREDIT_BAND"))
portfolio = st.sidebar.multiselect("Portfolio", opts("NAME_PORTFOLIO"))
bucket = st.sidebar.multiselect("Decision recency", opts("DECISION_YEAR_BUCKET"))

where, params = [], {}
for col, vals in [("NAME_CONTRACT_TYPE", contract), ("NAME_CLIENT_TYPE", client), ("CREDIT_BAND", band),
                  ("NAME_PORTFOLIO", portfolio), ("DECISION_YEAR_BUCKET", bucket)]:
    if vals:
        keys = [f"{col}_{i}" for i in range(len(vals))]
        where.append(f"{col} IN ({', '.join(':' + k for k in keys)})"); params.update(dict(zip(keys, vals)))
W = "WHERE " + " AND ".join(where) if where else ""

st.title("💳 Credit Risk & Loan Repayment Behaviour")
st.caption("Refusal rate is used as the risk indicator (the dataset has no default flag).")
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "⚠️ Risk Segments", "💰 Financials", "🧾 SQL Queries"])

# ---------- Overview ----------
with tab1:
    k = run(f"""SELECT COUNT(*) apps, COUNT(DISTINCT SK_ID_CURR) customers, SUM(AMT_CREDIT) credit,
                AVG(AMT_APPLICATION) avg_app, 100*AVG(IS_APPROVED) appr, 100*AVG(IS_REFUSED) refu
                FROM loan_data {W}""", params).iloc[0]
    if not k["apps"]: st.warning("No records match the filters."); st.stop()
    c = st.columns(6)
    c[0].metric("Applications", f"{int(k.apps):,}"); c[1].metric("Customers", f"{int(k.customers):,}")
    c[2].metric("Total credit", f"{k.credit/1e9:,.2f} B"); c[3].metric("Avg application", f"{k.avg_app:,.0f}")
    c[4].metric("Approval %", f"{k.appr:.1f}"); c[5].metric("Refusal %", f"{k.refu:.1f}")
    a, b = st.columns(2)
    d = run(f"SELECT NAME_CONTRACT_STATUS status, COUNT(*) n FROM loan_data {W} GROUP BY 1", params)
    a.plotly_chart(px.pie(d, names="status", values="n", hole=.45, title="Application status"), use_container_width=True)
    d = run(f"SELECT NAME_CONTRACT_TYPE t, NAME_CONTRACT_STATUS s, COUNT(*) n FROM loan_data {W} GROUP BY 1,2", params)
    b.plotly_chart(px.bar(d, x="t", y="n", color="s", title="Status by contract type"), use_container_width=True)
    d = run(f"SELECT WEEKDAY_APPR_PROCESS_START d, COUNT(*) n FROM loan_data {W} GROUP BY 1", params)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    st.plotly_chart(px.bar(d, x="d", y="n", title="Applications by weekday", category_orders={"d": days}), use_container_width=True)

# ---------- Risk ----------
with tab2:
    dim = st.selectbox("Segment by", ["NAME_CONTRACT_TYPE", "NAME_CLIENT_TYPE", "CREDIT_BAND", "NAME_PORTFOLIO",
                                      "CHANNEL_TYPE", "NAME_YIELD_GROUP", "DECISION_YEAR_BUCKET", "NAME_SELLER_INDUSTRY"])
    d = run(f"""SELECT {dim} segment, COUNT(*) applications, ROUND(100*AVG(IS_REFUSED),1) refusal_pct,
                ROUND(100*AVG(IS_APPROVED),1) approval_pct FROM loan_data {W}
                GROUP BY {dim} HAVING COUNT(*) >= 30 ORDER BY refusal_pct DESC""", params)
    a, b = st.columns(2)
    a.plotly_chart(px.bar(d, x="segment", y="refusal_pct", color="refusal_pct", color_continuous_scale="Reds",
                          title=f"Refusal % by {dim} (segments ≥30 apps)"), use_container_width=True)
    b.dataframe(d, use_container_width=True, hide_index=True)
    st.subheader("🚩 High-risk segments (refusal ≥ 30 %)")
    st.dataframe(d[d.refusal_pct >= 30], use_container_width=True, hide_index=True)
    r = run(f"""SELECT CODE_REJECT_REASON reason, COUNT(*) n FROM loan_data
                {W + ' AND' if W else 'WHERE'} IS_REFUSED = 1 GROUP BY 1 ORDER BY n DESC""", params)
    st.plotly_chart(px.bar(r, x="reason", y="n", title="Rejection reasons"), use_container_width=True)

# ---------- Financials ----------
with tab3:
    d = run(f"SELECT AMT_CREDIT amt_credit, AMT_APPLICATION amt_application, NAME_CONTRACT_STATUS s FROM loan_data {W} "
            f"{'AND' if W else 'WHERE'} AMT_CREDIT > 0 AND AMT_APPLICATION > 0 LIMIT 5000", params)
    st.plotly_chart(px.scatter(d, x="amt_application", y="amt_credit", color="s", log_x=True, log_y=True, opacity=.5,
                               title="Application vs credit amount (first 5K rows, log scale)"), use_container_width=True)
    a, b = st.columns(2)
    d = run(f"SELECT NAME_SELLER_INDUSTRY i, SUM(AMT_CREDIT) total FROM loan_data {W} GROUP BY 1 ORDER BY total DESC LIMIT 8", params)
    a.plotly_chart(px.bar(d, x="total", y="i", orientation="h", title="Credit by seller industry"), use_container_width=True)
    d = run(f"SELECT NAME_CONTRACT_TYPE t, AVG(AMT_ANNUITY) annuity, AVG(AMT_CREDIT) credit FROM loan_data {W} GROUP BY 1", params)
    b.plotly_chart(px.bar(d.melt("t"), x="t", y="value", color="variable", barmode="group", title="Avg annuity & credit"), use_container_width=True)

# ---------- SQL ----------
with tab4:
    raw = open(os.path.join(os.path.dirname(__file__), "sql", "queries.sql"), encoding="utf-8").read().strip()
    Q = {}
    for blk in re.split(r"\n(?=-- Q\d+ \|)", raw):
        head, *body = blk.splitlines()
        n, cat, title = [x.strip() for x in head[3:].split("|")]
        Q[f"{n} · {cat} · {title}"] = "\n".join(body).strip()
    pick = st.selectbox("Predefined query (20)", list(Q))
    st.code(Q[pick], language="sql")
    if st.button("▶ Execute", type="primary"):
        out = run(Q[pick]); st.success(f"{len(out):,} rows"); st.dataframe(out, use_container_width=True)
        st.download_button("Download CSV", out.to_csv(index=False), "query_result.csv")
