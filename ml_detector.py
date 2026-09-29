"""Anomaly detector trained on reproducible synthetic normal telemetry."""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = ["network_requests", "failed_logins", "cpu_usage", "temperature", "packet_rate"]


def fit_baseline(seed=42):
    rng = np.random.default_rng(seed)
    count = 1200
    normal = pd.DataFrame({
        "network_requests": np.clip(rng.normal(140, 35, count), 20, 350),
        "failed_logins": rng.poisson(1, count),
        "cpu_usage": np.clip(rng.normal(42, 15, count), 5, 95),
        "temperature": np.clip(rng.normal(37, 6, count), 18, 75),
        "packet_rate": np.clip(rng.normal(160, 45, count), 20, 400),
    })
    # Log transformation prevents one large network number from dominating.
    model = IsolationForest(n_estimators=100, contamination=0.02, random_state=seed)
    model.fit(_transform(normal))
    return model


def _transform(frame):
    values = frame[FEATURES].astype(float).copy()
    for col in ("network_requests", "packet_rate"):
        values[col] = np.log1p(values[col].clip(lower=0))
    return values


def detect(frame, model):
    out = frame.copy()
    out["ml_anomaly"] = model.predict(_transform(out)) == -1
    out["ml_score"] = (-model.decision_function(_transform(out))).round(3)
    return out
