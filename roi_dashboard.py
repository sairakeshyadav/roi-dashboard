import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Sidebar config
st.set_page_config("📊 ROI Dashboard", layout="wide")

# Dark Mode Toggle
st.sidebar.header("🛠️ Display Settings")
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False)

# Theme setting
theme = "plotly_dark" if dark_mode else "plotly_white"
bg_color = "#1e1e1e" if dark_mode else "#f9f9f9"
font_color = "white" if dark_mode else "black"

# File uploader
st.sidebar.header("📂 Upload Your File")
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

# Manual Date Range Filter
st.sidebar.subheader("📅 Filter by Date Range")
start_date = st.sidebar.date_input("Start Date", datetime(2024, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

# Main title
st.markdown(f"<h1 style='text-align: center; color:{font_color}'>📊 ROI Dashboard</h1>", unsafe_allow_html=True)

# Load and preprocess data
def load_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df['Date'] = pd.to_datetime(df['Date'])
    df['Profit'] = df['Revenue'] - df['Cost']
    df['ROI (%)'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
    df['Annualized ROI (%)'] = (((df['Revenue'] / df['Cost']) ** (365 / df['Date'].nunique())) - 1) * 100
    df['Cost/Conversion'] = df['Cost'] / df['Conversions']
    df['Revenue/Conversion'] = df['Revenue'] / df['Conversions']
    return df

if uploaded_file:
    df = load_data(uploaded_file)
    df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]

    with st.expander("📋 View Raw Data"):
        st.dataframe(df, use_container_width=True)

    campaigns = df['Campaign'].unique()
    selected_campaigns = st.sidebar.multiselect("🎯 Filter by Campaign", campaigns, default=campaigns)
    df = df[df['Campaign'].isin(selected_campaigns)]

    # Suggest Top Campaigns
    top_by_roi = df.groupby('Campaign')['ROI (%)'].mean().sort_values(ascending=False).head(3)
    top_by_revenue = df.groupby('Campaign')['Revenue'].sum().sort_values(ascending=False).head(3)
    top_by_conversions = df.groupby('Campaign')['Conversions'].sum().sort_values(ascending=False).head(3)

    st.markdown(f"### 🧠 Top Campaigns Suggestions")
    col1, col2, col3 = st.columns(3)
    col1.metric("🔥 Top ROI", top_by_roi.idxmax(), f"{top_by_roi.max():.2f}%")
    col2.metric("💰 Top Revenue", top_by_revenue.idxmax(), f"${top_by_revenue.max():,.2f}")
    col3.metric("🚀 Top Conversions", top_by_conversions.idxmax(), f"{int(top_by_conversions.max())}")

    # KPIs
    st.markdown("### 📈 Key Metrics")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("💸 Total Investment", f"${df['Cost'].sum():,.2f}")
    kpi2.metric("📈 Total Revenue", f"${df['Revenue'].sum():,.2f}")
    kpi3.metric("💹 Net Profit", f"${df['Profit'].sum():,.2f}")
    kpi4.metric("📊 Avg ROI", f"{df['ROI (%)'].mean():.2f}%")
    kpi5.metric("⏳ Annualized ROI", f"{df['Annualized ROI (%)'].mean():.2f}%")

    # ROI Over Time Chart
    st.markdown("### 📊 ROI Over Time")
    roi_time = df.groupby('Date')[['Cost', 'Revenue']].sum().reset_index()
    roi_time['ROI (%)'] = ((roi_time['Revenue'] - roi_time['Cost']) / roi_time['Cost']) * 100
    fig = px.line(roi_time, x='Date', y='ROI (%)', markers=True, template=theme, title="ROI Over Time")
    st.plotly_chart(fig, use_container_width=True)

    # Campaign Comparison Chart
    st.markdown("### 📉 Campaign Comparison")
    camp_perf = df.groupby('Campaign')[['Cost', 'Revenue', 'Conversions']].sum()
    camp_perf['ROI (%)'] = ((camp_perf['Revenue'] - camp_perf['Cost']) / camp_perf['Cost']) * 100
    fig2 = px.bar(camp_perf, x=camp_perf.index, y='ROI (%)', template=theme, color='ROI (%)',
                  title="ROI by Campaign", color_continuous_scale="Teal")
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("👈 Upload a file to get started, or scroll to use manual ROI calculator.")

    # Manual ROI Calculator
    st.subheader("🧮 Manual ROI Calculator")
    with st.form("manual_roi"):
        col1, col2 = st.columns(2)
        with col1:
            manual_cost = st.number_input("💵 Investment", min_value=0.0, format="%.2f")
        with col2:
            manual_return = st.number_input("💰 Return", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Calculate")

    if submitted:
        if manual_cost > 0:
            roi = ((manual_return - manual_cost) / manual_cost) * 100
            st.success(f"📊 Your ROI is **{roi:.2f}%**")
        else:
            st.error("Please enter an investment greater than 0.")

    # Sample Format
    st.markdown("---")
    st.markdown("### 📁 Sample File Format")
    st.markdown("""
    Your uploaded file should contain the following columns:
    - **Date**
    - **Campaign**
    - **Cost**
    - **Revenue**
    - **Conversions**
    """)

