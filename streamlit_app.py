import streamlit as st
import pandas as pd
from datetime import date
import plotly_calplot
from streamlit_gsheets import GSheetsConnection

# --- Google Sheets Setup ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Load data once into session state
if "payments_df" not in st.session_state:
    data = conn.read(worksheet="Blad1", ttl=0)
    if data.empty:
        st.session_state.payments_df = pd.DataFrame(columns=["Name", "Date"])
    else:
        st.session_state.payments_df = data.copy()
        if "Date" not in st.session_state.payments_df.columns:
            st.session_state.payments_df["Date"] = pd.NaT

df = st.session_state.payments_df

# --- Streamlit UI ---
st.title("💸 Payment Tracker")

payer = st.text_input("Who paid?")
payment_date = st.date_input("Payment date", value=date.today())

# Button click: update session and sheet
if st.button("Add Payment"):
    if payer:
        new_entry = pd.DataFrame([{"Name": payer, "Date": str(payment_date)}])
        st.session_state.payments_df = pd.concat([st.session_state.payments_df, new_entry], ignore_index=True)
        conn.update(worksheet="Blad1", data=st.session_state.payments_df)
        st.success(f"Added payment for {payer} on {payment_date}")
    else:
        st.warning("Please enter a name before adding a payment.")

# --- Display Data ---
if not st.session_state.payments_df.empty:
    df = st.session_state.payments_df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    last_entry = df.iloc[-1]
    st.success(f"Last payment was made by: **{last_entry['Name']}** on {last_entry['Date'].date()}")

    st.subheader("📊 Payment Counts")
    counts = df["Name"].value_counts().reset_index()
    counts.columns = ["Name", "Times Paid"]
    st.table(counts)

    with st.expander("📅 Payment History", expanded=False):
        st.dataframe(df)

    st.subheader("🗓️ Calendar View")
    grouped = (
        df.groupby("Date")["Name"]
        .apply(lambda x: ", ".join(x))
        .reset_index()
    )
    grouped["Payments"] = grouped["Name"].apply(lambda x: len(x.split(", ")))
    grouped.rename(columns={"Name": "Who"}, inplace=True)

    fig = plotly_calplot.calplot(
        grouped,
        x="Date",
        y="Payments",
        text="Who",  # hover text with names
        colorscale="greens",
        month_lines_width=2,
        gap=1,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No payments recorded yet.")
