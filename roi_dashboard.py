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
    
    # Filter by Campaign if available
    if 'Campaign' in df.columns:
        campaigns = df['Campaign'].unique()
        selected_campaigns = st.sidebar.multiselect("Select Campaign(s)", campaigns, default=campaigns)
        df_filtered = df[df['Campaign'].isin(selected_campaigns)]
    else:
        df_filtered = df

    # Add Date Range Filter
    if 'Date' in df_filtered.columns and not df_filtered.empty:
        min_date = df_filtered['Date'].min().date()
        max_date = df_filtered['Date'].max().date()
        selected_dates = st.sidebar.date_input("Select Date Range", value=[min_date, max_date])
        if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
            df_filtered = df_filtered[(df_filtered['Date'].dt.date >= start_date) & (df_filtered['Date'].dt.date <= end_date)]
        else:
            # If a single date is returned, filter by that date
            df_filtered = df_filtered[df_filtered['Date'].dt.date == selected_dates]

    # Calculate overall ROI and Annualized ROI using the date range
    total_cost = df_filtered['Cost'].sum()
    total_revenue = df_filtered['Revenue'].sum()
    overall_roi = ((total_revenue - total_cost) / total_cost) * 100 if total_cost > 0 else 0

    # Determine the time period in years based on the Date column
    if 'Date' in df_filtered.columns and not df_filtered.empty:
        start_date_file = df_filtered['Date'].min()
        end_date_file = df_filtered['Date'].max()
        period_years = (end_date_file - start_date_file).days / 365.25
    else:
        period_years = 0

    if period_years > 0:
        annualized_roi = ((1 + overall_roi/100) ** (1/period_years) - 1) * 100
    else:
        annualized_roi = 0

    # KPI Metrics
    st.subheader("📈 Summary Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Investment", f"${total_cost:,.2f}")
    col2.metric("Total Revenue", f"${total_revenue:,.2f}")
    col3.metric("Net Profit", f"${(total_revenue - total_cost):,.2f}")
    col4.metric("Basic ROI", f"{overall_roi:.2f}%")
    col5.metric("Annualized ROI", f"{annualized_roi:.2f}%")
    if 'Conversions' in df_filtered.columns:
        col6.metric("Total Conversions", int(df_filtered['Conversions'].sum()))
    
    # Chart: ROI Over Time
    st.subheader("📊 ROI Over Time")
    try:
        roi_over_time = df_filtered.groupby('Date').agg({
            'Cost': 'sum',
            'Revenue': 'sum'
        })
        roi_over_time['ROI (%)'] = ((roi_over_time['Revenue'] - roi_over_time['Cost']) / roi_over_time['Cost']) * 100
        st.line_chart(roi_over_time[['ROI (%)']])
    except Exception as e:
        st.error(f"Error generating ROI Over Time chart: {e}")

    # Chart: Campaign Performance
    if 'Campaign' in df_filtered.columns:
        st.subheader("📈 Campaign Performance")
        performance = df_filtered.groupby('Campaign').agg({
            'Cost': 'sum',
            'Revenue': 'sum'
        })
        performance['ROI (%)'] = ((performance['Revenue'] - performance['Cost']) / performance['Cost']) * 100
        st.bar_chart(performance[['ROI (%)']])
    
    # Detailed Data Table
    st.subheader("🧾 Detailed Data")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("👈 Upload an Excel or CSV file to analyze your campaign data.")
    st.markdown("""
    ### Sample Columns Your File Should Contain:
    - **Date**
    - **Campaign**
    - **Cost**
    - **Revenue**
    - **Conversions**
    
    You can also add extra columns like "Platform" or "Channel" for deeper analysis.
    """)

    st.markdown("---")
    st.subheader("🧮 Manual ROI Calculator")

    # Create a form for manual inputs with manual date selection
    with st.form("manual_roi_form"):
        col1, col2 = st.columns(2)
        with col1:
            manual_cost = st.number_input("Enter Total Investment ($)", min_value=0.0, step=100.0, value=0.0)
            manual_revenue = st.number_input("Enter Total Revenue ($)", min_value=0.0, step=100.0, value=0.0)
        with col2:
            date_range_manual = st.date_input("Select Date Range", value=[datetime.today(), datetime.today()])
        submitted = st.form_submit_button("Calculate ROI")

    if submitted:
        if manual_cost > 0:
            basic_roi_manual = ((manual_revenue - manual_cost) / manual_cost) * 100
            # Calculate time period from manually selected dates
            if isinstance(date_range_manual, (tuple, list)) and len(date_range_manual) == 2:
                start_date_manual, end_date_manual = date_range_manual
                period_years_manual = (end_date_manual - start_date_manual).days / 365.25
            else:
                period_years_manual = 0

            if period_years_manual > 0:
                annualized_roi_manual = ((1 + basic_roi_manual/100) ** (1/period_years_manual) - 1) * 100
            else:
                annualized_roi_manual = 0
            st.success(f"✅ Basic ROI: **{basic_roi_manual:.2f}%**")
            st.success(f"✅ Annualized ROI: **{annualized_roi_manual:.2f}%**")
        else:
            st.warning("Investment must be greater than zero to calculate ROI.")

    st.markdown("---")
    st.markdown("### Quick Calculation Formula")
    st.markdown("**ROI (%) = ((Total Revenue - Total Investment) / Total Investment) × 100**")
