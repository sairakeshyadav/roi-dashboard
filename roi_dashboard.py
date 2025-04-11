import streamlit as st
import pandas as pd
import bcrypt
import os
from datetime import datetime
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
import io

# ---------- Constants ----------
USER_FILE = "users.csv"
ACTIVITY_LOG_FILE = "user_activity_log.csv"
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

def log_user_activity(user, action):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_df = pd.DataFrame([[timestamp, user, action]], columns=["Timestamp", "User", "Action"])
    if os.path.exists(ACTIVITY_LOG_FILE):
        log_df.to_csv(ACTIVITY_LOG_FILE, mode='a', header=False, index=False)
    else:
        log_df.to_csv(ACTIVITY_LOG_FILE, index=False)

# ---------- App UI ----------
st.set_page_config(page_title="ROI Dashboard", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

        body {
            background: linear-gradient(to right, #e0f7fa, #e1bee7);
            font-family: 'Inter', sans-serif;
        }
        .stTabs [role="tab"] {
            padding: 0.75rem 1.5rem;
            margin-right: 1rem;
            font-size: 1.1rem;
            font-weight: bold;
            color: #4a4a4a;
            border-radius: 10px 10px 0 0;
            background-color: #f1f1f1;
            transition: all 0.3s ease-in-out;
        }
        .stTabs [role="tab"]:hover {
            background-color: #e0e0e0;
            transform: scale(1.05);
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff;
            border-bottom: 2px solid #4a90e2;
        }
        .stButton > button {
            transition: background-color 0.3s ease, transform 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #4a90e2;
            color: white;
            transform: scale(1.03);
        }
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background: linear-gradient(135deg, #74ebd5, #9face6);
            font-family: 'Inter', sans-serif;
        }
        .login-box {
            background: rgba(255, 255, 255, 0.95);
            padding: 3rem 2.5rem;
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            width: 360px;
            animation: slideUpFade 0.8s ease-in-out;
            text-align: center;
        }
        .login-box input {
            border-radius: 12px !important;
            padding: 10px !important;
        }
        .stButton > button {
            border-radius: 10px;
            padding: 10px 20px;
            font-weight: bold;
            background: #6a11cb;
            background: linear-gradient(to right, #2575fc, #6a11cb);
            color: white;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        @keyframes slideUpFade {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .logout-button {
            position: fixed;
            top: 15px;
            right: 20px;
            z-index: 999;
        }
        .user-display {
            position: fixed;
            top: 15px;
            right: 120px;
            background-color: #ffffff;
            padding: 6px 12px;
            border-radius: 10px;
            font-weight: 600;
            color: #333333;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            z-index: 998;
        }
        .logout-button .stButton > button {
            background-color: #f44336;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: bold;
        }
        .logout-button .stButton > button:hover {
            background-color: #d32f2f;
        }
    </style>
""", unsafe_allow_html=True)

if 'logged_in' in st.session_state and st.session_state.logged_in:
    tabs = st.tabs(["ROI Calculator", "ROI File Analysis", "Admin Panel", "User Activity", "Export Data"])

    with tabs[0]:
        st.subheader("📈 Manual ROI Calculator")
        investment = st.number_input("Enter Investment Amount ($)", min_value=0.0, step=100.0)
        returns = st.number_input("Enter Return Amount ($)", min_value=0.0, step=100.0)
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")

        if st.button("Calculate ROI"):
            if investment > 0:
                roi = (returns - investment) / investment
                st.metric("ROI", f"{roi:.2%}")

                days = (end_date - start_date).days
                if days > 0:
                    years = days / 365.25
                    annualized_roi = (1 + roi) ** (1 / years) - 1
                    st.metric("Annualized ROI", f"{annualized_roi:.2%}")
                else:
                    st.warning("End date must be after start date.")
            else:
                st.error("Investment must be greater than 0.")

    with tabs[1]:
        st.subheader("📂 ROI File Analysis")
        uploaded_file = st.file_uploader("Upload ROI Data File (CSV)", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("Preview of uploaded data:")
            st.dataframe(df.head())

            if "Investment" in df.columns and "Return" in df.columns:
                df["ROI"] = (df["Return"] - df["Investment"]) / df["Investment"]
                st.write("📊 ROI Calculations:")
                st.dataframe(df[["Investment", "Return", "ROI"]])

                fig = px.bar(df, y="ROI", title="ROI by Entry", labels={"index": "Entry", "ROI": "ROI"})
                st.plotly_chart(fig)
            else:
                st.error("File must contain 'Investment' and 'Return' columns.")

    with tabs[2]:
        st.subheader("🔐 Admin Panel")

        st.markdown("### Add New User")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Add User"):
            if new_user and new_pass:
                save_user(new_user, new_pass)
                st.success(f"User '{new_user}' added.")
                log_user_activity(st.session_state.username, f"Added user {new_user}")
            else:
                st.error("Please enter both username and password.")

        st.markdown("---")
        st.markdown("### Reset/Delete Existing User")
        users = load_users()
        usernames = users["username"].tolist()
        selected_user = st.selectbox("Select User", usernames)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 Reset User Password"):
                new_password = st.text_input("Enter New Password", key="reset_pass", type="password")
                if new_password:
                    hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    users.loc[users.username == selected_user, "password"] = hashed_pw
                    users.to_csv(USER_FILE, index=False)
                    st.success(f"Password for {selected_user} has been reset.")
                    log_user_activity(st.session_state.username, f"Reset password for {selected_user}")
        with col2:
            if selected_user != DEFAULT_ADMIN["username"] and st.button("❌ Delete User"):
                users = users[users.username != selected_user]
                users.to_csv(USER_FILE, index=False)
                st.success(f"User '{selected_user}' deleted.")
                log_user_activity(st.session_state.username, f"Deleted user {selected_user}")
            elif selected_user == DEFAULT_ADMIN["username"]:
                st.warning("Default admin user cannot be deleted.")

    with tabs[3]:
        st.subheader("📝 User Activity Log")
        if os.path.exists(ACTIVITY_LOG_FILE):
            logs = pd.read_csv(ACTIVITY_LOG_FILE)
            st.dataframe(logs.tail(100))
        else:
            st.info("No activity logs found.")

    with tabs[4]:
        st.subheader("📤 Export Data")

        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, "rb") as f:
                st.download_button(
                    label="Download Activity Log",
                    data=f,
                    file_name="user_activity_log.csv",
                    mime="text/csv"
                )

        if 'df' in locals():
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download ROI Analysis",
                data=csv_data,
                file_name="roi_analysis.csv",
                mime="text/csv"
            )
        else:
            st.info("Upload a ROI file to enable export.")
