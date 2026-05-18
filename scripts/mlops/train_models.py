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


def _mlflow_reachable(uri: str | None = None, timeout_sec: float = 3.0) -> bool:
    """Cek cepat — hindari retry panjang MLflow client jika container mati."""
    target = (uri or MLFLOW_URI).rstrip("/")
    try:
        import urllib.error
        import urllib.request

        req = urllib.request.Request(f"{target}/health", method="GET")
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return resp.status < 500
    except Exception:
        return False


def _train_risk_score() -> dict:
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    df = pd.DataFrame({
        "ipk": [3.2, 2.8, 3.5, 2.1, 3.0],
        "lama_studi": [4, 5, 4, 6, 4],
        "label": [1, 0, 1, 0, 1],
    })
    X = df[["ipk", "lama_studi"]]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    acc = float(model.score(X_test, y_test))

    result: dict = {"model": "risk_score_prodi", "run_id": None, "accuracy": acc}

    if not _mlflow_reachable():
        logger.warning(
            "MLflow tidak terjangkau di %s — latih model lokal tanpa registry. "
            "Jalankan: docker compose up -d mlflow",
            MLFLOW_URI,
        )
        result["mlflow"] = "skipped_unreachable"
        return result

    os.environ.setdefault("MLFLOW_HTTP_REQUEST_MAX_RETRIES", "2")
    os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", "10")

    import mlflow

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("risk_score_prodi")

    with mlflow.start_run(run_name="risk_score_prodi"):
        mlflow.log_param("n_estimators", 50)
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(model, "model")
        result["run_id"] = mlflow.active_run().info.run_id
        result["mlflow"] = "logged"
    return result


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
