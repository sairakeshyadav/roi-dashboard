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
import PyPDF2
import docx

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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_trigger' not in st.session_state:
    st.session_state.login_trigger = False

if not st.session_state.logged_in:
    st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
    st.title("🔐 ROI Dashboard Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if verify_user(username, password):
            st.session_state.username = username
            st.session_state.logged_in = True
            st.session_state.login_trigger = True
        else:
            st.error("Invalid username or password.")

    if st.session_state.login_trigger:
        log_user_activity(st.session_state.username, "Logged in")
        st.session_state.login_trigger = False
        st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f"<div class='user-display'>👤 {st.session_state.username}</div>", unsafe_allow_html=True)
    st.markdown("<div class='logout-button'>", unsafe_allow_html=True)
    if st.button("Logout"):
        log_user_activity(st.session_state.username, "Logged out")
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    tab_names = ["ROI Calculator", "ROI File Analysis"]
    if st.session_state.username == "admin":
        tab_names.extend(["Admin Panel", "User Activity", "Export Data"])

    tabs = st.tabs(tab_names)

    with tabs[0]:
        st.subheader("📈 Manual ROI Calculator")
        date = st.date_input("Select Date")
        impressions = st.number_input("Impressions", value=0)
        clicks = st.number_input("Clicks", value=0)
        conversions = st.number_input("Conversions", value=0)
        revenue = st.number_input("Revenue", value=0.0)
        cost = st.number_input("Cost", value=0.0)

        if st.button("Calculate ROI"):
            roi = ((revenue - cost) / cost) * 100 if cost != 0 else 0
            st.success(f"ROI: {roi:.2f}%")

    with tabs[1]:
        st.subheader("📂 ROI File Analysis")
        uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx", "pdf", "docx", "json"])

        if uploaded_file:
            file_type = uploaded_file.type
            df = None

            if file_type == "text/csv":
                df = pd.read_csv(uploaded_file)

            elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                df = pd.read_excel(uploaded_file)

            elif file_type == "application/pdf":
                try:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    pdf_text = ""
                    for page in reader.pages:
                        pdf_text += page.extract_text() or ""
                    st.text_area("📄 PDF Content", pdf_text, height=300)
                    st.info("PDF content displayed as plain text.")
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")

            elif file_type == "application/json":
                try:
                    data = pd.read_json(uploaded_file)
                    df = pd.json_normalize(data)
                except Exception as e:
                    st.error(f"Error reading JSON: {e}")

            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                try:
                    doc = docx.Document(uploaded_file)
                    full_text = "\n".join([para.text for para in doc.paragraphs])
                    st.text_area("📄 DOCX Content", full_text, height=300)
                except Exception as e:
                    st.error(f"Error reading DOCX: {e}")

            else:
                st.warning("Unsupported file type.")

            if df is not None:
                st.dataframe(df)
                if 'Cost' in df.columns and 'Revenue' in df.columns:
                    df['ROI'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
                    st.success("✅ ROI calculated and added.")
                    st.dataframe(df)

    if st.session_state.username == "admin":
        with tabs[2]:
            st.subheader("🔐 Admin Panel")
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password", key="add_user_pass")
            if st.button("Add User"):
                save_user(new_user, new_pass)
                st.success("User added successfully")

            st.markdown("---")
            st.subheader("Reset User Password")
            reset_user = st.text_input("Username to Reset Password")
            new_reset_pass = st.text_input("New Password", type="password", key="reset_user_pass")
            if st.button("🔁 Reset User Password"):
                users = load_users()
                if reset_user in users['username'].values:
                    users.loc[users['username'] == reset_user, 'password'] = bcrypt.hashpw(new_reset_pass.encode(), bcrypt.gensalt()).decode()
                    users.to_csv(USER_FILE, index=False)
                    st.success(f"Password for user '{reset_user}' has been reset.")
                else:
                    st.error("User not found.")

            st.markdown("---")
            st.subheader("Delete User")
            del_user = st.text_input("Username to Delete")
            if st.button("❌ Delete User"):
                users = load_users()
                if del_user in users['username'].values:
                    users = users[users['username'] != del_user]
                    users.to_csv(USER_FILE, index=False)
                    st.success(f"User '{del_user}' deleted successfully.")
                else:
                    st.error("User not found.")

        with tabs[3]:
            st.subheader("📊 User Activity Log")
            if os.path.exists(ACTIVITY_LOG_FILE):
                log_df = pd.read_csv(ACTIVITY_LOG_FILE)
                st.dataframe(log_df)
            else:
                st.info("No activity log found.")

        with tabs[4]:
            st.subheader("⬇️ Export Data")
            if os.path.exists(ACTIVITY_LOG_FILE):
                with open(ACTIVITY_LOG_FILE, "rb") as f:
                    st.download_button("Download Activity Log", f, file_name="activity_log.csv")
