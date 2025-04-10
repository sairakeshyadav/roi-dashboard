import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import bcrypt
import json
import os
import random
import smtplib
from email.message import EmailMessage

# ---------------------- CONFIG ----------------------
st.set_page_config(
    page_title="Advanced ROI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- EMAIL CONFIG ----------------------
EMAIL_ADDRESS = "youremail@example.com"  # replace with your real email
EMAIL_PASSWORD = "yourapppassword"  # use App Password for Gmail
OTP_STORE = {}
USER_FILE = "users.json"

def send_otp_email(recipient_email, otp):
    msg = EmailMessage()
    msg['Subject'] = 'Your OTP Verification Code'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg.set_content(f"Your OTP code is: {otp}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user(username, email, password_hash):
    users = load_users()
    users[username] = {"email": email, "password": password_hash}
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

# ---------------------- LOGIN / REGISTER ----------------------
def register_section():
    st.subheader("📝 Register with Email Verification")
    new_user = st.text_input("Choose a username")
    new_email = st.text_input("Email address")
    new_pass = st.text_input("Choose a password", type="password")
    confirm_pass = st.text_input("Confirm password", type="password")

    if st.button("Send OTP"):
        if new_user and new_email and new_pass == confirm_pass:
            otp = str(random.randint(100000, 999999))
            OTP_STORE[new_email] = otp
            send_otp_email(new_email, otp)
            st.session_state["otp_pending"] = {
                "username": new_user,
                "email": new_email,
                "password": new_pass
            }
            st.success("✅ OTP sent to your email!")
        else:
            st.warning("Please fill all fields correctly.")

    if "otp_pending" in st.session_state:
        otp_input = st.text_input("Enter the OTP sent to your email")
        if st.button("Verify OTP"):
            actual_otp = OTP_STORE.get(st.session_state["otp_pending"]["email"])
            if otp_input == actual_otp:
                user_info = st.session_state.pop("otp_pending")
                save_user(
                    user_info["username"],
                    user_info["email"],
                    hash_password(user_info["password"])
                )
                st.success("🎉 Registration complete! You can now log in.")
            else:
                st.error("❌ Invalid OTP.")

def login_section():
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_users()
        if username in users and check_password(password, users[username]['password']):
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.success(f"✅ Welcome back, {username}!")
        else:
            st.error("❌ Invalid credentials")

# ---------------------- APP ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Register"])
    with tab1:
        login_section()
    with tab2:
        register_section()
    st.stop()

# ---------------------- DASHBOARD ----------------------
st.sidebar.title("📁 Upload Data & Settings")
uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV File", type=["xlsx", "csv"])

selected_tab = st.sidebar.radio("Navigate", ["Dashboard", "Manual Calculator"], index=0)

if selected_tab == "Dashboard":
    st.title("📊 ROI Dashboard - Campaign Insights")

    if uploaded_file is not None:
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

        st.subheader("📋 Data Preview")
        st.dataframe(df, use_container_width=True)

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
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("💸 Total Investment", f"${df_filtered['Cost'].sum():,.2f}")
        col2.metric("💰 Total Revenue", f"${df_filtered['Revenue'].sum():,.2f}")
        col3.metric("📈 Net Profit", f"${df_filtered['Profit'].sum():,.2f}")
        col4.metric("📊 Avg ROI", f"{df_filtered['ROI (%)'].mean():.2f}%")
        col5.metric("👥 Total Conversions", int(df_filtered['Conversions'].sum()))

        st.markdown("### 📆 ROI Over Time")
        roi_time = df_filtered.groupby('Date').agg({'Cost': 'sum', 'Revenue': 'sum'})
        roi_time['ROI (%)'] = ((roi_time['Revenue'] - roi_time['Cost']) / roi_time['Cost']) * 100
        st.plotly_chart(px.line(roi_time, y='ROI (%)', title="ROI Trend"), use_container_width=True)

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
