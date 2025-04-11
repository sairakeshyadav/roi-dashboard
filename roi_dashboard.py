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

# ---------- App Config ----------
st.set_page_config(page_title="ROI Dashboard", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

if not st.session_state.authenticated:
    st.title("🔐 ROI Dashboard Login")
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
st.sidebar.title(f"Welcome, {st.session_state.username}")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

is_admin = st.session_state.username == "admin"

all_tabs = ["ROI Calculator", "ROI File Analysis", "Monthly ROI Trends"]
if is_admin:
    all_tabs.extend(["Admin Panel", "User Activity"])

tabs = st.tabs(all_tabs)

# ---------- ROI Calculator ----------
with tabs[0]:
    st.header("📊 ROI Calculator")
    cost = st.number_input("Enter Cost", min_value=0.0)
    revenue = st.number_input("Enter Revenue", min_value=0.0)
    if st.button("Calculate ROI"):
        if cost == 0:
            st.error("Cost cannot be zero.")
        else:
            roi = ((revenue - cost) / cost) * 100
            st.success(f"ROI: {roi:.2f}%")

# ---------- ROI File Analysis ----------
with tabs[1]:
    st.header("📂 ROI File Analysis")
    uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx", "pdf", "docx"])
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

            st.metric("Total Revenue", f"₹{total_revenue:,.2f}")
            st.metric("Total Cost", f"₹{total_cost:,.2f}")
            st.metric("Total ROI", f"{total_roi:.2f}%")

            for _, row in grouped.iterrows():
                st.markdown(f"**{row['Campaign']}** | Revenue: ₹{row['Revenue']:,.2f} | Cost: ₹{row['Cost']:,.2f} | ROI: {row['ROI']:.2f}%")

            csv = grouped.to_csv(index=False).encode('utf-8')
            st.download_button("Download ROI Summary", csv, "roi_summary.csv", "text/csv")

# ---------- Monthly ROI Trends ----------
with tabs[2]:
    st.header("📅 Monthly ROI Trends")
    st.info("Coming soon...")

# ---------- Admin Panel ----------
if is_admin:
    with tabs[3]:
        st.header("👨‍💼 Admin Panel")

        st.subheader("Add New User")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Add User"):
            if new_username and new_password:
                existing_users = load_users()
                if new_username in existing_users['username'].values:
                    st.warning("Username already exists.")
                else:
                    save_user(new_username, new_password)
                    st.success(f"User {new_username} added successfully.")

        st.subheader("Manage Existing Users")
        users = load_users()
        selected_user = st.selectbox("Select User", users['username'])
        new_pass = st.text_input("Reset Password", type="password")
        if st.button("Reset Password"):
            reset_password(selected_user, new_pass)
            st.success("Password reset successfully.")

        if st.button("Delete User"):
            delete_user(selected_user)
            st.success("User deleted successfully.")

    with tabs[4]:
        st.header("📈 User Activity")
        if os.path.exists(ACTIVITY_LOG_FILE):
            logs = pd.read_csv(ACTIVITY_LOG_FILE)
            st.dataframe(logs)
        else:
            st.warning("No user activity found.")
