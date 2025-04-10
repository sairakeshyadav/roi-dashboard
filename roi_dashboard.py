import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

    # KPI Metrics
    st.subheader("📈 Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Investment", f"${df_filtered['Cost'].sum():,.2f}")
    col2.metric("Total Revenue", f"${df_filtered['Revenue'].sum():,.2f}")
    col3.metric("Net Profit", f"${df_filtered['Profit'].sum():,.2f}")
    col4.metric("Average ROI", f"{df_filtered['ROI (%)'].mean():.2f}%")
    if 'Conversions' in df_filtered.columns:
        col5.metric("Total Conversions", int(df_filtered['Conversions'].sum()))
    
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

    # Create a form for manual inputs
    with st.form("manual_roi_form"):
        col1, col2 = st.columns(2)
        with col1:
            manual_cost = st.number_input("Enter Total Investment ($)", min_value=0.0, step=100.0, value=0.0)
        with col2:
            manual_revenue = st.number_input("Enter Total Revenue ($)", min_value=0.0, step=100.0, value=0.0)
        submitted = st.form_submit_button("Calculate ROI")

    if submitted:
        if manual_cost > 0:
            roi_manual = ((manual_revenue - manual_cost) / manual_cost) * 100
            st.success(f"✅ Your ROI is **{roi_manual:.2f}%**")
        else:
            st.warning("Investment must be greater than zero to calculate ROI.")

    st.markdown("---")
    st.markdown("### Quick Calculation Formula")
    st.markdown("**ROI (%) = ((Total Revenue - Total Investment) / Total Investment) × 100**")
