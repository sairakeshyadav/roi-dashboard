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
st.set_page_config(page_title="ROI Dashboard", layout="wide")

st.markdown("""
    <style>
        body {
            background: linear-gradient(to right, #e0f7fa, #e1bee7);
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
            align-items: flex-start;
            height: 100vh;
            background: linear-gradient(to right, #4facfe, #00f2fe);
            padding-top: 80px;
        }
        .login-box {
            background: white;
            padding: 3rem 2rem;
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            width: 350px;
            text-align: center;
            animation: fadeIn 1s ease-in-out;
        }
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(30px); }
            100% { opacity: 1; transform: translateY(0); }
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

if os.getenv("ENV") == "development":
    st.session_state.logged_in = True
    st.session_state.username = "admin"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if "trigger_rerun" not in st.session_state:
    st.session_state.trigger_rerun = False

# Login Section
if not st.session_state.logged_in:
    st.markdown("<div class='login-container'><div class='login-box'>", unsafe_allow_html=True)
    st.image("https://img.icons8.com/fluency/96/lock.png", width=60)
    st.title("ROI Dashboard Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        with st.spinner("Verifying credentials..."):
            time.sleep(1)
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.trigger_rerun = True
            else:
                st.error("Invalid username or password.")

    st.markdown("</div></div>", unsafe_allow_html=True)

    if st.session_state.get("trigger_rerun", False):
        st.session_state.trigger_rerun = False
        try:
            st.rerun()
        except Exception as e:
            st.warning(f"Could not rerun: {e}")

    st.stop()

# User Display and Logout
st.markdown(f"<div class='user-display'>👤 <b>{st.session_state.username}</b></div>", unsafe_allow_html=True)
st.markdown("<div class='logout-button'>", unsafe_allow_html=True)
if st.button("Logout", key="logout", help="Click to logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# Tabs for App Sections
roi_tab, file_tab, admin_tab = st.tabs(["ROI Calculator", "ROI File Analysis", "Admin Management"])

with roi_tab:
    st.subheader("📈 Manual ROI Calculator")
    investment = st.number_input("Enter Investment Amount ($)", min_value=0.0, step=100.0)
    returns = st.number_input("Enter Return Amount ($)", min_value=0.0, step=100.0)
    start_date = st.date_input("Start Date")
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
                st.warning("End date must be after start date to calculate annualized ROI.")
        else:
            st.error("Investment must be greater than 0.")

with file_tab:
    st.subheader("📂 Upload and Analyze ROI Data")
    uploaded_file = st.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.success("✅ File Uploaded Successfully")

            required_columns = {"Date", "Campaign", "Cost", "Revenue", "Conversions"}
            if not required_columns.issubset(df.columns):
                st.error(f"❌ Missing columns: {required_columns - set(df.columns)}")
            else:
                df['Date'] = pd.to_datetime(df['Date'])
                df['Profit'] = df['Revenue'] - df['Cost']
                df['ROI (%)'] = np.where(df['Cost'] != 0, ((df['Revenue'] - df['Cost']) / df['Cost']) * 100, 0)
                df['Cost/Conversion'] = np.where(df['Conversions'] != 0, df['Cost'] / df['Conversions'], 0)
                df['Revenue/Conversion'] = np.where(df['Conversions'] != 0, df['Revenue'] / df['Conversions'], 0)
                df['Annualized ROI (%)'] = 0.0
                for i in df.index:
                    days = (df.loc[i, 'Date'] - df['Date'].min()).days
                    if days > 0 and df.loc[i, 'Cost'] != 0:
                        roi = (df.loc[i, 'Revenue'] - df.loc[i, 'Cost']) / df.loc[i, 'Cost']
                        years = days / 365.25
                        df.loc[i, 'Annualized ROI (%)'] = (1 + roi) ** (1 / years) - 1

                st.subheader("📊 ROI Over Time")
                roi_time = df.groupby("Date").agg({"Cost": "sum", "Revenue": "sum"}).reset_index()
                roi_time["ROI (%)"] = np.where(roi_time["Cost"] != 0, ((roi_time["Revenue"] - roi_time["Cost"]) / roi_time["Cost"]) * 100, 0)
                fig = px.line(roi_time, x="Date", y="ROI (%)", title="ROI (%) Over Time", markers=True)
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📈 Campaign ROI Summary")
                roi_summary = df.groupby("Campaign").agg({
                    'Cost': 'sum',
                    'Revenue': 'sum',
                    'Profit': 'sum',
                    'Conversions': 'sum'
                }).reset_index()
                roi_summary['ROI (%)'] = np.where(roi_summary["Cost"] != 0, ((roi_summary["Revenue"] - roi_summary["Cost"]) / roi_summary["Cost"]) * 100, 0)

                for _, row in roi_summary.iterrows():
                    st.markdown(f"""
                        <div style='background: linear-gradient(to right, #e3f2fd, #e8f5e9); padding: 1rem; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
                            <h4 style='margin-bottom:0.5rem;'>📢 {row['Campaign']}</h4>
                            <b>Cost:</b> ${row['Cost']:,.2f} | 
                            <b>Revenue:</b> ${row['Revenue']:,.2f} | 
                            <b>Profit:</b> ${row['Profit']:,.2f} | 
                            <b>Conversions:</b> {row['Conversions']} | 
                            <b>ROI (%):</b> {row['ROI (%)']:.2f}%
                        </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"⚠️ Error processing file: {e}")
    else:
        st.info("📤 Please upload a file to get started.")

with admin_tab:
    st.subheader("🔐 Admin Dashboard")
    st.write("Manage application users securely.")

    users_df = load_users()
    st.markdown("### 👥 Existing Users")
    st.dataframe(users_df.drop(columns=["password"]))

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

    st.markdown("### 🔁 Reset User Password")
    non_admin_users = users_df[users_df.username != "admin"]
    if not non_admin_users.empty:
        user_to_reset = st.selectbox("Select user", non_admin_users["username"].tolist())
        new_reset_password = st.text_input("New Password for Selected User", type="password")
        if st.button("Reset Password"):
            if user_to_reset and new_reset_password:
                users_df.loc[users_df["username"] == user_to_reset, "password"] = bcrypt.hashpw(new_reset_password.encode(), bcrypt.gensalt()).decode()
                users_df.to_csv(USER_FILE, index=False)
                st.success(f"Password for '{user_to_reset}' has been reset.")
            else:
                st.warning("Please provide a valid user and password.")

    st.markdown("### ❌ Delete User")
    if not non_admin_users.empty:
        user_to_delete = st.selectbox("Select user to delete", non_admin_users["username"].tolist())
        if st.button("Delete User"):
            users_df = users_df[users_df["username"] != user_to_delete]
            users_df.to_csv(USER_FILE, index=False)
            st.success(f"User '{user_to_delete}' deleted. Please refresh the page to see the update.")
