import streamlit as st
import pandas as pd
import bcrypt
import os
from datetime import datetime
import numpy as np
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

# ---------- App UI Config ----------
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
        .fade-in {
            animation: fadeIn 1s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .logout-button {
            position: absolute;
            right: 1rem;
            top: 1rem;
            background-color: #ff4d4d;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
        }
        .logout-button:hover {
            background-color: #ff0000;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Login Page ----------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.markdown("""
        <div style='text-align:center; padding-top: 50px;'>
            <h2>🔐 ROI Dashboard Login</h2>
        </div>
    """, unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            log_user_activity(username, "Login")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ---------- Main App ----------
st.markdown(f"### Welcome, `{st.session_state.username}`")
if st.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

is_admin = st.session_state.username == "admin"

# ---------- Tabs ----------
all_tabs = ["📊 ROI Calculator", "📂 ROI File Analysis"]
if is_admin:
    all_tabs.extend(["👨‍💼 Admin Panel", "📈 User Activity", "📥 Export Data"])

tabs = st.tabs(all_tabs)

# ---------- ROI Calculator ----------
with tabs[0]:
    st.subheader("📊 ROI Calculator")
    cost = st.number_input("Enter Cost", min_value=0.0)
    revenue = st.number_input("Enter Revenue", min_value=0.0)
    date_range = st.date_input("Select Date Range", [])

    if st.button("Calculate ROI"):
        if cost == 0:
            st.error("Cost cannot be zero.")
        else:
            roi = ((revenue - cost) / cost) * 100
            st.success(f"ROI: {roi:.2f}%")
            if date_range:
                st.info(f"Analysis from {date_range[0]} to {date_range[-1]}")

# ---------- ROI File Analysis ----------
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
                pdf_text = "".join(page.extract_text() or "" for page in reader.pages)
                st.text_area("📄 PDF Content", pdf_text, height=300)
            except Exception as e:
                st.error(f"❌ Error reading PDF: {e}")
        elif file_type == "application/json":
            try:
                data = pd.read_json(uploaded_file)
                df = pd.json_normalize(data)
            except Exception as e:
                st.error(f"❌ Error reading JSON: {e}")
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            try:
                doc = docx.Document(uploaded_file)
                full_text = "\n".join([para.text for para in doc.paragraphs])
                st.text_area("📄 DOCX Content", full_text, height=300)
            except Exception as e:
                st.error(f"❌ Error reading DOCX: {e}")

        if df is not None:
            st.dataframe(df)

            if 'Cost' in df.columns and 'Revenue' in df.columns:
                df['ROI'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100

                with st.container():
                    st.markdown("""
                        <div class="fade-in" style="padding: 1rem; background-color: #f9f9f9; border-radius: 12px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                            <h4 style="color: #4a4a4a;">🔍 ROI Summary</h4>
                    """, unsafe_allow_html=True)

                    avg_roi = df['ROI'].mean()
                    total_rev = df['Revenue'].sum()
                    total_cost = df['Cost'].sum()

                    st.write(f"✅ **Total Revenue**: ₹{total_rev:,.2f}")
                    st.write(f"💸 **Total Cost**: ₹{total_cost:,.2f}")
                    st.write(f"📈 **Average ROI**: {avg_roi:.2f}%")

                    st.markdown("</div>", unsafe_allow_html=True)

                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download ROI Data", csv_data, "roi_processed.csv", "text/csv")







# ---------- Admin Panel ----------
if is_admin:
    with tabs[2]:
        st.subheader("👨‍💼 Admin Panel")
        st.markdown("### ➕ Add User")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Create User"):
            if new_user and new_pass:
                save_user(new_user, new_pass)
                st.success(f"User {new_user} added.")

        st.markdown("### 🔁 Reset User Password")
        reset_user = st.text_input("Username to Reset")
        new_reset_pass = st.text_input("New Password", type="password", key="reset_pass")
        if st.button("Reset Password"):
            users = load_users()
            if reset_user in users['username'].values:
                users.loc[users.username == reset_user, 'password'] = bcrypt.hashpw(new_reset_pass.encode(), bcrypt.gensalt()).decode()
                users.to_csv(USER_FILE, index=False)
                st.success("Password reset successful.")

        st.markdown("### ❌ Delete User")
        del_user = st.text_input("Username to Delete")
        if st.button("Delete User"):
            users = load_users()
            if del_user in users['username'].values:
                users = users[users.username != del_user]
                users.to_csv(USER_FILE, index=False)
                st.success(f"User {del_user} deleted.")

# ---------- User Activity ----------
if is_admin:
    with tabs[3]:
        st.subheader("📈 User Activity")
        if os.path.exists(ACTIVITY_LOG_FILE):
            activity_df = pd.read_csv(ACTIVITY_LOG_FILE)
            st.dataframe(activity_df)
        else:
            st.warning("No user activity logged yet.")

# ---------- Export Data ----------
if is_admin:
    with tabs[4]:
        st.subheader("📥 Export Data")
        if st.button("Download ROI Data as CSV"):
            dummy_data = pd.DataFrame({"Metric": ["ROI"], "Value": ["N/A"]})
            csv = dummy_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "roi_data.csv", "text/csv", key='download-csv')
