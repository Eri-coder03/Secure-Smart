"""Illustrative environmental alerts; values are arbitrary demo indices, not safety limits."""
from datetime import datetime

import pandas as pd
import streamlit as st

SENSORS = [
    {"sensor_id": "ENV-01", "location": "Lab Wing", "signal": "Gas and smoke index"},
    {"sensor_id": "ENV-02", "location": "Parking", "signal": "Water level index"},
]


def simulate_emergencies(tick, scenario):
    """Return stable, repeatable simulated readings from 0 to 100."""
    stage = min(tick, 4)
    rows = []
    for sensor in SENSORS:
        active = (scenario == "Gas / smoke" and sensor["sensor_id"] == "ENV-01") or (
            scenario == "Water leak" and sensor["sensor_id"] == "ENV-02"
        )
        index = [12, 31, 57, 78, 94][stage] if active else 12
        level = "EMERGENCY" if index >= 75 else "WATCH" if index >= 50 else "NORMAL"
        rows.append({**sensor, "reading_index": index, "level": level})
    return pd.DataFrame(rows)


def update_emergency_history(frame, tick, scenario):
    if "emergency_history" not in st.session_state:
        st.session_state.emergency_history = []
    key = (tick, scenario)
    if st.session_state.get("last_emergency_key") == key:
        return
    st.session_state.last_emergency_key = key
    for _, row in frame[frame["level"].isin(["WATCH", "EMERGENCY"])].iterrows():
        st.session_state.emergency_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update": tick,
            "sensor_id": row["sensor_id"],
            "location": row["location"],
            "signal": row["signal"],
            "reading_index": int(row["reading_index"]),
            "level": row["level"],
        })
    st.session_state.emergency_history = st.session_state.emergency_history[-200:]


def get_emergency_history():
    return pd.DataFrame(st.session_state.get("emergency_history", []))
