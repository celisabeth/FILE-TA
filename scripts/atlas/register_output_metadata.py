#!/usr/bin/env python3
"""Registrasi lineage Output Tables MLOps → Atlas."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("atlas.ml_output")

ATLAS_URL = os.environ.get("ATLAS_URL", "http://atlas:21000")


def register_outputs(inference_result: dict | None = None) -> bool:
    logger.info("Atlas MLOps output metadata (stub) @ %s", ATLAS_URL)
    if inference_result:
        logger.info("  output table: %s", inference_result.get("table"))
    return True
