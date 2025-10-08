#!/usr/bin/env python3
"""Three-day marine weather job orchestrator."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.pipeline.config import PipelineConfig, load_pipeline_config
from src.marine_ops.pipeline.daypart import (
    decide_dayparts,
    route_window,
    summarize_dayparts,
)
from src.marine_ops.pipeline.eri import compute_eri_3d
from src.marine_ops.pipeline.fusion import fuse_timeseries_3d
from src.marine_ops.pipeline.ingest import collect_weather_data_3d
from src.marine_ops.pipeline.ml_forecast import (
    detect_anomalies,
    predict_long_range,
    train_model,
)
from src.marine_ops.pipeline.reporting import render_html_3d, write_side_outputs


def _ensure_location(cfg: PipelineConfig, location_id: str) -> None:
    if location_id not in cfg.location_ids():
        raise ValueError(f"Location '{location_id}' not configured in locations.yaml")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate 72h marine forecast reports for AGI/DAS"
    )
    parser.add_argument(
        "--config", default="config/locations.yaml", help="Pipeline configuration file"
    )
    parser.add_argument("--out", default="out", help="Output directory")
    parser.add_argument(
        "--mode",
        choices=["auto", "online", "offline"],
        default="auto",
        help="Execution mode hint",
    )
    parser.add_argument(
        "--locations",
        nargs="*",
        default=["AGI", "DAS"],
        help="Location identifiers to process",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    cfg = load_pipeline_config(args.config)
    for loc in args.locations:
        _ensure_location(cfg, loc)

    run_ts = datetime.now(timezone.utc)
    print(f"[72H] Starting run at {run_ts.isoformat()} (mode={args.mode})")

    raw = collect_weather_data_3d(cfg, mode=args.mode)
    fused = fuse_timeseries_3d(raw["sources"])
    compute_eri_3d(fused["timeseries"])  # ERI computed for downstream analyses

    print("[72H] Training long-range forecast model")
    try:
        artifacts = train_model(
            history_source=cfg.ml_history_path,
            recent_frames=fused["frames"],
            target_column="wave_height",
            cache_path=cfg.ml_model_cache,
            sqlite_table=cfg.ml_sqlite_table,
        )
        long_range = predict_long_range(
            artifacts=artifacts,
            recent_frames=fused["frames"],
            horizon_hours=24 * 7,
            tz=cfg.tz,
        )
        anomalies = detect_anomalies(artifacts)
    except ValueError as exc:
        print(f"[72H] Long-range model skipped: {exc}")
        long_range = {}
        anomalies = pd.DataFrame()

    decisions = {}
    for loc in args.locations:
        frame = fused["frames"].get(loc, pd.DataFrame())
        summary = summarize_dayparts(frame, cfg.tz)
        decisions[loc] = decide_dayparts(summary, cfg, raw.get("ncm_alerts", []))
        point_count = sum(
            metrics.count
            for day_metrics in summary.values()
            for metrics in day_metrics.values()
        )
        print(f"[72H] Processed {loc}: {point_count} hourly points across dayparts")

    agi_decisions = decisions.get("AGI", {})
    das_decisions = decisions.get("DAS", {})
    windows = route_window(agi_decisions, das_decisions)

    html_path = render_html_3d(
        run_ts=run_ts,
        cfg=cfg,
        agi=agi_decisions,
        das=das_decisions,
        route_windows=windows,
        ncm_alerts=raw.get("ncm_alerts", []),
        long_range_forecasts=long_range,
        anomaly_alerts=anomalies,
        out_dir=args.out,
    )

    side_outputs = write_side_outputs(
        run_ts=run_ts,
        cfg=cfg,
        agi=agi_decisions,
        das=das_decisions,
        route_windows=windows,
        ncm_alerts=raw.get("ncm_alerts", []),
        api_status=raw.get("api_status", {}),
        long_range_forecasts=long_range,
        anomaly_alerts=anomalies,
        out_dir=args.out,
    )

    print(f"[72H] HTML report: {html_path}")
    for label, path in side_outputs.items():
        print(f"[72H] {label.upper()} saved to {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
