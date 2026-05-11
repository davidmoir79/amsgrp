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
    
