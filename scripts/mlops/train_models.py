#!/usr/bin/env python3
"""
Training ringkas empat use case MLOps (scaffold penelitian).

Model: Risk (sklearn), Forecast/Opportunity/Anomaly (placeholder metrics).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("mlops.train")

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")


def _train_risk_score() -> dict:
    import mlflow
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("risk_score_prodi")

    df = pd.DataFrame({
        "ipk": [3.2, 2.8, 3.5, 2.1, 3.0],
        "lama_studi": [4, 5, 4, 6, 4],
        "label": [1, 0, 1, 0, 1],
    })
    X = df[["ipk", "lama_studi"]]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    with mlflow.start_run(run_name="risk_score_prodi"):
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        acc = float(model.score(X_test, y_test))
        mlflow.log_param("n_estimators", 50)
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(model, "model")
        run_id = mlflow.active_run().info.run_id
    return {"model": "risk_score_prodi", "run_id": run_id, "accuracy": acc}


def run_training() -> dict:
    results = {"trained_at": datetime.now(timezone.utc).isoformat(), "models": []}
    try:
        results["models"].append(_train_risk_score())
    except Exception as exc:
        logger.warning("Risk model training skipped: %s", exc)
        results["models"].append({"model": "risk_score_prodi", "error": str(exc)})

    for name in ("forecast_iku", "opportunity_prodi", "anomaly_iku"):
        results["models"].append({
            "model": name,
            "status": "placeholder",
            "note": "Lengkapi dengan Prophet / KMeans / PyOD saat data Gold penuh",
        })
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_training())
