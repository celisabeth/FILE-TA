#!/usr/bin/env python3
"""Registrasi metadata model MLOps ke Atlas (AI Metadata Gold)."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("atlas.ml_model")

ATLAS_URL = os.environ.get("ATLAS_URL", "http://atlas:21000")


def register_models(training_result: dict | None = None) -> bool:
    """Placeholder — lengkapi typedef ml_model di Atlas saat produksi."""
    logger.info("Atlas model metadata registration (stub) @ %s", ATLAS_URL)
    if training_result:
        for m in training_result.get("models", []):
            logger.info("  model: %s", m.get("model"))
    return True
