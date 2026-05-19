#!/usr/bin/env python3
"""
HTTP exporter Prometheus dari metrics/*.json — AQE, Metadata, MLOps, Dashboard Insight.
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from benchmark._common import find_latest_metric_file, metrics_dir


def _escape_label(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _metric_line(name: str, value: float, labels: dict | None = None) -> str:
    if labels:
        lbl = ",".join(f'{k}="{_escape_label(str(v))}"' for k, v in labels.items())
        return f"{name}{{{lbl}}} {value}\n"
    return f"{name} {value}\n"


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _export_aqe_metrics(lines: list[str], root: Path) -> None:
    latest = find_latest_metric_file(root, "experiment_summary.json")
    if latest is None:
        latest = find_latest_metric_file(root, "experiment_summary_*.json")
    if latest is None:
        latest = root / "experiment_summary_latest.json"
    if latest and latest.is_file():
        try:
            summary = json.loads(latest.read_text(encoding="utf-8"))
            cmp_ = summary.get("aqe_comparison", {})
            sp = cmp_.get("silver_pipeline", {})
            speedup = sp.get("speedup_pct")
            if speedup is not None:
                lines.append(_metric_line("lakehouse_aqe_silver_speedup_percent", float(speedup)))
            for side, key in (("off", "off"), ("on", "on")):
                block = sp.get(side) or {}
                dur = block.get("duration_sec")
                if dur is not None:
                    lines.append(
                        _metric_line(
                            "lakehouse_pipeline_duration_seconds",
                            float(dur),
                            {"pipeline": "bronze_to_silver", "aqe_scenario": side.upper()},
                        )
                    )
        except (json.JSONDecodeError, OSError):
            pass

    for pattern, pipeline, label_key in (
        ("staging_to_bronze_*.json", "staging_to_bronze", None),
        ("bronze_to_silver_aqe_OFF_*.json", "bronze_to_silver", "OFF"),
        ("bronze_to_silver_aqe_ON_*.json", "bronze_to_silver", "ON"),
        ("silver_to_gold_*.json", "silver_to_gold", None),
    ):
        path = find_latest_metric_file(root, pattern)
        if not path:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            dur = data.get("duration_sec")
            if dur is None:
                continue
            labels = {"pipeline": pipeline}
            if label_key:
                labels["aqe_scenario"] = label_key
            elif data.get("aqe_scenario"):
                labels["aqe_scenario"] = str(data["aqe_scenario"])
            lines.append(_metric_line("lakehouse_pipeline_duration_seconds", float(dur), labels))
        except (json.JSONDecodeError, OSError):
            continue

    for pattern, engine in (
        ("workloads_spark_aqe_OFF_*.json", "spark"),
        ("workloads_spark_aqe_ON_*.json", "spark"),
        ("workloads_trino_ctx_OFF_*.json", "trino"),
        ("workloads_trino_ctx_ON_*.json", "trino"),
    ):
        path = find_latest_metric_file(root, pattern)
        if not path:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            scenario = str(
                data.get("aqe_scenario") or data.get("aqe_context_silver") or "unknown"
            ).upper()
            for wid, wl in (data.get("workloads") or {}).items():
                dur = wl.get("duration_sec")
                if dur is None:
                    continue
                lines.append(
                    _metric_line(
                        "lakehouse_workload_duration_seconds",
                        float(dur),
                        {
                            "workload_id": wid,
                            "engine": engine,
                            "aqe_scenario": scenario,
                            "workload_type": wl.get("workload_type", "unknown"),
                        },
                    )
                )
        except (json.JSONDecodeError, OSError):
            continue


def _export_mlops_metrics(lines: list[str], root: Path) -> None:
    mlops_path = find_latest_metric_file(root, "mlops_metrics.json")
    if mlops_path is None:
        mlops_path = find_latest_metric_file(root, "mlops_metrics_latest.json")
    if mlops_path is None:
        mlops_path = root / "mlops_metrics_latest.json"
    if not mlops_path.is_file():
        return
    try:
        data = json.loads(mlops_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    for task, dur in (data.get("pipeline_tasks") or {}).items():
        if dur is not None:
            lines.append(
                _metric_line(
                    "lakehouse_mlops_task_duration_seconds",
                    float(dur),
                    {"task": str(task)},
                )
            )

    for model in data.get("training", {}).get("models", []):
        name = model.get("model", "unknown")
        for key, val in model.items():
            if key in ("model", "run_id", "status", "note", "error"):
                continue
            if isinstance(val, (int, float)):
                lines.append(
                    _metric_line(
                        "lakehouse_mlops_model_metric",
                        float(val),
                        {"model": name, "metric": key},
                    )
                )

    insight = data.get("dashboard_insight") or {}

    for point in insight.get("forecast", {}).get("series", []):
        tahun = point.get("tahun")
        if point.get("actual") is not None:
            lines.append(
                _metric_line(
                    "lakehouse_insight_forecast",
                    float(point["actual"]),
                    {"tahun": str(tahun), "series": "actual"},
                )
            )
        if point.get("forecast") is not None:
            lines.append(
                _metric_line(
                    "lakehouse_insight_forecast",
                    float(point["forecast"]),
                    {"tahun": str(tahun), "series": "forecast"},
                )
            )

    for row in insight.get("risk_score", {}).get("by_prodi", []):
        score = row.get("risk_score")
        if score is not None:
            lines.append(
                _metric_line(
                    "lakehouse_insight_risk_score",
                    float(score),
                    {"prodi_id": str(row.get("prodi_id", "unknown"))},
                )
            )

    for row in insight.get("opportunity", {}).get("by_prodi", []):
        score = row.get("opportunity_score")
        if score is not None:
            lines.append(
                _metric_line(
                    "lakehouse_insight_opportunity_score",
                    float(score),
                    {
                        "prodi_id": str(row.get("prodi_id", "unknown")),
                        "cluster": str(row.get("cluster", "unknown")),
                    },
                )
            )

    anomaly = insight.get("anomaly") or {}
    if anomaly.get("anomaly_count") is not None:
        lines.append(
            _metric_line("lakehouse_insight_anomaly_count", float(anomaly["anomaly_count"]))
        )
    if anomaly.get("anomaly_rate_pct") is not None:
        lines.append(
            _metric_line("lakehouse_insight_anomaly_rate_percent", float(anomaly["anomaly_rate_pct"]))
        )
    for i, sample in enumerate(anomaly.get("samples") or []):
        if sample.get("flag"):
            lines.append(
                _metric_line(
                    "lakehouse_insight_anomaly_flag",
                    float(sample.get("value", 1)),
                    {
                        "entity": str(sample.get("entity", f"sample_{i}")),
                        "tahun": str(sample.get("tahun", "")),
                    },
                )
            )


def _metrics_search_root(mdir: Path) -> Path:
    if (mdir / "runs").is_dir() or (mdir / "latest").is_dir():
        return mdir
    try:
        from benchmark.experiment_run import root_metrics_dir

        return root_metrics_dir()
    except Exception:
        return mdir


def build_prometheus_text(mdir: Path | None = None) -> str:
    root = _metrics_search_root(mdir or metrics_dir())
    lines: list[str] = []
    _export_aqe_metrics(lines, root)
    _export_mlops_metrics(lines, root)
    if not lines:
        lines.append("# No metrics yet — jalankan pipeline eksperimen terlebih dahulu\n")
    return "".join(lines)


class MetricsHandler(BaseHTTPRequestHandler):
    metrics_dir: Path = metrics_dir()

    def do_GET(self):
        if self.path in ("/metrics", "/"):
            body = build_prometheus_text(self.metrics_dir).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Prometheus metrics exporter (AQE + MLOps + Insight)")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.environ.get("METRICS_EXPORTER_PORT", "9101")))
    parser.add_argument("--metrics-dir", default=None)
    args = parser.parse_args()

    MetricsHandler.metrics_dir = Path(args.metrics_dir) if args.metrics_dir else metrics_dir()
    server = HTTPServer((args.host, args.port), MetricsHandler)
    print(f"Metrics exporter on http://{args.host}:{args.port}/metrics (dir={MetricsHandler.metrics_dir})")
    server.serve_forever()


if __name__ == "__main__":
    main()
