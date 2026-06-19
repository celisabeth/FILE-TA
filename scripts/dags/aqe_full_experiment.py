"""
DAG: Eksperimen AQE End-to-End
================================
Menjalankan seluruh alur eksperimen: Medallion + workload Spark/Trino + agregasi metrik.

Trigger manual:
  airflow dags trigger aqe_full_experiment
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


def task_init_experiment_run(**context):
    from benchmark.experiment_run import init_airflow_task

    os.environ["EXPERIMENT_TRACK"] = "aqe"
    path = init_airflow_task(**context)
    logging.info("AQE metrics audit run → %s", path)


def _activate_aqe(context) -> None:
    from benchmark.experiment_run import activate_from_airflow_context

    os.environ["EXPERIMENT_TRACK"] = "aqe"
    activate_from_airflow_context(context, "aqe")


def task_upload_staging(**context):
    _activate_aqe(context)
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


def task_dataset_summary(**context):
    _activate_aqe(context)
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
    _activate_aqe(context)
    from spark.staging_to_bronze import run_staging_to_bronze

    run_staging_to_bronze()


def task_silver_off(**context):
    _activate_aqe(context)
    os.environ["SPARK_AQE_SCENARIO"] = "OFF"
    from spark.bronze_to_silver_aqe import run_bronze_to_silver

    run_bronze_to_silver(aqe_scenario="OFF")


def task_spark_workloads_off(**context):
    _activate_aqe(context)
    from benchmark.run_spark_workloads import run_workloads

    run_workloads("OFF")


def task_gold_off(**context):
    _activate_aqe(context)
    os.environ["SPARK_AQE_SCENARIO"] = "OFF"
    from spark.silver_to_gold_aqe import run_silver_to_gold

    run_silver_to_gold(aqe_context="OFF")


def task_trino_off(**context):
    _activate_aqe(context)
    from benchmark.run_trino_workloads import run_workloads

    run_workloads("OFF")


def task_silver_on(**context):
    _activate_aqe(context)
    os.environ["SPARK_AQE_SCENARIO"] = "ON"
    from spark.bronze_to_silver_aqe import run_bronze_to_silver

    run_bronze_to_silver(aqe_scenario="ON")


def task_spark_workloads_on(**context):
    _activate_aqe(context)
    from benchmark.run_spark_workloads import run_workloads

    run_workloads("ON")


def task_gold_on(**context):
    _activate_aqe(context)
    os.environ["SPARK_AQE_SCENARIO"] = "ON"
    from spark.silver_to_gold_aqe import run_silver_to_gold

    run_silver_to_gold(aqe_context="ON")


def task_trino_on(**context):
    _activate_aqe(context)
    from benchmark.run_trino_workloads import run_workloads

    run_workloads("ON")


def task_aggregate(**context):
    _activate_aqe(context)
    from benchmark.aggregate_results import aggregate
    from benchmark.compare_aqe_runs import compare, print_markdown_table
    from benchmark._common import metrics_dir, utc_now, write_json
    from benchmark.experiment_run import finalize_run, mirror_to_latest_slot

    report = compare()
    print_markdown_table(report)
    summary = aggregate(track="aqe")
    summary["aqe_comparison"] = report
    mdir = metrics_dir()
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    cmp_out = write_json(mdir / f"aqe_comparison_{ts}.json", report, artifact_role="aqe_comparison")
    mirror_to_latest_slot("aqe", cmp_out.name, "aqe_comparison.json")
    sum_out = write_json(mdir / f"experiment_summary_{ts}.json", summary, artifact_role="experiment_summary")
    mirror_to_latest_slot("aqe", sum_out.name, "experiment_summary.json")
    finalize_run(summary_file=sum_out.name, extra={"aqe_comparison_file": cmp_out.name})
    logging.info("AQE experiment summary written to %s", mdir)


with DAG(
    dag_id="aqe_full_experiment",
    description="Eksperimen AQE end-to-end: Medallion + workloads + agregasi metrik",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "aqe", "experiment", "benchmark"],
    params={"experiment_track": "aqe"},
) as dag:

    t_init = PythonOperator(task_id="init_experiment_run", python_callable=task_init_experiment_run)
    t_upload = PythonOperator(task_id="upload_staging_to_minio", python_callable=task_upload_staging)
    t0 = PythonOperator(task_id="dataset_summary", python_callable=task_dataset_summary)
    t1 = PythonOperator(
        task_id="staging_to_bronze",
        python_callable=task_staging_bronze,
        execution_timeout=timedelta(hours=2),
    )
    t2 = PythonOperator(
        task_id="bronze_to_silver_off",
        python_callable=task_silver_off,
        execution_timeout=timedelta(hours=3),
    )
    t3 = PythonOperator(
        task_id="spark_workloads_off",
        python_callable=task_spark_workloads_off,
        execution_timeout=timedelta(hours=1),
    )
    t4 = PythonOperator(
        task_id="silver_to_gold_off",
        python_callable=task_gold_off,
        execution_timeout=timedelta(hours=2),
    )
    t5 = PythonOperator(
        task_id="trino_workloads_off",
        python_callable=task_trino_off,
        execution_timeout=timedelta(minutes=30),
    )
    t6 = PythonOperator(
        task_id="bronze_to_silver_on",
        python_callable=task_silver_on,
        execution_timeout=timedelta(hours=3),
    )
    t7 = PythonOperator(
        task_id="spark_workloads_on",
        python_callable=task_spark_workloads_on,
        execution_timeout=timedelta(hours=1),
    )
    t8 = PythonOperator(
        task_id="silver_to_gold_on",
        python_callable=task_gold_on,
        execution_timeout=timedelta(hours=2),
    )
    t9 = PythonOperator(
        task_id="trino_workloads_on",
        python_callable=task_trino_on,
        execution_timeout=timedelta(minutes=30),
    )
    t10 = PythonOperator(task_id="aggregate_results", python_callable=task_aggregate)

    t_init >> t_upload >> t0 >> t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7 >> t8 >> t9 >> t10
