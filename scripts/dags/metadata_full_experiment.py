"""
DAG: Eksperimen Metadata End-to-End
====================================
Medallion + registrasi Atlas + UMT + evaluasi kualitas metadata + agregasi metrik.

Trigger manual:
  airflow dags trigger metadata_full_experiment
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/scripts")

default_args = {
    "owner": "data-engineering",
    "retries": 0,
    "email_on_failure": False,
}

STAGING_DIR = "/opt/airflow/data/staging"
MINIO_ENDPOINT = "http://minio:9000"
ATLAS_URL = "http://atlas:21000"
ATLAS_AUTH = ("admin", "admin")


def task_upload_staging(**_context):
    import boto3
    from botocore.client import Config

    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin123",
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    staging = Path(STAGING_DIR)
    if not staging.is_dir():
        raise FileNotFoundError(f"Staging not found: {staging}")
    n = 0
    for fname in sorted(staging.glob("*.csv")):
        s3.upload_file(str(fname), "staging", fname.name)
        n += 1
        logging.info("Uploaded staging/%s", fname.name)
    logging.info("Uploaded %d CSV files to MinIO", n)


def task_dataset_summary(**_context):
    from benchmark.dataset_summary import summarize_staging
    from benchmark._common import metrics_dir, utc_now, write_json

    staging = Path(STAGING_DIR)
    if not staging.is_dir() or not any(staging.glob("*.csv")):
        logging.warning("No staging CSV — skip dataset summary")
        return
    payload = summarize_staging(staging)
    out = metrics_dir() / f"dataset_summary_{utc_now().strftime('%Y%m%d_%H%M%S')}.json"
    write_json(out, payload)
    logging.info("Dataset summary → %s", out)


def task_staging_bronze(**context):
    from spark.staging_to_bronze import run_staging_to_bronze

    profiling = run_staging_to_bronze()
    context["ti"].xcom_push(key="bronze_profiling", value=profiling)
    return len(profiling)


def task_register_bronze(**context):
    from atlas.register_bronze_metadata import register_all_metadata
    from benchmark.atlas_registration_snapshot import write_registration_snapshot

    profiling = context["ti"].xcom_pull(task_ids="staging_to_bronze", key="bronze_profiling")
    if not profiling:
        raise ValueError("No bronze profiling from staging_to_bronze")
    register_all_metadata(
        profiling_results=profiling,
        atlas_url=ATLAS_URL,
        atlas_user=ATLAS_AUTH[0],
        atlas_pass=ATLAS_AUTH[1],
    )
    path = write_registration_snapshot("bronze")
    logging.info("Bronze Atlas snapshot → %s", path)


def task_bronze_silver(**context):
    from spark.bronze_to_silver import run_bronze_to_silver

    profiling = run_bronze_to_silver()
    context["ti"].xcom_push(key="silver_profiling", value=profiling)
    return sum(1 for r in profiling.values() if r.get("written"))


def task_register_silver(**context):
    from atlas.register_silver_metadata import register_all_silver_metadata
    from benchmark.atlas_registration_snapshot import write_registration_snapshot

    profiling = context["ti"].xcom_pull(task_ids="bronze_to_silver", key="silver_profiling")
    if not profiling:
        raise ValueError("No silver profiling from bronze_to_silver")
    register_all_silver_metadata(
        profiling_results=profiling,
        atlas_url=ATLAS_URL,
        atlas_user=ATLAS_AUTH[0],
        atlas_pass=ATLAS_AUTH[1],
    )
    path = write_registration_snapshot("silver")
    logging.info("Silver Atlas snapshot → %s", path)


def task_silver_gold(**context):
    from spark.silver_to_gold import run_silver_to_gold

    profiling = run_silver_to_gold()
    context["ti"].xcom_push(key="gold_profiling", value=profiling)
    return sum(1 for r in profiling.values() if r.get("written"))


def task_register_gold(**context):
    from atlas.register_gold_metadata import register_all_gold_metadata
    from benchmark.atlas_registration_snapshot import write_registration_snapshot

    profiling = context["ti"].xcom_pull(task_ids="silver_to_gold", key="gold_profiling")
    if not profiling:
        raise ValueError("No gold profiling from silver_to_gold")
    register_all_gold_metadata(
        profiling_results=profiling,
        atlas_url=ATLAS_URL,
        atlas_user=ATLAS_AUTH[0],
        atlas_pass=ATLAS_AUTH[1],
    )
    path = write_registration_snapshot("gold")
    logging.info("Gold Atlas snapshot → %s", path)


def task_collect_umt(**_context):
    from benchmark.collect_umt import collect_umt
    from benchmark._common import metrics_dir, utc_now, write_json

    payload = collect_umt()
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    write_json(metrics_dir() / f"umt_{ts}.json", payload)
    write_json(metrics_dir() / "umt_latest.json", payload)
    logging.info("UMT rows: %d", len(payload.get("rows", [])))


def task_metadata_quality(**_context):
    from benchmark.atlas_quality import evaluate_metadata_quality
    from benchmark._common import metrics_dir, utc_now, write_json

    report = evaluate_metadata_quality()
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    write_json(metrics_dir() / f"metadata_quality_{ts}.json", report)
    write_json(metrics_dir() / "metadata_quality_latest.json", report)
    for layer in report.get("layers", []):
        logging.info(
            "Quality %s: completeness=%s%% consistency=%s%%",
            layer.get("label"),
            layer.get("completeness"),
            layer.get("consistency"),
        )


def task_atlas_inventory(**_context):
    from benchmark.atlas_inventory import collect_inventory
    from benchmark._common import metrics_dir, utc_now, write_json

    payload = collect_inventory()
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    write_json(metrics_dir() / f"atlas_inventory_{ts}.json", payload)
    write_json(metrics_dir() / "atlas_inventory_latest.json", payload)


def task_aggregate(**_context):
    from benchmark.aggregate_results import aggregate
    from benchmark._common import metrics_dir, utc_now, write_json

    summary = aggregate()
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    mdir = metrics_dir()
    write_json(mdir / f"experiment_summary_{ts}.json", summary)
    write_json(mdir / "experiment_summary_latest.json", summary)
    logging.info("Experiment summary written to %s", mdir)


with DAG(
    dag_id="metadata_full_experiment",
    description="Eksperimen metadata E2E: Medallion + Atlas + UMT + kualitas + agregasi metrik",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "metadata", "atlas", "experiment", "catalog"],
) as dag:

    t_upload = PythonOperator(task_id="upload_staging_to_minio", python_callable=task_upload_staging)
    t0 = PythonOperator(task_id="dataset_summary", python_callable=task_dataset_summary)
    t1 = PythonOperator(
        task_id="staging_to_bronze",
        python_callable=task_staging_bronze,
        execution_timeout=timedelta(hours=2),
    )
    t1b = PythonOperator(task_id="register_bronze_atlas", python_callable=task_register_bronze)
    t2 = PythonOperator(
        task_id="bronze_to_silver",
        python_callable=task_bronze_silver,
        execution_timeout=timedelta(hours=3),
    )
    t2b = PythonOperator(task_id="register_silver_atlas", python_callable=task_register_silver)
    t3 = PythonOperator(
        task_id="silver_to_gold",
        python_callable=task_silver_gold,
        execution_timeout=timedelta(hours=2),
    )
    t3b = PythonOperator(task_id="register_gold_atlas", python_callable=task_register_gold)
    t4 = PythonOperator(task_id="collect_umt", python_callable=task_collect_umt)
    t5 = PythonOperator(task_id="evaluate_metadata_quality", python_callable=task_metadata_quality)
    t6 = PythonOperator(task_id="atlas_inventory", python_callable=task_atlas_inventory)
    t7 = PythonOperator(task_id="aggregate_results", python_callable=task_aggregate)

    t_upload >> t0 >> t1 >> t1b >> t2 >> t2b >> t3 >> t3b >> t4 >> t5 >> t6 >> t7
