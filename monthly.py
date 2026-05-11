import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="AMS Samples Dashboard", layout="wide")

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

st.title("AMS Samples Dashboard")

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

customers = sorted(df["customer"].dropna().astype(str).unique())

st.subheader("Customer selector")
selected_customer = st.selectbox("Select customer", customers)

customer_df = df[df["customer"].astype(str) == selected_customer].copy()
customer_df = customer_df.sort_values("sampledate")

if customer_df.empty:
    st.warning("No records found for the selected customer.")
    st.stop()

max_month = customer_df["month"].max()
months_24 = pd.date_range(end=max_month, periods=24, freq="MS")

monthly_customer = (
    customer_df[customer_df["month"].isin(months_24)]
    .groupby("month")
    .size()
    .reset_index(name="samples")
    .sort_values("month")
)

latest_2 = monthly_customer.sort_values("month", ascending=False).head(2).copy()
latest_2["month_label"] = latest_2["month"].dt.strftime("%b %Y")
latest_2 = latest_2[["month_label", "samples"]]

st.subheader(f"Latest months for {selected_customer}")
c1, c2 = st.columns([2, 1])

with c1:
    fig_month = px.line(
        monthly_customer,
        x="month",
        y="samples",
        markers=True,
        title=f"Monthly samples for {selected_customer} - last 24 months",
    )
    fig_month.update_layout(xaxis_title="Sample month", yaxis_title="Samples")
    st.plotly_chart(fig_month, use_container_width=True)

with c2:
    st.dataframe(latest_2, hide_index=True, use_container_width=True)

st.subheader(f"Samples by month for {selected_customer}")
st.dataframe(monthly_customer.sort_values("month", ascending=False), hide_index=True, use_container_width=True)

st.subheader(f"Sample records for {selected_customer}")
table_cols = [
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
st.dataframe(
    customer_df[table_cols],
    hide_index=True,
    use_container_width=True,
)

st.subheader(f"Status for {selected_customer}")
status_customer = (
    customer_df.groupby("status")
    .size()
    .reset_index(name="count")
    .sort_values("status")
)

fig_status_customer = px.pie(
    status_customer,
    names="status",
    values="count",
    title=f"Status for {selected_customer}",
)
st.plotly_chart(fig_status_customer, use_container_width=True)

st.subheader("All customers overview")
overview = (
    df.groupby("customer")
    .size()
    .reset_index(name="samples")
    .sort_values("samples", ascending=False)
)

fig_overview = px.bar(
    overview,
    x="customer",
    y="samples",
    title="Samples per customer",
)
fig_overview.update_layout(xaxis_title="Customer", yaxis_title="Samples")
st.plotly_chart(fig_overview, use_container_width=True)

st.subheader("Customer status summary")
status_all_customers = (
    df.groupby(["customer", "status"])
    .size()
    .reset_index(name="count")
    .sort_values(["customer", "status"])
)
st.dataframe(status_all_customers, hide_index=True, use_container_width=True)
