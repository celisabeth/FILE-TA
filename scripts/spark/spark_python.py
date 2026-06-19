"""PySpark helpers: session factory, Python version alignment, cluster resource limits."""

from __future__ import annotations

import glob
import logging
import os
import socket

from pyspark.sql import SparkSession

from spark.lakehouse_catalog import configure_spark_catalog

logger = logging.getLogger("spark_python")


def apply_pyspark_python_configs(builder):
    """Spark workers (apache/spark image) use Python 3.10; driver must match."""
    py = os.environ.get("PYSPARK_PYTHON", "python3")
    driver_py = os.environ.get("PYSPARK_DRIVER_PYTHON", py)
    scripts_path = os.environ.get("PYTHONPATH", "/opt/airflow/scripts")
    return (
        builder.config("spark.pyspark.python", py)
        .config("spark.pyspark.driver.python", driver_py)
        .config("spark.executorEnv.PYSPARK_PYTHON", py)
        .config("spark.executorEnv.PYTHONPATH", scripts_path)
    )


def apply_cluster_resource_configs(builder, *, app_name: str = "lakehouse"):
    """
    Workers in compose are 2G RAM / 2 cores each.
    Default Spark would spawn 4x1G executors → OOM (exit 137) on workers.
    """
    instances = os.environ.get("SPARK_EXECUTOR_INSTANCES", "2")
    executor_mem = os.environ.get("SPARK_EXECUTOR_MEMORY", "1400m")
    driver_mem = os.environ.get("SPARK_DRIVER_MEMORY", "1536m")

    return (
        builder.config("spark.dynamicAllocation.enabled", "false")
        .config("spark.executor.instances", instances)
        .config("spark.executor.cores", "1")
        .config("spark.executor.memory", executor_mem)
        .config("spark.driver.memory", driver_mem)
        .config("spark.cores.max", str(int(instances) * 1))
        .config("spark.sql.shuffle.partitions", os.environ.get("SPARK_SHUFFLE_PARTITIONS", "8"))
        .config("spark.ui.showConsoleProgress", "true")
    )


def _resolve_jars() -> str:
    jars_dir = os.environ.get("SPARK_JARS_DIR", "/opt/spark-jars")
    jars = glob.glob(os.path.join(jars_dir, "*.jar"))
    if jars:
        logger.info("Using pre-downloaded JARs from %s (%d files)", jars_dir, len(jars))
        return ",".join(sorted(jars))
    return ""


def _resolve_spark_master() -> str:
    spark_master = os.environ.get("SPARK_MASTER", "spark://spark-master:7077")
    try:
        sock = socket.create_connection(("spark-master", 7077), timeout=5)
        sock.close()
        logger.info("Spark master reachable at %s", spark_master)
        return spark_master
    except (OSError, socket.timeout):
        fallback = "local[*]"
        logger.warning("Spark master unreachable — falling back to %s", fallback)
        return fallback


def get_spark_session(
    app_name: str = "lakehouse-mlops",
    *,
    aqe_scenario: str | None = None,
) -> SparkSession:
    """
    SparkSession bersama untuk DAG MLOps dan skrip lain yang butuh katalog Iceberg.

    Args:
        app_name: Nama aplikasi Spark (mis. MLOps-Preprocessing).
        aqe_scenario: Opsional — diteruskan ke configure_spark_catalog untuk run AQE.
    """
    spark_master = _resolve_spark_master()

    builder = configure_spark_catalog(
        SparkSession.builder.appName(app_name).master(spark_master),
        aqe_scenario,
    )

    local_jars = _resolve_jars()
    if local_jars:
        builder = builder.config("spark.jars", local_jars)
    else:
        builder = builder.config(
            "spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262",
        )

    builder = apply_cluster_resource_configs(builder, app_name=app_name)
    return apply_pyspark_python_configs(builder).getOrCreate()
