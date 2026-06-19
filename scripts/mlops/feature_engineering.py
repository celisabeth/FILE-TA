#!/usr/bin/env python3
"""Feature engineering dari Gold — output ke s3a://mlops/features/."""

from __future__ import annotations

import logging

logger = logging.getLogger("mlops.features")

FEATURE_PATH = "s3a://mlops/features/iku_features"


def run_feature_engineering() -> dict:
    from pyspark.sql import functions as F
    from spark.spark_python import get_spark_session

    spark = get_spark_session(app_name="MLOps-Features")
    try:
        rekap = spark.table("lakehouse.gold.fact_rekap_iku_institusi")
        waktu = spark.table("lakehouse.gold.dim_waktu")
        features = (
            rekap.join(waktu, "waktu_id", "inner")
            .select(
                waktu["tahun"],
                F.col("iku_kode").alias("iku_code"),
                F.col("nilai_capaian").alias("nilai_capaian"),
                F.col("nilai_target").alias("nilai_target"),
            )
            .dropna()
        )
        n = features.count()
        features.write.mode("overwrite").parquet(FEATURE_PATH)
        logger.info("Features written → %s (%s rows)", FEATURE_PATH, n)
        return {"path": FEATURE_PATH, "row_count": n}
    except Exception as exc:
        logger.error("Feature engineering failed: %s", exc)
        return {"path": FEATURE_PATH, "row_count": 0, "error": str(exc)}
    finally:
        spark.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_feature_engineering())
