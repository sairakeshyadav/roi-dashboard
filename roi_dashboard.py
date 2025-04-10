import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ---------- Page Config ----------
st.set_page_config(page_title="💹 ROI Dashboard", layout="wide")

st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight:600;
    }
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.title("💹 ROI Analytics Dashboard")
st.markdown("Use this tool to analyze campaign performance, calculate ROI, and make better investment decisions.")

# ---------- Sidebar ----------
st.sidebar.header("📁 Upload Campaign File")
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

# ---------- Manual Calculator ----------
with st.expander("🧮 Manual ROI Calculator (No Upload Needed)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        manual_investment = st.number_input("💸 Investment Amount ($)", min_value=0.0, value=1000.0)
    with col2:
        manual_return = st.number_input("💰 Return Amount ($)", min_value=0.0, value=1500.0)
    
    if manual_investment > 0:
        manual_roi = (manual_return - manual_investment) / manual_investment * 100
        st.success(f"📊 Your ROI is **{manual_roi:.2f}%**")
    else:
        st.warning("Please enter a valid investment amount.")

# ---------- Data Upload Section ----------
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    
    # ---------- Data Preprocessing ----------
    try:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Profit'] = df['Revenue'] - df['Cost']
        df['ROI (%)'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
        df['Annualized ROI (%)'] = df.apply(
            lambda row: ((1 + ((row['Revenue'] - row['Cost']) / row['Cost'])) ** (365 / max((datetime.now() - row['Date']).days, 1)) - 1) * 100,
            axis=1
        )
        df['Cost/Conversion'] = df['Cost'] / df['Conversions']
        df['Revenue/Conversion'] = df['Revenue'] / df['Conversions']
    except Exception as e:
        st.error(f"Data formatting error: {e}")
        st.stop()

    # ---------- Filter Section ----------
    st.sidebar.header("📅 Filter Data")
    min_date = df['Date'].min()
    max_date = df['Date'].max()

    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    if len(date_range) == 2:
        df = df[(df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))]

    selected_campaigns = st.sidebar.multiselect("🎯 Campaigns", options=df['Campaign'].unique(), default=df['Campaign'].unique())
    df = df[df['Campaign'].isin(selected_campaigns)]

    # ---------- Metrics Section ----------
    st.markdown("## 📈 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💸 Total Investment", f"${df['Cost'].sum():,.2f}")
    col2.metric("💰 Total Revenue", f"${df['Revenue'].sum():,.2f}")
    col3.metric("📈 Net Profit", f"${df['Profit'].sum():,.2f}")
    col4.metric("📊 Avg ROI", f"{df['ROI (%)'].mean():.2f}%")
    col5.metric("🧠 Annualized ROI", f"{df['Annualized ROI (%)'].mean():.2f}%")

    # ---------- Charts ----------
    st.markdown("## 📊 ROI Over Time")
    fig = px.line(df, x="Date", y="ROI (%)", color="Campaign", markers=True, title="Daily ROI Trends")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("## 📊 Revenue vs Cost by Campaign")
    bar_df = df.groupby("Campaign").agg({'Revenue': 'sum', 'Cost': 'sum'}).reset_index()
    fig2 = px.bar(bar_df, x="Campaign", y=["Revenue", "Cost"], barmode="group", title="Campaign Performance")
    st.plotly_chart(fig2, use_container_width=True)

    # ---------- Data Table ----------
    st.markdown("## 📄 Detailed Data")
    st.dataframe(df, use_container_width=True)

else:
    st.info("📁 Please upload a file to begin analyzing your campaign data.")
    st.markdown("""
    ### 🔍 Sample Format:
    - **Date** (YYYY-MM-DD)
    - **Campaign**
    - **Cost**
    - **Revenue**
    - **Conversions**
    """)

