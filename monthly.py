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
    df.columns = df.columns.astype(str).str.strip().str.lower()
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
        
