import streamlit as st
import pandas as pd
import bcrypt
import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

# ---------- Constants ----------
USER_FILE = "users.csv"
DEFAULT_ADMIN = {"username": "admin", "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()}

# ---------- User Auth Functions ----------
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    if username not in users['username'].values:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        new_row = pd.DataFrame([{"username": username, "password": hashed_pw}])
        users = pd.concat([users, new_row], ignore_index=True)
        users.to_csv(USER_FILE, index=False)

def verify_user(username, password):
    users = load_users()
    if users.empty:
        save_user(DEFAULT_ADMIN["username"], "admin123")
        users = load_users()
    user = users[users.username == username]
    if not user.empty:
        return bcrypt.checkpw(password.encode(), user.iloc[0].password.encode())
    return False

# ---------- App UI ----------
st.set_page_config(page_title="ROI Dashboard Login", layout="wide")
st.title("🔐 ROI Dashboard with Analysis")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Login"])
else:
    if st.session_state.username == "admin":
        menu = st.sidebar.selectbox("Menu", ["ROI Calculator", "File ROI Analysis", "Admin", "Logout"])
    else:
        menu = st.sidebar.selectbox("Menu", ["ROI Calculator", "File ROI Analysis", "Logout"])

if menu == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(username, password):
            st.success(f"Welcome {username}!")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")

elif menu == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = None
    st.success("You have been logged out.")
    st.experimental_rerun()

elif menu == "ROI Calculator":
    st.subheader("📈 Manual ROI Calculator")

    investment = st.number_input("Enter Investment Amount ($)", min_value=0.0, step=100.0)
    returns = st.number_input("Enter Return Amount ($)", min_value=0.0, step=100.0)
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    if st.button("Calculate ROI"):
        if investment > 0:
            roi = (returns - investment) / investment
            st.metric("ROI", f"{roi:.2%}")

            # Annualized ROI
            days = (end_date - start_date).days
            if days > 0:
                years = days / 365.25
                annualized_roi = (1 + roi) ** (1 / years) - 1
                st.metric("Annualized ROI", f"{annualized_roi:.2%}")
            else:
                st.warning("End date must be after start date to calculate annualized ROI.")
        else:
            st.error("Investment must be greater than 0.")

elif menu == "File ROI Analysis":
    st.subheader("📂 Upload and Analyze ROI Data")

    uploaded_file = st.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.dataframe(df.head())

        try:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Profit'] = df['Revenue'] - df['Cost']
            df['ROI (%)'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
            df['Cost/Conversion'] = df['Cost'] / df['Conversions']
            df['Revenue/Conversion'] = df['Revenue'] / df['Conversions']

            st.success("Data Processed Successfully")
            st.dataframe(df)

            roi_summary = df.groupby('Campaign').agg({
                'Cost': 'sum',
                'Revenue': 'sum',
                'Profit': 'sum',
                'Conversions': 'sum',
                'ROI (%)': 'mean'
            }).reset_index()

            st.subheader("📊 Campaign ROI Summary")
            st.dataframe(roi_summary)

        except Exception as e:
            st.error(f"Error processing data: {e}")
    else:
        st.info("Upload a file to analyze campaign ROI data.")

elif menu == "Admin":
    st.subheader("🔐 Admin Dashboard")
    st.info("You are logged in as admin. Future admin tools and user management can go here.")
