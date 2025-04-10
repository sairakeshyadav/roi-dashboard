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

# Sidebar menu control
if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Login"])
else:
    if st.session_state.username == "admin":
        menu = st.sidebar.selectbox("Menu", ["ROI Calculator", "File ROI Analysis", "Admin", "Logout"])
    else:
        menu = st.sidebar.selectbox("Menu", ["ROI Calculator", "File ROI Analysis", "Logout"])

# Login Section
if menu == "Login":
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

# Logout Section
elif menu == "Logout":
    st.session_state.logged_in = False
    st.session_state.username = None
    st.success("You have been logged out.")
    st.stop()

# Manual ROI Calculator
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

# File ROI Analysis
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

# Admin Dashboard
elif menu == "Admin":
    st.subheader("🔐 Admin Dashboard")
    st.write("Manage application users securely.")

    users_df = load_users()

    st.markdown("### 👥 Existing Users")
    st.dataframe(users_df.drop(columns=["password"]))  # Hide passwords

    # --- Add New User ---
    st.markdown("### ➕ Add New User")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Add User"):
        if new_username and new_password:
            if new_username in users_df['username'].values:
                st.warning("User already exists.")
            else:
                save_user(new_username, new_password)
                st.success(f"User '{new_username}' added. Please refresh the page to see the update.")
        else:
            st.warning("Username and password cannot be empty.")

    # --- Reset Password ---
    st.markdown("### 🔁 Reset User Password")
    user_to_reset = st.selectbox("Select user", users_df[users_df.username != "admin"]["username"].tolist())
    new_reset_password = st.text_input("New Password for Selected User", type="password")
    if st.button("Reset Password"):
        if user_to_reset and new_reset_password:
            users_df.loc[users_df["username"] == user_to_reset, "password"] = bcrypt.hashpw(new_reset_password.encode(), bcrypt.gensalt()).decode()
            users_df.to_csv(USER_FILE, index=False)
            st.success(f"Password for '{user_to_reset}' has been reset.")
        else:
            st.warning("Please provide a valid user and password.")

    # --- Delete User ---
    st.markdown("### ❌ Delete User")
    user_to_delete = st.selectbox("Select user to delete", users_df[users_df.username != "admin"]["username"].tolist())
    if st.button("Delete User"):
        users_df = users_df[users_df["username"] != user_to_delete]
        users_df.to_csv(USER_FILE, index=False)
        st.success(f"User '{user_to_delete}' deleted. Please refresh the page to see the update.")
