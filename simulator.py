import numpy as np
import pandas as pd
from datetime import datetime

DEVICE_TYPES = ["CCTV Camera", "Traffic Sensor", "Air Sensor", "Access Control", "Smart Light", "Gas Sensor"]
LOCATIONS = ["Main Gate", "Block A", "Block B", "Parking", "Lab Wing", "Cafeteria", "Library", "Road Junction"]

def generate_devices(n=28, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(1, n + 1):
        dtype = rng.choice(DEVICE_TYPES)
        rows.append({
            "device_id": f"DEV-{i:02d}",
            "device_type": dtype,
            "location": rng.choice(LOCATIONS),
            "network_requests": int(rng.normal(140, 35)),
            "failed_logins": int(max(0, rng.poisson(1))),
            "cpu_usage": float(np.clip(rng.normal(42, 15), 5, 95)),
            "temperature": float(np.clip(rng.normal(37, 6), 18, 75)),
            "packet_rate": int(max(20, rng.normal(160, 45))),
            "online": bool(rng.random() > 0.08),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return pd.DataFrame(rows)

def inject_demo_incident(df, device_id="DEV-12"):
    df = df.copy()
    idx = df.index[df["device_id"] == device_id]
    if len(idx):
        i = idx[0]
        df.loc[i, ["network_requests","failed_logins","cpu_usage","packet_rate"]] = [8200, 34, 96, 7900]
    return df


def generate_tick(n=28, seed=42, tick=0, incident=False):
    """Deterministic next snapshot; DEV-12 escalates over four ticks."""
    df = generate_devices(n, seed + tick)
    # Device identity and location stay fixed while readings change.
    fixed = generate_devices(n, seed).set_index("device_id")
    df["device_type"] = df["device_id"].map(fixed["device_type"])
    df["location"] = df["device_id"].map(fixed["location"])
    if incident:
        idx = df.index[df["device_id"] == "DEV-12"]
        if len(idx):
            stage = min(tick, 4)
            i = idx[0]
            requests = [140, 240, 700, 2400, 8200]
            logins = [0, 1, 3, 9, 34]
            cpu = [42, 50, 65, 82, 96]
            packets = [160, 230, 600, 2200, 7900]
            df.loc[i, ["network_requests", "failed_logins", "cpu_usage", "packet_rate", "online"]] = [
                requests[stage], logins[stage], cpu[stage], packets[stage], True,
            ]
    return df
