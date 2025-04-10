import streamlit as st
import pandas as pd
import bcrypt
import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

# ---------- Constants ----------
USER_FILE = "users.csv"

# ---------- User Auth Functions ----------
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_row = pd.DataFrame([{"username": username, "password": hashed_pw}])
    users = pd.concat([users, new_row], ignore_index=True)
    users.to_csv(USER_FILE, index=False)

def verify_user(username, password):
    users = load_users()
    user = users[users.username == username]
    if not user.empty:
        return bcrypt.checkpw(password.encode(), user.iloc[0].password.encode())
    return False

# ---------- App UI ----------
st.set_page_config(page_title="ROI Dashboard Login", layout="wide")
st.title("🔐 ROI Dashboard with Analysis")

menu = st.sidebar.selectbox("Menu", ["Login", "Register", "ROI Calculator", "File ROI Analysis"])

if menu == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(username, password):
            st.success(f"Welcome {username}!")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
        else:
            st.error("Invalid username or password.")

elif menu == "Register":
    st.subheader("Create New Account")
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Register"):
        if new_user and new_pass:
            save_user(new_user, new_pass)
            st.success("User registered successfully! Please login.")
        else:
            st.warning("Please enter both username and password.")

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
