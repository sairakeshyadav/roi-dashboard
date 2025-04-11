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
import streamlit.components.v1 as components

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

def reset_password(username, new_password):
    users = load_users()
    hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    users.loc[users.username == username, 'password'] = hashed_pw
    users.to_csv(USER_FILE, index=False)

def delete_user(username):
    users = load_users()
    users = users[users.username != username]
    users.to_csv(USER_FILE, index=False)

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
all_tabs = [
    "📊 ROI Calculator", 
    "📂 ROI File Analysis", 
    "📅 Monthly ROI Trends"
]
if is_admin:
    all_tabs.extend([
        "👨‍💼 Admin Panel", 
        "📈 User Activity", 
    ])

tabs = st.tabs(all_tabs)

# ROI Calculator Tab
with tabs[0]:
    st.subheader("📊 ROI Calculator")
    cost = st.number_input("Enter Campaign Cost", min_value=0.0, format="%.2f")
    revenue = st.number_input("Enter Campaign Revenue", min_value=0.0, format="%.2f")
    if st.button("Calculate ROI"):
        if cost > 0:
            roi = ((revenue - cost) / cost) * 100
            st.success(f"ROI is {roi:.2f}%")
        else:
            st.error("Cost must be greater than 0")

# ROI File Analysis Tab
with tabs[1]:
    st.subheader("📂 ROI File Analysis")
    uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx", "pdf", "docx"], key="roi_analysis")

    if uploaded_file:
        ext = uploaded_file.name.split(".")[-1]
        df = None
        if ext == "csv":
            df = pd.read_csv(uploaded_file)
        elif ext == "xlsx":
            df = pd.read_excel(uploaded_file)
        elif ext == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
            st.text_area("PDF Content", text)
        elif ext == "docx":
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs])
            st.text_area("Word Document Content", text)

        if df is not None and {'Cost', 'Revenue', 'Campaign'}.issubset(df.columns):
            df['ROI'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
            grouped = df.groupby("Campaign").agg({"Cost": "sum", "Revenue": "sum", "ROI": "mean"}).reset_index()
            grouped = grouped.sort_values(by="ROI", ascending=False)

            total_cost = grouped['Cost'].sum()
            total_revenue = grouped['Revenue'].sum()
            total_roi = ((total_revenue - total_cost) / total_cost) * 100 if total_cost != 0 else 0

            st.markdown(f"""
                <div class="fade-in" style="margin-top: 1rem; padding: 1rem; background-color: #e3f2fd; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                    <h3 style="color:#1565c0;">📈 Total Summary</h3>
                    <p><strong>Total Revenue:</strong> ₹{total_revenue:,.2f}</p>
                    <p><strong>Total Cost:</strong> ₹{total_cost:,.2f}</p>
                    <p><strong>Total ROI:</strong> <span style="color:#2e7d32; font-weight:bold;">{total_roi:.2f}%</span></p>
                </div>
            """, unsafe_allow_html=True)

            for _, row in grouped.iterrows():
                if isinstance(row['Campaign'], str) and not row['Campaign'].startswith("202"):
                    st.markdown(f"""
                        <div class="fade-in" style="margin: 10px 0; padding: 1rem; background-color: #ffffff; border-left: 5px solid #2196f3; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <h4>📌 {row['Campaign']}</h4>
                            <p><strong>Revenue:</strong> ₹{row['Revenue']:,.2f}</p>
                            <p><strong>Cost:</strong> ₹{row['Cost']:,.2f}</p>
                            <p><strong>ROI:</strong> <span style="color:#28a745; font-weight:bold;">{row['ROI']:.2f}%</span></p>
                        </div>
                    """, unsafe_allow_html=True)

            csv = grouped.to_csv(index=False).encode('utf-8')
            st.download_button("Download ROI Summary", csv, "roi_summary.csv", "text/csv")

# Monthly ROI Trends Tab
with tabs[2]:
    st.subheader("📅 Monthly ROI Trends")
    st.info("Coming soon with detailed visualizations!")

with tabs[3]:
    st.subheader("👨‍💼 Admin Panel")

    st.markdown("### ➕ Add New User")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Add User"):
        if new_username and new_password:
            existing_users = load_users()
            if new_username in existing_users['username'].values:
                st.warning("Username already exists.")
            else:
                save_user(new_username, new_password)
                st.success(f"User `{new_username}` added successfully.")
        else:
            st.error("Please fill both username and password.")

    st.markdown("---")
    st.markdown("### 🔧 Manage Existing Users")
    users = load_users()
    selected_user = st.selectbox("Select User to Manage", users['username'])
    new_pass = st.text_input("Reset Password", type="password", key="admin_reset_password")
    if st.button("🔁 Reset Password"):
        reset_password(selected_user, new_pass)
        st.success("Password reset successful")

    if st.button("❌ Delete User"):
        delete_user(selected_user)
        st.success("User deleted")


    with tabs[4]:
        st.subheader("📈 User Activity")
        if os.path.exists(ACTIVITY_LOG_FILE):
            logs = pd.read_csv(ACTIVITY_LOG_FILE)
            st.dataframe(logs)
        else:
            st.warning("No activity log found.")

