import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="ROI Dashboard", layout="centered")

# Title
st.title("📈 ROI Dashboard")

# Input section
st.header("Enter Investment Data")
investment_amount = st.number_input("Investment Amount ($)", min_value=0.0, step=100.0)
investment_date = st.date_input("Investment Date", datetime.today())

return_amount = st.number_input("Return Amount ($)", min_value=0.0, step=100.0)
return_date = st.date_input("Return Date", datetime.today())

# Add button
if st.button("Calculate ROI"):
    # Calculate ROI
    profit = return_amount - investment_amount
    roi = (profit / investment_amount) if investment_amount else 0
    duration = (return_date - investment_date).days / 365.25
    annualized_roi = (1 + roi) ** (1 / duration) - 1 if duration > 0 else 0

    # Display summary
    st.subheader("ROI Summary")
    st.metric("Total Investment", f"${investment_amount:,.2f}")
    st.metric("Total Returns", f"${return_amount:,.2f}")
    st.metric("Net Profit", f"${profit:,.2f}")
    st.metric("ROI", f"{roi:.2%}")
    st.metric("Annualized ROI", f"{annualized_roi:.2%}")

    # Plot
    fig, ax = plt.subplots()
    ax.bar(["Investment", "Return"], [investment_amount, return_amount], color=["blue", "green"])
    ax.set_title("Investment vs Return")
    st.pyplot(fig)
