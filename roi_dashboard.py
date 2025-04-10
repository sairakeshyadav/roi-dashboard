import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="🎨 Stylish ROI Dashboard", layout="wide", page_icon="📊")

# Custom CSS Styling
st.markdown("""
    <style>
        .main {
            background-color: #f0f2f6;
        }
        .css-18e3th9 {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .css-1d391kg {
            background-color: #ffffff;
            border-radius: 10px;
        }
        h1, h2, h3 {
            color: #1f77b4;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🎨 Stylish & Interactive ROI Dashboard")

# Sidebar for Upload
st.sidebar.header("📤 Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Choose Excel or CSV File", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file, engine='openpyxl')
    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
        st.stop()

    df['Date'] = pd.to_datetime(df['Date'])
    df['Profit'] = df['Revenue'] - df['Cost']
    df['ROI (%)'] = ((df['Profit']) / df['Cost']) * 100
    df['Cost/Conversion'] = df['Cost'] / df['Conversions']
    df['Revenue/Conversion'] = df['Revenue'] / df['Conversions']

    # Filters
    st.sidebar.subheader("🔍 Filters")
    selected_campaigns = st.sidebar.multiselect("Select Campaign(s)", df['Campaign'].unique(), default=list(df['Campaign'].unique()))
    date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])

    filtered_df = df[(df['Campaign'].isin(selected_campaigns)) &
                     (df['Date'].dt.date >= date_range[0]) &
                     (df['Date'].dt.date <= date_range[1])]

    # KPI Metrics
    st.markdown("## 📈 Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    total_cost = filtered_df['Cost'].sum()
    total_revenue = filtered_df['Revenue'].sum()
    total_profit = total_revenue - total_cost
    roi = ((total_profit) / total_cost) * 100 if total_cost else 0
    years = (filtered_df['Date'].max() - filtered_df['Date'].min()).days / 365.25
    annualized_roi = ((1 + roi / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

    kpi1.metric("💰 Investment", f"${total_cost:,.2f}")
    kpi2.metric("📈 Revenue", f"${total_revenue:,.2f}")
    kpi3.metric("📊 Profit", f"${total_profit:,.2f}")
    kpi4.metric("📉 ROI", f"{roi:.2f}%")
    kpi5.metric("📆 Annualized ROI", f"{annualized_roi:.2f}%")

    # Charts
    st.markdown("## 📊 ROI Over Time")
    roi_by_date = filtered_df.groupby('Date').agg({'Revenue': 'sum', 'Cost': 'sum'}).reset_index()
    roi_by_date['ROI (%)'] = ((roi_by_date['Revenue'] - roi_by_date['Cost']) / roi_by_date['Cost']) * 100
    fig = px.line(roi_by_date, x='Date', y='ROI (%)', title='📆 ROI Trend', markers=True, template="plotly")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("## 🧾 Campaign Performance")
    if 'Campaign' in filtered_df.columns:
        campaign_perf = filtered_df.groupby('Campaign').agg({'Revenue': 'sum', 'Cost': 'sum'}).reset_index()
        campaign_perf['ROI (%)'] = ((campaign_perf['Revenue'] - campaign_perf['Cost']) / campaign_perf['Cost']) * 100
        fig2 = px.bar(campaign_perf, x='Campaign', y='ROI (%)', color='ROI (%)', title='🚀 Campaign ROI', template='plotly_dark')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("## 🔍 Detailed Data")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("👈 Upload a file to get started or use the manual calculator below.")

    st.markdown("## 🔧 Manual ROI Calculator")
    with st.form("manual_calc"):
        col1, col2 = st.columns(2)
        with col1:
            investment = st.number_input("Investment ($)", value=1000.0, step=100.0)
            revenue = st.number_input("Revenue ($)", value=1500.0, step=100.0)
        with col2:
            manual_dates = st.date_input("Select Start & End Date", [datetime.today(), datetime.today()])
        submit = st.form_submit_button("Calculate")

    if submit:
        roi = ((revenue - investment) / investment) * 100 if investment > 0 else 0
        years = (manual_dates[1] - manual_dates[0]).days / 365.25 if len(manual_dates) == 2 else 0
        annualized_roi = ((1 + roi / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
        st.success(f"📊 ROI: {roi:.2f}%")
        st.success(f"📆 Annualized ROI: {annualized_roi:.2f}%")
