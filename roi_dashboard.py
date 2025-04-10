import streamlit as st
import pandas as pd
import bcrypt
import os
from datetime import datetime

# ---------- Constants ----------
USER_FILE = "users.csv"

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

st.set_page_config(page_title="ROI Dashboard Login", layout="centered")
st.title("🔐 ROI Dashboard Login")

menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

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
