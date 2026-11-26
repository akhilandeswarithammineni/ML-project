
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

st.set_page_config(
    page_title="Load Sentinel",
    page_icon="⚡",
    layout="wide"
)

DB_PATH = Path(__file__).parent / "load_sentinel.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                meter TEXT,
                reading REAL,
                status TEXT
            )
        """)


def detect_anomalies(readings):
    values = pd.Series(readings).astype(float)
    median = values.median()
    mad = (values - median).abs().median()

    if mad == 0:
        return values.index[
            (values - median).abs() > 0
        ].tolist()

    score = 0.6745 * (values - median).abs() / mad
    return values.index[score > 3.5].tolist()


def save_results(results):
    if not results:
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany("""
            INSERT INTO anomalies (timestamp, meter, reading, status)
            VALUES (?, ?, ?, ?)
        """, results)


init_db()

st.title("⚡ Load Sentinel")
st.subheader("Electricity Load Anomaly Detection System")
st.write("Upload electricity meter readings to identify unusual consumption.")

uploaded_file = st.file_uploader(
    "Upload electricity data (CSV)",
    type=["csv"]
)

tariff = st.number_input(
    "Tariff per kWh (₹)",
    min_value=0.0,
    value=5.0,
    step=0.5
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        if df.empty or len(df.columns) < 2:
            st.error("CSV must have a timestamp column and at least one meter column.")
        else:
            timestamp_column = df.columns[0]
            meter_columns = df.columns[1:]

            all_results = []
            chart_data = {}

            for meter in meter_columns:
                readings = pd.to_numeric(df[meter], errors="coerce")
                valid = readings.dropna()

                chart_data[str(meter)] = readings

                if len(valid) < 5:
                    continue

                indexes = detect_anomalies(valid)

                for index in indexes:
                    all_results.append({
                        "Timestamp": str(df.loc[index, timestamp_column]),
                        "Meter": str(meter),
                        "Reading (kW)": float(readings.loc[index]),
                        "Status": "Anomaly"
                    })

            total_readings = sum(
                pd.to_numeric(df[col], errors="coerce").notna().sum()
                for col in meter_columns
            )

            st.subheader("Dashboard")

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Readings", int(total_readings))
            c2.metric("Detected Anomalies", len(all_results))
            c3.metric("Tariff per kWh", f"₹{tariff:.2f}")

            st.subheader("Electricity Load Chart")
            st.line_chart(pd.DataFrame(chart_data))

            st.subheader("Detected Anomalies")

            if all_results:
                result_df = pd.DataFrame(all_results)
                st.dataframe(result_df, use_container_width=True)

                if st.button("Save anomalies to database"):
                    save_results([
                        (
                            item["Timestamp"],
                            item["Meter"],
                            item["Reading (kW)"],
                            item["Status"]
                        )
                        for item in all_results
                    ])
                    st.success("Anomalies saved to the SQLite database.")
            else:
                st.success("No anomalies detected in the uploaded data.")

            st.info(
                "Note: This version detects statistical outliers. "
                "It does not yet calculate excess energy or estimated anomaly cost."
            )

    except Exception:
        st.error("Could not read the CSV. Check the column names and file format.")

st.divider()
st.caption("Load Sentinel | Mini Project | Statistical Anomaly Detection")

