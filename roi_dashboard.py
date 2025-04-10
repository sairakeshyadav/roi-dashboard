import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Set up the page configuration
st.set_page_config(page_title="Advanced ROI Dashboard", layout="wide")

# Main Title
st.title("📊 Advanced ROI Dashboard")

# Sidebar - File Upload Section
st.sidebar.header("Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Load the file based on extension
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    st.subheader("📋 Raw Data Preview")
    st.dataframe(df.head(), use_container_width=True)

    # Data Preprocessing
    try:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Profit'] = df['Revenue'] - df['Cost']
        df['ROI (%)'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
        df['Cost/Conversion'] = df['Cost'] / df['Conversions']
        df['Revenue/Conversion'] = df['Revenue'] / df['Conversions']
    except Exception as e:
        st.error(f"Error in processing data: {e}")
        st.stop()

    # Sidebar Filter Section
    st.sidebar.subheader("Filters")
    if 'Campaign' in df.columns:
        campaigns = df['Campaign'].unique()
        selected_campaigns = st.sidebar.multiselect("Select Campaign(s)", campaigns, default=campaigns)
        df_filtered = df[df['Campaign'].isin(selected_campaigns)]
    else:
        df_filtered = df

    # Calculate overall ROI and Annualized ROI using the date range
    total_cost = df_filtered['Cost'].sum()
    total_revenue = df_filtered['Revenue'].sum()
    overall_roi = ((total_revenue - total_cost) / total_cost) * 100 if total_cost > 0 else 0

    # Determine the time period in years based on the Date column
    if 'Date' in df_filtered.columns and not df_filtered.empty:
        start_date = df_filtered['Date'].min()
        end_date = df_filtered['Date'].max()
        period_years = (end_date - start_date).days / 365.25
    else:
        period_years = 0

    if period_years > 0:
        annualized_roi = ((1 + overall_roi/100) ** (1/period_years) - 1) * 100
    else:
        annualized_roi = 0

    # KPI Metrics
    st.subheader("📈 Summary Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Investment",
