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

def clean_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
    )
    return df

def load_data(file_obj):
    df = pd.read_csv(file_obj)
    df = clean_columns(df)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        st.error(f"Missing columns in CSV: {missing}")
        st.write("Found columns:", list(df.columns))
        st.stop()

    for c in ["sampledate", "registerdate"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    df["status"] = pd.to_numeric(df["status"], errors="coerce").fillna(0).astype(int)
    df["month"] = df["sampledate"].dt.to_period("M").dt.to_timestamp()
    return df

st.title("AMS Samples Dashboard")

uploaded_file = st.sidebar.file_uploader("Upload data_ams.csv", type=["csv"])
df = None

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
months_24 = pd.date_range(end=max_month, periods=24, freq="MS")

monthly_all = (
    df[df["month"].isin(months_24)]
    .groupby("month")
    .size()
    .reset_index(name="samples")
)

latest_2 = monthly_all.sort_values("month", ascending=False).head(2).copy()
latest_2["month_label"] = latest_2["month"].dt.strftime("%b %Y")
latest_2 = latest_2[["month_label", "samples"]]

st.subheader("Latest months")
c1, c2 = st.columns([2, 1])

with c1:
    fig_month = px.line(
        monthly_all,
        x="month",
        y="samples",
        markers=True,
        title="Monthly samples for all sites - last 24 months",
    )
    fig_month.update_layout(xaxis_title="Month", yaxis_title="Samples")
    st.plotly_chart(fig_month, use_container_width=True)

with c2:
    st.dataframe(latest_2, hide_index=True, use_container_width=True)

st.subheader("Samples per site")
site_counts = (
    df.groupby("site")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="samples")
)

fig_site = px.bar(site_counts, x="site", y="samples", title="Number of samples per site")
fig_site.update_layout(xaxis_title="Site", yaxis_title="Samples")
st.plotly_chart(fig_site, use_container_width=True)

st.subheader("Last month table")
last_month_df = df[df["month"] == max_month].copy()

table_cols = [
    "customer",
    "sampno",
    
