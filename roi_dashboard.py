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

# Login Section
if not st.session_state.logged_in:
    st.markdown("""
        <style>
            .login-container {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
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
                st.success(f"Welcome {username}!")
                st.balloons()
                st.rerun()
            else:
                st.error("Invalid username or password.")

    st.markdown("</div></div>", unsafe_allow_html=True)
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
        exec(open("manual_roi_calculator.py").read())

    with tab2:
        exec(open("file_roi_analysis.py").read())

    with tab3:
        if st.session_state.username == "admin":
            exec(open("admin_dashboard.py").read())
        else:
            st.warning("Access Denied: Admins only")
