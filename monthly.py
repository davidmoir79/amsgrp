import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from pathlib import Path

pio.templates.default = "plotly"

st.set_page_config(page_title="AFRIMAT GROUP OIL SAMPLE DASHBOARD", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #d9e2ec;
        padding: 1rem 1rem 0.8rem 1rem;
        border-radius: 12px;
    }
    h1, h2, h3 {color: #3b3b3b;}
    </style>
    """,
    unsafe_allow_html=True,
)

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

GREY = "#7f7f7f"
DARK_RED = "#7a0019"
LIGHT_GREY = "#d9d9d9"

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

uploaded_file = st.sidebar.file_uploader(
    "Upload data_ams.csv",
    type=["csv"],
    label_visibility="collapsed",
    key="upload_csv",
)

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
report_month = (this_month - pd.DateOffset(months=1)).to_period("M").to_timestamp()
prev_month = (report_month - pd.DateOffset(months=1)).to_period("M").to_timestamp()

last_24_months = pd.date_range(end=report_month, periods=24, freq="MS")
last_12_months = pd.date_range(end=report_month, periods=12, freq="MS")

current_month_df = df[df["month"] == report_month].copy()
prev_month_df = df[df["month"] == prev_month].copy()
active_customers_df = df[df["month"].isin(last_12_months)].copy()

current_total = len(current_month_df)
last_total = len(prev_month_df)
active_customers = sorted(active_customers_df["customer"].dropna().astype(str).unique())

diesel_current = current_month_df[
    current_month_df["machine"].astype(str).str.contains("diesel", case=False, na=False)
    | current_month_df["component"].astype(str).str.contains("diesel", case=False, na=False)
]
diesel_count = len(diesel_current)

st.subheader("Monthly overview")
m1, m2, m3 = st.columns(3)
m1.metric(f"Current Month ({report_month.strftime('%B %Y')})", current_total)
m2.metric(f"Last Month ({prev_month.strftime('%B %Y')})", last_total)
m3.metric(f"Diesel samples ({report_month.strftime('%B %Y')})", diesel_count)

st.subheader("All samples for last 24 months")
all_24 = df[df["month"].isin(last_24_months)].copy()
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
    text="samples",
    title="All samples - last 24 months",
    color_discrete_sequence=[DARK_RED],
)
fig_all.update_traces(textposition="top center")
fig_all.update_layout(
    xaxis_title="Month",
    yaxis_title="Samples",
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font_color="#3b3b3b",
)
st.plotly_chart(fig_all, use_container_width=True, key="all_24_line")

st.subheader(f"Current month samples by customer: {report_month.strftime('%B %Y')}")
current_counts = (
    current_month_df.groupby("customer")
    .size()
    .reset_index(name="samples")
    .sort_values("samples", ascending=False)
)

fig_current = px.bar(
    current_counts,
    x="customer",
    y="samples",
    text="samples",
    title=f"Current month samples for all customers ({report_month.strftime('%B %Y')})",
    color_discrete_sequence=[DARK_RED],
)
fig_current.update_traces(texttemplate="%{text}", textposition="outside")
fig_current.update_layout(
    xaxis_title="Customer",
    yaxis_title="Samples",
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font_color="#3b3b3b",
)
st.plotly_chart(fig_current, use_container_width=True, key="current_customer_bar")

st.subheader("Customers active in the last 12 months")
for idx, customer in enumerate(active_customers):
    cust_current = current_month_df[current_month_df["customer"].astype(str) == customer].copy()
    cust_current = cust_current.sort_values("sampledate")

    cust_24 = all_24[all_24["customer"].astype(str) == customer].copy()
    cust_24 = cust_24.sort_values("sampledate")

    if cust_24.empty and cust_current.empty:
        continue

    cust_monthly_24 = (
        cust_24.groupby("month")
        .size()
        .reset_index(name="samples")
        .sort_values("month")
    )

    status_current = cust_current.groupby("status").size().reset_index(name="count")
    status_24 = cust_24.groupby("status").size().reset_index(name="count")

    with st.expander(f"{customer}  |  Current month samples: {len(cust_current)}", expanded=False):
        st.caption(f"Current month ({report_month.strftime('%B %Y')}): {len(cust_current)} sample(s)")

        c1, c2 = st.columns([2, 1])

        with c1:
            fig_line = px.line(
                cust_monthly_24,
                x="month",
                y="samples",
                markers=True,
                text="samples",
                title=f"{customer} - samples per month (last 24 months)",
                color_discrete_sequence=[DARK_RED],
            )
            fig_line.update_traces(textposition="top center")
            fig_line.update_layout(
                xaxis_title="Month",
                yaxis_title="Samples",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font_color="#3b3b3b",
            )
            st.plotly_chart(fig_line, use_container_width=True, key=f"cust_line_{idx}")

        with c2:
            fig_current_status = px.pie(
                status_current,
                names="status",
                values="count",
                title=f"{customer} - status current month",
                color_discrete_sequence=[DARK_RED, GREY, LIGHT_GREY, "#b22222", "#8b8b8b"],
            )
            fig_current_status.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font_color="#3b3b3b",
            )
            st.plotly_chart(fig_current_status, use_container_width=True, key=f"cust_status_current_{idx}")

        c3, c4 = st.columns([2, 1])

        with c3:
            st.dataframe(
                cust_current[
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
                color_discrete_sequence=[DARK_RED, GREY, LIGHT_GREY, "#b22222", "#8b8b8b"],
            )
            fig_24_status.update_layout(
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font_color="#3b3b3b",
            )
            st.plotly_chart(fig_24_status, use_container_width=True, key=f"cust_status_24_{idx}")

st.subheader("Customer month selector")
customer_choice = st.selectbox("Select customer", active_customers, key="customer_choice")

customer_history = df[df["customer"].astype(str) == customer_choice].copy()
customer_history = customer_history.sort_values("sampledate")
customer_24 = customer_history[customer_history["month"].isin(last_24_months)].copy()

customer_24_monthly = (
    customer_24.groupby("month")
    .size()
    .reset_index(name="samples")
    .sort_values("month")
)

fig_24 = px.line(
    customer_24_monthly,
    x="month",
    y="samples",
    markers=True,
    text="samples",
    title=f"{customer_choice} - samples per month (last 24 months)",
    color_discrete_sequence=[DARK_RED],
)
fig_24.update_traces(textposition="top center")
fig_24.update_layout(
    xaxis_title="Month",
    yaxis_title="Samples",
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font_color="#3b3b3b",
)
st.plotly_chart(fig_24, use_container_width=True, key="customer_month_line")

st.subheader("Diesel samples and high status records")

diesel_all = df[
    df["machine"].astype(str).str.contains("diesel", case=False, na=False)
    | df["component"].astype(str).str.contains("diesel", case=False, na=False)
].copy()

diesel_current_month = diesel_all[diesel_all["month"] == report_month].copy()

d1, d2 = st.columns(2)
d1.metric(f"Diesel samples for current month ({report_month.strftime('%B %Y')})", len(diesel_current_month))
d2.metric("Diesel samples with status 2 or above", len(diesel_current_month[diesel_current_month["status"] >= 2]))

st.markdown("### Diesel samples for current month")
if diesel_current_month.empty:
    st.info("No diesel samples found for the current month.")
else:
    diesel_show = diesel_current_month[
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
    ].copy()

    def highlight_status(row):
        if row["status"] >= 2:
            return ["background-color: #ffd6d6"] * len(row)
        return [""] * len(row)

    st.dataframe(
        diesel_show.style.apply(highlight_status, axis=1),
        use_container_width=True,
        hide_index=True,
    )
