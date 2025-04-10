import streamlit as st
import pandas as pd
import bcrypt
import plotly.express as px
from datetime import datetime

# -------- CONFIG --------
st.set_page_config(page_title="ROI Dashboard", layout="wide")

# -------- USER AUTH --------
USER_FILE = "users.csv"

def load_users():
    try:
        return pd.read_csv(USER_FILE)
    except:
        return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users = users.append({"username": username, "password": hashed_pw}, ignore_index=True)
    users.to_csv(USER_FILE, index=False)

def login(username, password):
    users = load_users()
    user = users[users["username"] == username]
    if not user.empty and bcrypt.checkpw(password.encode(), user.iloc[0]["password"].encode()):
        return True
    return False

# -------- SIDEBAR AUTH SECTION --------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_section():
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login(username, password):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.sidebar.error("Invalid credentials")

def register_section():
    st.sidebar.title("📝 Register")
    new_user = st.sidebar.text_input("New Username")
    new_pass = st.sidebar.text_input("New Password", type="password")
    if st.sidebar.button("Register"):
        users = load_users()
        if new_user in users["username"].values:
            st.sidebar.warning("Username already exists.")
        else:
            save_user(new_user, new_pass)
            st.sidebar.success("User registered. Please log in.")

def logout_section():
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.experimental_rerun()

# -------- MAIN LOGIC --------
if not st.session_state.logged_in:
    login_section()
    st.sidebar.markdown("---")
    register_section()
else:
    st.sidebar.markdown(f"👤 Logged in as **{st.session_state.user}**")
    logout_section()

    # -------- Dashboard Logic Here --------
    st.title("📊 ROI Dashboard - Welcome!")

    uploaded_file = st.sidebar.file_uploader("Upload Excel or CSV", type=["xlsx", "csv"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df['Date'] = pd.to_datetime(df['Date'])
        df['Profit'] = df['Revenue'] - df['Cost']
        df['ROI (%)'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100

        with st.expander("📅 Filter by Date"):
            start = st.date_input("Start Date", df['Date'].min())
            end = st.date_input("End Date", df['Date'].max())
            df = df[(df['Date'] >= pd.to_datetime(start)) & (df['Date'] <= pd.to_datetime(end))]

        st.write("### 📈 Metrics")
        st.metric("Total Investment", f"${df['Cost'].sum():,.2f}")
        st.metric("Total Revenue", f"${df['Revenue'].sum():,.2f}")
        st.metric("Net Profit", f"${df['Profit'].sum():,.2f}")
        st.metric("Avg ROI (%)", f"{df['ROI (%)'].mean():.2f}")

        st.write("### 📊 ROI Over Time")
        chart_df = df.groupby("Date")[["Cost", "Revenue"]].sum()
        chart_df["ROI (%)"] = ((chart_df["Revenue"] - chart_df["Cost"]) / chart_df["Cost"]) * 100
        st.plotly_chart(px.line(chart_df, y="ROI (%)", title="ROI Trend"), use_container_width=True)

        st.write("### 📄 Raw Data")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Upload data to begin analyzing.")

