import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Page config
st.set_page_config("📊 ROI Dashboard", layout="wide")

# Dark mode toggle
st.sidebar.header("🛠️ Display Settings")
dark_mode = st.sidebar.toggle("🌙 Enable Dark Mode", value=False)

# Apply custom CSS for light/dark mode
if dark_mode:
    st.markdown(
        """
        <style>
        body { background-color: #121212; color: white; }
        .stApp { background-color: #121212; }
        .block-container { background-color: #1e1e1e; color: white; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    theme = "plotly_dark"
    text_color = "white"
else:
    st.markdown(
        """
        <style>
        body { background-color: #ffffff; color: black; }
        .stApp { background-color: #ffffff; }
        .block-container { background-color: #f9f9f9; color: black; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    theme = "plotly_white"
    text_color = "black"

# File uploader
st.sidebar.header("📂 Upload Your File")
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])

# Manual date input
st.sidebar.subheader("📅 Filter by Date Range")
start_date = st.sidebar.date_input("Start Date", datetime(2024, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

# Page title
st.markdown(f"<h1 style='text-align: center; color:{text_color}'>📊 ROI Dashboard</h1>", unsafe_allow_html=True)

# Load data function
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

# Process data
if uploaded_file:
    df = load_data(uploaded_file)
    df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]

    st.markdown("### 📋 Data Preview")
    st.dataframe(df, use_container_width=True)

    # Campaign selection
    campaigns = df['Campaign'].unique()
    selected_campaigns = st.sidebar.multiselect("🎯 Select Campaigns", campaigns, default=campaigns)
    df = df[df['Campaign'].isin(selected_campaigns)]

    # KPIs
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💸 Investment", f"${df['Cost'].sum():,.2f}")
    col2.metric("📈 Revenue", f"${df['Revenue'].sum():,.2f}")
    col3.metric("💹 Net Profit", f"${df['Profit'].sum():,.2f}")
    col4.metric("📊 Avg ROI", f"{df['ROI (%)'].mean():.2f}%")
    col5.metric("📆 Annualized ROI", f"{df['Annualized ROI (%)'].mean():.2f}%")

    # ROI Over Time
    st.markdown("### 🕒 ROI Over Time")
    time_grouped = df.groupby('Date')[['Cost', 'Revenue']].sum().reset_index()
    time_grouped['ROI (%)'] = ((time_grouped['Revenue'] - time_grouped['Cost']) / time_grouped['Cost']) * 100
    fig_time = px.line(time_grouped, x='Date', y='ROI (%)', markers=True, template=theme)
    st.plotly_chart(fig_time, use_container_width=True)

    # Campaign Performance
    st.markdown("### 🚀 Campaign Performance")
    camp_grouped = df.groupby('Campaign')[['Cost', 'Revenue', 'Conversions']].sum().reset_index()
    camp_grouped['ROI (%)'] = ((camp_grouped['Revenue'] - camp_grouped['Cost']) / camp_grouped['Cost']) * 100
    fig_camp = px.bar(camp_grouped, x='Campaign', y='ROI (%)', color='ROI (%)', template=theme,
                      color_continuous_scale='Teal', title="ROI by Campaign")
    st.plotly_chart(fig_camp, use_container_width=True)

else:
    st.info("👈 Upload a CSV or Excel file to get started.")
    st.markdown("### Or use the manual ROI calculator below.")

    st.subheader("🧮 Manual ROI Calculator")
    with st.form("manual_roi"):
        col1, col2 = st.columns(2)
        with col1:
            investment = st.number_input("💰 Investment ($)", min_value=0.0, step=100.0)
        with col2:
            returns = st.number_input("📈 Return ($)", min_value=0.0, step=100.0)
        calc_button = st.form_submit_button("Calculate ROI")

    if calc_button:
        if investment > 0:
            roi = ((returns - investment) / investment) * 100
            st.success(f"🎯 Your ROI is: **{roi:.2f}%**")
        else:
            st.warning("Please enter an investment greater than 0.")
