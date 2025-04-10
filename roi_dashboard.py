import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import time

# ---------------------- CONFIG ----------------------
st.set_page_config(
    page_title="Advanced ROI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- STYLES ----------------------
ANIMATED_KPI_STYLE = """
    <style>
    .kpi-card {
        padding: 1rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #e0f7fa, #e0f2f1);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 10px;
        transition: transform 0.3s ease;
    }
    .kpi-card:hover {
        transform: scale(1.05);
    }
    </style>
"""

st.markdown(ANIMATED_KPI_STYLE, unsafe_allow_html=True)

# ---------------------- SIDEBAR ----------------------
st.sidebar.title("📁 Upload Data & Settings")

uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV File", type=["xlsx", "csv"])
dark_mode = st.sidebar.toggle("🌙 Dark Mode")

# Tabs navigation
selected_tab = st.sidebar.radio("Navigate", ["Dashboard", "Manual Calculator"], index=0)

# ---------------------- THEME ----------------------
if dark_mode:
    st.markdown("""
        <style>
            body, .stApp { background-color: #0e1117; color: #FAFAFA; }
            .css-1d391kg, .css-1v0mbdj, .css-ffhzg2, .css-1k2i4n7 { color: #FAFAFA !important; }
            .stButton>button { background-color: #2e7bcf; color: white; border-radius: 8px; }
        </style>
    """, unsafe_allow_html=True)

# ---------------------- DASHBOARD TAB ----------------------
if selected_tab == "Dashboard":
    st.title("📊 ROI Dashboard - Campaign Insights")

    if uploaded_file is not None:
        with st.spinner("Processing your data..."):
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            try:
                df['Date'] = pd.to_datetime(df['Date'])
                df['Profit'] = df['Revenue'] - df['Cost']
                df['ROI (%)'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
                df['Cost/Conversion'] = df['Cost'] / df['Conversions']
                df['Revenue/Conversion'] = df['Revenue'] / df['Conversions']
            except Exception as e:
                st.error(f"Error in processing data: {e}")
                st.stop()

        st.success("✅ Data successfully loaded!")
        st.subheader("📋 Data Preview")
        st.dataframe(df, use_container_width=True)

        # Filter by campaign and date
        with st.expander("📅 Filter & View"):
            col1, col2 = st.columns(2)
            with col1:
                selected_campaigns = st.multiselect("Select Campaign(s)", df['Campaign'].unique(), default=df['Campaign'].unique())
            with col2:
                start_date = st.date_input("Start Date", value=df['Date'].min())
                end_date = st.date_input("End Date", value=df['Date'].max())

        mask = (
            df['Campaign'].isin(selected_campaigns) &
            (df['Date'] >= pd.to_datetime(start_date)) &
            (df['Date'] <= pd.to_datetime(end_date))
        )
        df_filtered = df[mask]

        st.markdown("### 🚀 Performance Summary")
        kpi_cols = st.columns(5)
        kpis = [
            ("💸 Total Investment", f"${df_filtered['Cost'].sum():,.2f}"),
            ("💰 Total Revenue", f"${df_filtered['Revenue'].sum():,.2f}"),
            ("📈 Net Profit", f"${df_filtered['Profit'].sum():,.2f}"),
            ("📊 Avg ROI", f"{df_filtered['ROI (%)'].mean():.2f}%"),
            ("👥 Total Conversions", int(df_filtered['Conversions'].sum())),
        ]
        for col, (label, value) in zip(kpi_cols, kpis):
            with col:
                st.markdown(f"""
                    <div class="kpi-card">
                        <h5>{label}</h5>
                        <h2>{value}</h2>
                    </div>
                """, unsafe_allow_html=True)

        # ROI over time chart
        st.markdown("### 📆 ROI Over Time")
        roi_time = df_filtered.groupby('Date').agg({'Cost': 'sum', 'Revenue': 'sum'})
        roi_time['ROI (%)'] = ((roi_time['Revenue'] - roi_time['Cost']) / roi_time['Cost']) * 100
        st.plotly_chart(px.line(roi_time, y='ROI (%)', title="ROI Trend"), use_container_width=True)

        # Campaign performance
        st.markdown("### 🎯 Campaign Comparison")
        camp_perf = df_filtered.groupby('Campaign').agg({'Cost': 'sum', 'Revenue': 'sum', 'Conversions': 'sum'})
        camp_perf['ROI (%)'] = ((camp_perf['Revenue'] - camp_perf['Cost']) / camp_perf['Cost']) * 100
        st.plotly_chart(px.bar(camp_perf, y='ROI (%)', title="Campaign ROI (%)", color=camp_perf.index), use_container_width=True)

    else:
        st.info("👈 Upload an Excel or CSV file to get started.")
        st.markdown("""
        ### 📌 Your file should include columns like:
        - Date
        - Campaign
        - Cost
        - Revenue
        - Conversions
        """)

# ---------------------- MANUAL CALCULATOR TAB ----------------------
elif selected_tab == "Manual Calculator":
    st.title("🧮 Manual ROI & Annualized ROI Calculator")

    with st.form("manual_roi"):
        col1, col2 = st.columns(2)
        with col1:
            investment = st.number_input("💰 Investment ($)", min_value=0.0, step=100.0)
            start_date_manual = st.date_input("📅 Start Date", value=datetime(2024, 1, 1))
        with col2:
            returns = st.number_input("📈 Return ($)", min_value=0.0, step=100.0)
            end_date_manual = st.date_input("📅 End Date", value=datetime.now())

        submitted = st.form_submit_button("Calculate ROI")

    if submitted:
        if investment > 0:
            days = (end_date_manual - start_date_manual).days
            years = days / 365.25 if days > 0 else 0
            roi = ((returns - investment) / investment) * 100

            st.markdown(f"## 🔢 ROI: **{roi:.2f}%**")
            if years > 0:
                annualized_roi = ((returns / investment) ** (1 / years) - 1) * 100
                st.markdown(f"## 📅 Annualized ROI: **{annualized_roi:.2f}%**")
            else:
                st.warning("Start date must be before end date to calculate annualized ROI.")
        else:
            st.warning("Please enter a valid investment amount.")
