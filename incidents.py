"""Operator workflow for simulated alerts in one Streamlit session."""
from datetime import datetime

import pandas as pd
import streamlit as st


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sync_incidents(device_history, emergency_history):
    """Group each target's alerts into one case and retain the event timeline."""
    if "cases" not in st.session_state:
        st.session_state.cases = {}
    if "seen_alerts" not in st.session_state:
        st.session_state.seen_alerts = set()
    for source, history in (("Device", device_history), ("Environment", emergency_history)):
        if history.empty:
            continue
        for _, row in history.iterrows():
            update = int(row["tick"] if source == "Device" else row["update"])
            target = row["device_id"] if source == "Device" else row["sensor_id"]
            # The timestamp distinguishes repeat runs within a session.
            event_key = f'{source}:{row["timestamp"]}:{update}:{target}'
            if event_key in st.session_state.seen_alerts:
                continue
            st.session_state.seen_alerts.add(event_key)
            severity = row["severity"] if source == "Device" else row["level"]
            active = next((case for case in st.session_state.cases.values()
                           if case["source"] == source and case["target"] == target
                           and case["status"] != "Resolved"), None)
            if active is None:
                case_id = f'INC-{len(st.session_state.cases) + 1:03d}'
                active = {"id": case_id, "source": source, "target": target,
                          "location": row["location"], "severity": severity,
                          "status": "New", "note": "", "timeline": []}
                st.session_state.cases[case_id] = active
            active["severity"] = severity
            active["timeline"].append({"time": row["timestamp"],
                                       "event": f"{severity} alert at update {update}"})


def get_cases():
    return list(st.session_state.get("cases", {}).values())


def latest_case(source, target):
    """Return the newest case for a simulated device or sensor."""
    return next((case for case in reversed(get_cases())
                 if case["source"] == source and case["target"] == target), None)


def is_new_case(source, target):
    case = latest_case(source, target)
    return case is None or case["status"] == "New"


def recover_devices(frame):
    """Apply a demo-only normal reading to resolved device targets."""
    out = frame.copy()
    case = latest_case("Device", "DEV-12")
    if case and case["status"] == "Resolved":
        idx = out.index[out["device_id"] == "DEV-12"]
        if len(idx):
            out.loc[idx[0], ["network_requests", "failed_logins", "cpu_usage", "temperature", "packet_rate", "online"]] = [140, 0, 42, 37, 160, True]
    return out


def recover_environment(frame):
    """Apply demo-only normal readings to resolved environmental targets."""
    out = frame.copy()
    for target in ("ENV-01", "ENV-02"):
        case = latest_case("Environment", target)
        if case and case["status"] == "Resolved":
            idx = out.index[out["sensor_id"] == target]
            if len(idx):
                out.loc[idx[0], ["reading_index", "level"]] = [12, "NORMAL"]
    return out


def change_case(case_id, action, note=""):
    for case in get_cases():
        if case["id"] != case_id:
            continue
        if action == "Acknowledge" and case["status"] == "New":
            case["status"] = "Investigating"
            case["timeline"].append({"time": _now(), "event": "Operator acknowledged alert"})
        elif action == "Resolve" and case["status"] == "Investigating":
            case["status"] = "Resolved"
            case["timeline"].append({"time": _now(), "event": "Operator resolved case; demo recovery will restore simulated readings"})
        else:
            return False
        if note.strip():
            case["note"] = note.strip()[:300]
            case["timeline"].append({"time": _now(), "event": "Operator added a note"})
        return True
    return False


def cases_table():
    return pd.DataFrame([{
        "id": case["id"],
        "priority": "1 · Site safety" if case["source"] == "Environment" and case["severity"] == "EMERGENCY"
                    else "2 · Device security" if case["source"] == "Device" else "3 · Review",
        "category": "Environment" if case["source"] == "Environment" else "Cybersecurity",
        "target": case["target"], "location": case["location"],
        "severity": case["severity"], "status": case["status"],
    } for case in get_cases()])
