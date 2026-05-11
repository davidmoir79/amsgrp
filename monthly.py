import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="AFRIMAT GROUP OIL SAMPLE DASHBOARD", layout="wide")

REQUIRED_COLS = [
    "customer",
    "sampno",
    "sampledate",
    "registerdate",
    "site",
    "machine",
    "component",
    "machread",
    "status",
]

def load_data(file_obj):
    df = pd.read_csv(file_obj, sep=";")
    df.columns = df.columns.astype(str).str.strip().str.lower()

    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
        st.write("Found columns:", list(df.columns))
        st.stop()

    df["sampledate"] = pd.to_datetime(df["sampledate"], errors="coerce")
    df["registerdate"] = pd.to_datetime(df["registerdate"], errors="coerce")
    df["status"] = pd.to_numeric(df["status"], errors="coerce").fillna(0).astype(int)
    df["month"] = df["sampledate"].dt.to_period("M").dt.to_timestamp()
    df = df.dropna(subset=["sampledate"])
    return df

st.title("AFRIMAT GROUP OIL SAMPLE DASHBOARD")

uploaded_file = st.sidebar.file_uploader("Upload data_ams.csv", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    local_file = Path(__file__).parent / "data_ams.csv"
    if local_file.exists():
        df = load_data(local_file)
    else:
        st.error("Please upload data_ams.csv or add it to the app folder.")
        st.stop()

if df.empty:
    st.warning("No data found in the CSV.")
    st.stop()

today = pd.Timestamp.today().normalize()
this_month = today.to_period("M").to_timestamp()
last_complete_month = (this_month - pd.DateOffset(months=1)).to_period("M").to_timestamp()

report_month = last_complete_month
prev_month = (report_month - pd.DateOffset(months=1)).to_period("M").to_timestamp()

current_month_df = df[df["month"] == report_month].copy()
last_month_df = df[df["month"] == prev_month].copy()

current_total = len(current_month_df)
last_total = len(last_month_df)

st.subheader("Monthly totals")
c1, c2 = st.columns(2)
c1.metric("Total Samples for Current Month", current_total)
c2.metric("Total Samples for Last Month", last_total)

last_24_months = pd.date_range(end=report_month, periods=24, freq="MS")
all_24 = df[df["month"].isin(last_24_months)].copy()

st.subheader("All samples for last 24 months")
all_monthly = (
    all_24.groupby("month")
    .size()
    .reset_index(name="samples")
    .sort_values("month")
)

fig_all = px.line(
    all_monthly,
    x="month",
    y="samples",
    markers=True,
    title="All samples - last 24 months",
)
fig_all.update_layout(xaxis_title="Month", yaxis_title="Samples")
st.plotly_chart(fig_all, use_container_width=True)

st.subheader(f"Last month samples by customer: {report_month.strftime('%B %Y')}")
last_month_counts = (
    current_month_df.groupby("customer")
    .size()
    .reset_index(name="samples")
    .sort_values("samples", ascending=False)
)

fig_last_month = px.bar(
    last_month_counts,
    x="customer",
    y="samples",
    title="Last month samples for all customers",
)
fig_last_month.update_layout(xaxis_title="Customer", yaxis_title="Samples")
st.plotly_chart(fig_last_month, use_container_width=True)

st.subheader("Last month data per customer")
customer_list = sorted(current_month_df["customer"].dropna().astype(str).unique())

for customer in customer_list:
    cust_last = current_month_df[current_month_df["customer"].astype(str) == customer].copy()
    cust_last = cust_last.sort_values("sampledate")

    cust_24 = all_24[all_24["customer"].astype(str) == customer].copy()
    cust_24 = cust_24.sort_values("sampledate")

    cust_monthly_24 = (
        cust_24.groupby("month")
        .size()
        .reset_index(name="samples")
        .sort_values("month")
    )

    status_current = cust_last.groupby("status").size().reset_index(name="count")
    status_24 = cust_24.groupby("status").size().reset_index(name="count")

    with st.expander(customer, expanded=False):
        st.markdown(f"### {customer}")

        c1, c2 = st.columns([2, 1])

        with c1:
            fig_line = px.line(
                cust_monthly_24,
                x="month",
                y="samples",
                markers=True,
                title=f"{customer} - samples per month for last 24 months",
            )
            fig_line.update_layout(xaxis_title="Month", yaxis_title="Samples")
            st.plotly_chart(fig_line, use_container_width=True)

        with c2:
            fig_current_status = px.pie(
                status_current,
                names="status",
                values="count",
                title=f"{customer} - status current month",
            )
            st.plotly_chart(fig_current_status, use_container_width=True)

        c3, c4 = st.columns([2, 1])

        with c3:
            st.dataframe(
                cust_last[
                    [
                        "customer",
                        "sampno",
                        "sampledate",
                        "registerdate",
                        "site",
                        "machine",
                        "component",
                        "machread",
                        "status",
                    ]
                ],
                hide_index=True,
                use_container_width=True,
            )

        with c4:
            fig_24_status = px.pie(
                status_24,
                names="status",
                values="count",
                title=f"{customer} - status last 24 months",
            )
            st.plotly_chart(fig_24_status, use_container_width=True)

st.subheader("Sample per month for last 24 months per customer")
customer_choice = st.selectbox(
    "Select customer",
    sorted(df["customer"].dropna().astype(str).unique())
)

customer_history = df[df["customer"].astype(str) == customer_choice].copy()
customer_history = customer_history.sort_values("sampledate")
customer_24 = customer_history[customer_history["month"].isin(last_24_months)].copy()

customer_24_monthly = (
    customer_24.groupby("month")
    .size()
    .reset_index(name="samples")
    .sort_values("month")
)

fig_24 = px.bar(
    customer_24_monthly,
    x="month",
    y="samples",
    title=f"{customer_choice} - samples per month (last 24 months)",
)
fig_24.update_layout(xaxis_title="Month", yaxis_title="Samples")
st.plotly_chart(fig_24, use_container_width=True)
