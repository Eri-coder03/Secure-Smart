"""Store demo incidents for this Streamlit browser session."""
from datetime import datetime

import pandas as pd
import streamlit as st


def update_history(frame, tick):
    if "incident_history" not in st.session_state:
        st.session_state.incident_history = []
    if "last_recorded_tick" not in st.session_state:
        st.session_state.last_recorded_tick = -1
    if st.session_state.last_recorded_tick == tick:
        return
    st.session_state.last_recorded_tick = tick
    for _, row in frame[frame["severity"].isin(["HIGH", "CRITICAL"])].iterrows():
        st.session_state.incident_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tick": tick,
            "device_id": row["device_id"],
            "location": row["location"],
            "severity": row["severity"],
            "risk_score": int(row["risk_score"]),
            "ml_anomaly": bool(row["ml_anomaly"]),
            "status": row["status"],
        })
    st.session_state.incident_history = st.session_state.incident_history[-200:]


def get_history():
    return pd.DataFrame(st.session_state.get("incident_history", []))
