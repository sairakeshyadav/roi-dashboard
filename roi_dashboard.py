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
    st.markdown("""
        <style>
            .login-container {
                display: flex;
                justify-content: center;
                align-items: start;
                height: 100vh;
                padding-top: 5vh;
            }
            .login-box {
                text-align: center;
                width: 300px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-container'><div class='login-box'>", unsafe_allow_html=True)
    st.title("🔐 ROI Dashboard Login")
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
        st.rerun()

    st.stop()

# Main Interface
if st.session_state.logged_in:
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.markdown(f"### 👤 Logged in as: `{st.session_state.username}`")
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.experimental_rerun()

    tab1, tab2, tab3 = st.tabs(["📈 ROI Calculator", "📂 File ROI Analysis", "🔐 Admin Management"])

    with tab1:
        # Manual ROI Calculator Code
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

    with tab2:
        # File ROI Analysis Code
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
                    df['Days'] = (df['Date'].max() - df['Date'].min()).days
                    df['Annualized ROI'] = np.where(
                        df['Days'] > 0,
                        ((1 + df['ROI (%)'] / 100) ** (365.25 / df['Days']) - 1) * 100,
                        0
                    )

                    st.success("✅ Data Processed Successfully")

                    roi_time = df.groupby("Date").agg({"Cost": "sum", "Revenue": "sum"}).reset_index()
                    roi_time["ROI (%)"] = np.where(
                        roi_time["Cost"] != 0,
                        ((roi_time["Revenue"] - roi_time["Cost"]) / roi_time["Cost"]) * 100,
                        0
                    )
                    fig = px.line(roi_time, x="Date", y="ROI (%)", title="ROI (%) Over Time", markers=True)
                    st.plotly_chart(fig, use_container_width=True)

                    roi_summary = df.groupby("Campaign").agg({
                        'Cost': 'sum',
                        'Revenue': 'sum',
                        'Profit': 'sum',
                        'Conversions': 'sum'
                    }).reset_index()
                    roi_summary['ROI (%)'] = np.where(roi_summary["Cost"] != 0, ((roi_summary["Revenue"] - roi_summary["Cost"]) / roi_summary["Cost"]) * 100, 0)

                    campaign_fig = go.Figure()
                    campaign_fig.add_trace(go.Bar(x=roi_summary['Campaign'], y=roi_summary['ROI (%)'], name='ROI (%)'))
                    campaign_fig.add_trace(go.Bar(x=roi_summary['Campaign'], y=roi_summary['Profit'], name='Profit'))
                    campaign_fig.update_layout(barmode='group', title="Campaign ROI Summary", xaxis_title="Campaign", yaxis_title="Value")
                    st.plotly_chart(campaign_fig, use_container_width=True)

            except Exception as e:
                st.error(f"⚠️ Error processing file: {e}")
        else:
            st.info("📤 Please upload a file to get started.")

    with tab3:
        if st.session_state.username == "admin":
            st.subheader("🔐 Admin Dashboard")
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
            user_to_reset = st.selectbox("Select user", users_df[users_df.username != "admin"]["username"].tolist())
            new_reset_password = st.text_input("New Password for Selected User", type="password")
            if st.button("Reset Password"):
                if user_to_reset and new_reset_password:
                    users_df.loc[users_df["username"] == user_to_reset, "password"] = bcrypt.hashpw(new_reset_password.encode(), bcrypt.gensalt()).decode()
                    users_df.to_csv(USER_FILE, index=False)
                    st.success(f"Password for '{user_to_reset}' has been reset.")
                else:
                    st.warning("Please provide a valid user and password.")

            st.markdown("### ❌ Delete User")
            user_to_delete = st.selectbox("Select user to delete", users_df[users_df.username != "admin"]["username"].tolist())
            if st.button("Delete User"):
                users_df = users_df[users_df["username"] != user_to_delete]
                users_df.to_csv(USER_FILE, index=False)
                st.success(f"User '{user_to_delete}' deleted. Please refresh the page to see the update.")
        else:
            st.warning("Access Denied: Admins only")
