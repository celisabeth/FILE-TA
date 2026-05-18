"""
DAG: MLOps Pipeline — Gold → Preprocessing → Features → Training → Inference → Atlas
"""

import logging
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/scripts")

default_args = {
    "owner": "data-engineering",
    "retries": 0,
    "email_on_failure": False,
}


def task_preprocess(**_):
    from mlops.data_preprocessing import run_preprocessing
    return run_preprocessing()


def task_features(**_):
    from mlops.feature_engineering import run_feature_engineering
    return run_feature_engineering()


def task_train(**_):
    from mlops.train_models import run_training
    result = run_training()
    from atlas.register_model_metadata import register_models
    register_models(result)
    return result


def task_inference(**_):
    from mlops.inference_batch import run_inference
    result = run_inference()
    from atlas.register_output_metadata import register_outputs
    register_outputs(result)
    return result


def task_export_metrics(**context):
    """Tulis metrics/mlops_metrics_latest.json untuk Grafana via metrics-exporter."""
    from benchmark.mlops_metrics import export_mlops_metrics

    ti = context["ti"]
    preprocess = ti.xcom_pull(task_ids="data_preprocessing")
    features = ti.xcom_pull(task_ids="feature_engineering")
    train = ti.xcom_pull(task_ids="train_models")
    inference = ti.xcom_pull(task_ids="inference_batch")

    task_durations: dict[str, float] = {}
    dag_run = context.get("dag_run")
    if dag_run:
        for tid in ("data_preprocessing", "feature_engineering", "train_models", "inference_batch"):
            inst = dag_run.get_task_instance(tid)
            if inst and inst.duration is not None:
                task_durations[tid] = float(inst.duration)

    out = export_mlops_metrics(
        preprocess=preprocess,
        features=features,
        train=train,
        inference=inference,
        task_durations=task_durations or None,
    )
    return str(out)


with DAG(
    dag_id="mlops_pipeline",
    description="MLOps: Forecast, Risk Score, Opportunity, Anomaly — Gold → Output Tables → Atlas",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["lakehouse", "mlops", "insight"],
) as dag:
    t1 = PythonOperator(task_id="data_preprocessing", python_callable=task_preprocess)
    t2 = PythonOperator(task_id="feature_engineering", python_callable=task_features, execution_timeout=timedelta(hours=2))
    t3 = PythonOperator(task_id="train_models", python_callable=task_train, execution_timeout=timedelta(hours=1))
    t4 = PythonOperator(task_id="inference_batch", python_callable=task_inference, execution_timeout=timedelta(hours=1))
    t5 = PythonOperator(task_id="export_mlops_metrics", python_callable=task_export_metrics)
    t1 >> t2 >> t3 >> t4 >> t5
