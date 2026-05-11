import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Samples Dashboard", layout="wide")

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    for c in ["sampledate", "registerdate"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df["status"] = pd.to_numeric(df["status"], errors="coerce").fillna(0).astype(int)
    df["month"] = df["sampledate"].dt.to_period("M").dt.to_timestamp()
    return df

st.title("Monthly Samples Dashboard")

path = st.sidebar.text_input("CSV path", "data.csv")
df = load_data(path)

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

monthly_last2 = monthly_all.sort_values("month", ascending=False).head(2).copy()
monthly_last2["month_label"] = monthly_last2["month"].dt.strftime("%b %Y")
monthly_last2 = monthly_last2[["month_label", "samples"]]

c1, c2 = st.columns([2, 1])

with c1:
    fig = px.line(
        monthly_all,
        x="month",
        y="samples",
        markers=True,
        title="Monthly samples - last 24 months",
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Samples")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Current and previous month")
    st.dataframe(monthly_last2, hide_index=True, use_container_width=True)

site_counts = (
    df.groupby("site")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="samples")
)

site_fig = px.bar(site_counts, x="site", y="samples", title="Samples by site")
site_fig.update_layout(xaxis_title="Site", yaxis_title="Samples")
st.plotly_chart(site_fig, use_container_width=True)

st.subheader("Last month sample table")
last_month_df = df[df["month"] == max_month].copy()
st.dataframe(
    last_month_df[
        ["customer", "sampno", "sampledate", "registerdate", "site", "machine", "component", "machread", "status"]
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader("All sites status")
status_all = df.groupby("status").size().reset_index(name="count")
fig_status_all = px.pie(status_all, names="status", values="count", title="Status - all sites")
st.plotly_chart(fig_status_all, use_container_width=True)

st.subheader("Status per site")
selected_site = st.selectbox("Select site", sorted(df["site"].dropna().unique()))
site_status = (
    df[df["site"] == selected_site]
    .groupby("status")
    .size()
    .reset_index(name="count")
)
fig_status_site = px.pie(site_status, names="status", values="count", title=f"Status - {selected_site}")
st.plotly_chart(fig_status_site, use_container_width=True)
