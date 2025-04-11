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
        .fade-in {
            animation: fadeIn 1s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
""", unsafe_allow_html=True)

# (The rest of your code remains unchanged up to ROI File Analysis)

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
                    st.markdown(f"<div class='fade-in'><textarea rows='15' cols='80'>{pdf_text}</textarea></div>", unsafe_allow_html=True)
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
                    st.markdown(f"<div class='fade-in'><textarea rows='15' cols='80'>{full_text}</textarea></div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error reading DOCX: {e}")
            else:
                st.warning("Unsupported file type.")

            if df is not None:
                st.dataframe(df)
                if 'Cost' in df.columns and 'Revenue' in df.columns:
                    df['ROI'] = ((df['Revenue'] - df['Cost']) / df['Cost']) * 100
                    st.success("✅ ROI calculated and added.")

                    st.markdown("#### 📊 ROI Visualization")
                    fig = px.bar(df, x=df.index, y='ROI', title="ROI by Row", color='ROI', color_continuous_scale='Blues')
                    st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(df)
