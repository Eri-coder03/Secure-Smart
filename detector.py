import numpy as np
import pandas as pd

FEATURES = ["network_requests", "failed_logins", "cpu_usage", "temperature", "packet_rate"]

def score_row(row):
    # Transparent, demo-friendly risk scoring. This detects anomalies; it does not perform attacks.
    score = 0
    score += min(30, row["network_requests"] / 300 * 10)
    score += min(25, row["failed_logins"] * 3)
    score += max(0, (row["cpu_usage"] - 65) * 0.7)
    score += min(25, row["packet_rate"] / 350 * 10)
    if not bool(row["online"]):
        score += 18
    if row["temperature"] > 60:
        score += 15
    return int(np.clip(score, 0, 100))

def classify(score):
    if score >= 70:
        return "CRITICAL"
    if score >= 45:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"

def analyze(df):
    out = df.copy()
    out["risk_score"] = out.apply(score_row, axis=1)
    if "ml_anomaly" in out:
        # ML is corroborating evidence. Transparent rules retain final severity.
        out.loc[out["ml_anomaly"] & (out["risk_score"] >= 25), "risk_score"] += 10
        out["risk_score"] = out["risk_score"].clip(upper=100)
    out["severity"] = out["risk_score"].apply(classify)
    out["status"] = out["severity"].map({
        "LOW": "Normal", "MEDIUM": "Suspicious", "HIGH": "Suspicious", "CRITICAL": "Attack suspected"
    })
    return out

def recommendation(row):
    if row["severity"] == "CRITICAL":
        return "Isolate the device in the demo environment, preserve logs, notify the administrator, and investigate related telemetry."
    if row["severity"] == "HIGH":
        return "Review recent telemetry and authentication events, verify the device owner, and increase monitoring."
    if row["severity"] == "MEDIUM":
        return "Watch the device closely and compare its behavior with its normal baseline."
    return "No action required. Continue normal monitoring."
