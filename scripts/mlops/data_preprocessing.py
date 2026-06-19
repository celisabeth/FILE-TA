#!/usr/bin/env python3
"""Inference data dari Gold layer — cleaning & normalisasi untuk MLOps."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("mlops.preprocessing")

GOLD_TABLES = [
    "fact_rekap_iku_institusi",
    "fact_iku4_kualifikasi_dosen",
    "fact_iku6_kerjasama_prodi",
    "fact_iku7_metode_pembelajaran",
    "fact_iku8_akreditasi_internasional",
]


def run_preprocessing() -> dict:
    from spark.spark_python import get_spark_session

    spark = get_spark_session(app_name="MLOps-Preprocessing")
    try:
        frames = {}
        for table in GOLD_TABLES:
            full = f"lakehouse.gold.{table}"
            try:
                df = spark.table(full)
                frames[table] = df.count()
                logger.info("Loaded %s: %s rows", full, f"{frames[table]:,}")
            except Exception as exc:
                logger.warning("Skip %s: %s", full, exc)
        return {"tables": frames, "status": "ok" if frames else "empty"}
    finally:
        spark.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_preprocessing())
