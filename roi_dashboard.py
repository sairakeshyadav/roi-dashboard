import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Advanced ROI Dashboard", layout="wide")

# Title
st.title("📊 ROI Dashboard - Upload & Analyze Your Campaign Data")

st.sidebar.header("Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

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

    # Filters
    st.sidebar.subheader("Filters")
    campaigns = df['Campaign'].unique()
    selected_campaigns = st.sidebar.multiselect("Select Campaign(s)", campaigns, default=campaigns)

    df_filtered = df[df['Campaign'].isin(selected_campaigns)]

    # KPI Metrics
    st.subheader("📈 Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Investment", f"${df_filtered['Cost'].sum():,.2f}")
    col2.metric("Total Revenue", f"${df_filtered['Revenue'].sum():,.2f}")
    col3.metric("Net Profit", f"${df_filtered['Profit'].sum():,.2f}")
    col4.metric("Average ROI", f"{df_filtered['ROI (%)'].mean():.2f}%")
    col5.metric("Total Conversions", int(df_filtered['Conversions'].sum()))

    # Chart Section
    st.subheader("📊 ROI Over Time")
    roi_over_time = df_filtered.groupby('Date').agg({
        'Cost': 'sum',
        'Revenue': 'sum',
        'Conversions': 'sum'
    })
    roi_over_time['ROI (%)'] = ((roi_over_time['Revenue'] - roi_over_time['Cost']) / roi_over_time['Cost']) * 100

    st.line_chart(roi_over_time[['ROI (%)']])

    # Campaign Comparison
    st.subheader("📈 Campaign Performance")
    performance = df_filtered.groupby('Campaign').agg({
        'Cost': 'sum',
        'Revenue': 'sum',
        'Conversions': 'sum'
    })
    performance['ROI (%)'] = ((performance['Revenue'] - performance['Cost']) / performance['Cost']) * 100

    st.bar_chart(performance[['ROI (%)']])

    # Detailed Table
    st.subheader("🧾 Detailed Data")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("👈 Upload an Excel or CSV file to get started.")
    st.markdown("""
    ### Sample Columns Your File Should Contain:
    - **Date**
    - **Campaign**
    - **Cost**
    - **Revenue**
    - **Conversions**
    
    You can add extra columns like "Channel", "Platform", etc., for deeper analysis.
    """)
