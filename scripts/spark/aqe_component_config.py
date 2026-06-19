"""
Profil konfigurasi Spark untuk pengukuran efektivitas komponen AQE (BAB IV §4.1.4).

Komponen:
  - DPP  : spark.sql.optimizer.dynamicPartitionPruning.enabled
  - COALESCE : spark.sql.adaptive.coalescePartitions.enabled
  - SKEW : spark.sql.adaptive.skewJoin.enabled
  - LOCAL_SHUFFLE : spark.sql.adaptive.localShuffleReader.enabled (sering berpasangan DPP)

Profil OFF = baseline; ON_FULL = semua aktif (selaras aqe_config ON).
"""

from __future__ import annotations

import os

from spark.aqe_config import _shuffle_partitions, aqe_spark_configs, resolve_aqe_scenario

COMPONENT_PROFILES = (
    "OFF",
    "ON_FULL",
    "ON_COALESCE_ONLY",
    "ON_SKEW_ONLY",
    "ON_DPP_ONLY",
    "ON_LOCAL_SHUFFLE_ONLY",
)


def _base_off() -> dict[str, str]:
    return dict(aqe_spark_configs("OFF"))


def _base_on_partial(**flags: bool) -> dict[str, str]:
    """AQE adaptif ON dengan komponen tertentu; DPP terpisah di optimizer."""
    shuffle = _shuffle_partitions()
    adaptive = flags.get("adaptive", True)
    coalesce = flags.get("coalesce", False)
    skew = flags.get("skew", False)
    local_reader = flags.get("local_shuffle", False)
    dpp = flags.get("dpp", False)

    cfg: dict[str, str] = {
        "spark.sql.adaptive.enabled": "true" if adaptive else "false",
        "spark.sql.adaptive.coalescePartitions.enabled": "true" if coalesce else "false",
        "spark.sql.adaptive.skewJoin.enabled": "true" if skew else "false",
        "spark.sql.adaptive.localShuffleReader.enabled": "true" if local_reader else "false",
        "spark.sql.adaptive.optimizeSkewsInRebalancePartitions.enabled": "true" if skew else "false",
        "spark.sql.optimizer.dynamicPartitionPruning.enabled": "true" if dpp else "false",
        "spark.sql.shuffle.partitions": shuffle,
    }
    if adaptive and coalesce:
        cfg["spark.sql.adaptive.advisoryPartitionSizeInBytes"] = os.environ.get(
            "SPARK_AQE_ADVISORY_PARTITION_SIZE", "64MB"
        )
        cfg["spark.sql.adaptive.coalescePartitions.minPartitionSize"] = os.environ.get(
            "SPARK_AQE_MIN_PARTITION_SIZE", "1MB"
        )
    if adaptive and skew:
        cfg["spark.sql.adaptive.skewJoin.skewedPartitionFactor"] = os.environ.get(
            "SPARK_AQE_SKEW_PARTITION_FACTOR", "5"
        )
        cfg["spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes"] = os.environ.get(
            "SPARK_AQE_SKEW_THRESHOLD", "256MB"
        )
    return cfg


def spark_configs_for_profile(profile: str, base_scenario: str | None = None) -> dict[str, str]:
    """Map nama profil → konfigurasi Spark."""
    name = profile.strip().upper()
    if name == "OFF":
        return _base_off()
    if name == "ON_FULL":
        on = dict(aqe_spark_configs("ON"))
        on["spark.sql.optimizer.dynamicPartitionPruning.enabled"] = "true"
        return on
    if name == "ON_COALESCE_ONLY":
        return _base_on_partial(adaptive=True, coalesce=True, skew=False, local_shuffle=False, dpp=False)
    if name == "ON_SKEW_ONLY":
        return _base_on_partial(adaptive=True, coalesce=False, skew=True, local_shuffle=False, dpp=False)
    if name == "ON_DPP_ONLY":
        off = _base_off()
        off["spark.sql.optimizer.dynamicPartitionPruning.enabled"] = "true"
        return off
    if name == "ON_LOCAL_SHUFFLE_ONLY":
        return _base_on_partial(adaptive=True, coalesce=False, skew=False, local_shuffle=True, dpp=False)

    # Alias skenario eksperimen OFF/ON
    sc = resolve_aqe_scenario(base_scenario or name)
    if sc == "ON":
        return spark_configs_for_profile("ON_FULL")
    return spark_configs_for_profile("OFF")


def profile_component_labels(profile: str) -> dict[str, str]:
    """Label komponen aktif (untuk JSON laporan)."""
    cfg = spark_configs_for_profile(profile)
    return {
        "profile": profile.upper(),
        "adaptive_enabled": cfg.get("spark.sql.adaptive.enabled", "?"),
        "coalesce_partitions": cfg.get("spark.sql.adaptive.coalescePartitions.enabled", "?"),
        "skew_join": cfg.get("spark.sql.adaptive.skewJoin.enabled", "?"),
        "local_shuffle_reader": cfg.get("spark.sql.adaptive.localShuffleReader.enabled", "?"),
        "dynamic_partition_pruning": cfg.get("spark.sql.optimizer.dynamicPartitionPruning.enabled", "?"),
    }
