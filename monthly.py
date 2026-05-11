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

max_month = df["month"].max()
prev_month = (max_month - pd.DateOffset(months=1)).to_period("M").to_timestamp()

last_month_df = df[df["month"] == max_month].copy()
last_month_df = last_month_df.sort_values("sampledate")

customer_counts = (
    last_month_df.groupby("customer")
    .size()
    .reset_index(name="samples")
    .sort_values("samples", ascending=False)
)

st.subheader(f"Last month samples by customer: {max_month.strftime('%B %Y')}")
fig_last_month = px.bar(
    customer_counts,
    x="customer",
    y="samples",
    title="Last month samples for all customers",
)
fig_last_month.update_layout(xaxis_title="Customer", yaxis_title="Samples")
st.plotly_chart(fig_last_month, use_container_width=True)

c1, c2 = st.columns(2)

with c1:
    st.subheader(f"Current month: {max_month.strftime('%B %Y')}")
    st.dataframe(
        last_month_df[
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

with c2:
    prev_month_df = df[df["month"] == prev_month].copy().sort_values("sampledate")
    st.subheader(f"Previous month: {prev_month.strftime('%B %Y')}")
    st.dataframe(
        prev_month_df[
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

st.subheader("Status by customer for last month")
customer_list = sorted(last_month_df["customer"].dropna().astype(str).unique())

for customer in customer_list:
    cust_df = last_month_df[last_month_df["customer"].astype(str) == customer].copy()
    if cust_df.empty:
        continue

    st.markdown(f"### {customer}")

    c1, c2 = st.columns([2, 1])

    with c1:
        fig_cust = px.line(
            cust_df.sort_values("sampledate"),
            x="sampledate",
            y="machread",
            markers=True,
            title=f"{customer} - sampledate trend",
        )
        fig_cust.update_layout(xaxis_title="Sample date", yaxis_title="Mach read")
        st.plotly_chart(fig_cust, use_container_width=True)

    with c2:
        status_counts = cust_df.groupby("status").size().reset_index(name="count")
        fig_pie = px.pie(
            status_counts,
            names="status",
            values="count",
            title=f"{customer} - status",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.dataframe(
        cust_df[
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
