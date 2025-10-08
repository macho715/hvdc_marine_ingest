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
from src.marine_ops.pipeline.daypart import decide_dayparts, route_window, summarize_dayparts
from src.marine_ops.pipeline.eri import compute_eri_3d
from src.marine_ops.pipeline.fusion import fuse_timeseries_3d
from src.marine_ops.pipeline.ingest import collect_weather_data_3d
from src.marine_ops.pipeline.ml_forecast import (
    MODEL_FILENAME,
    detect_anomalies,
    detect_dynamic_anomalies,
    load_model,
    predict_long_range,
    predict_long_range_dynamic,
    train_dynamic_model,
    train_model,
)
from src.marine_ops.pipeline.reporting import render_html_3d, write_side_outputs


def _ensure_location(cfg: PipelineConfig, location_id: str) -> None:
    if location_id not in cfg.location_ids():
        raise ValueError(f"Location '{location_id}' not configured in locations.yaml")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate 72h marine forecast reports for AGI/DAS")
    parser.add_argument("--config", default="config/locations.yaml", help="Pipeline configuration file")
    parser.add_argument("--out", default="out", help="Output directory")
    parser.add_argument("--mode", choices=["auto", "online", "offline"], default="auto", help="Execution mode hint")
    parser.add_argument("--locations", nargs="*", default=["AGI", "DAS"], help="Location identifiers to process")
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

    long_range: dict[str, pd.DataFrame] = {}
    anomalies: dict[str, list[dict[str, object]]] = {}
    ml_metadata: dict[str, object] = {}
    dynamic_success = False
    dynamic_configured = bool(getattr(cfg, "ml_history_path", None) or getattr(cfg, "ml_model_cache", None))
    if dynamic_configured:
        print("[72H][ML] Training dynamic long-range model")
        try:
            dynamic_artifacts = train_dynamic_model(
                history_source=getattr(cfg, "ml_history_path", None),
                recent_frames=fused["frames"],
                target_column=getattr(cfg, "ml_target_column", "wave_height"),
                feature_columns=getattr(cfg, "ml_feature_columns", None),
                cache_path=getattr(cfg, "ml_model_cache", None),
                sqlite_table=getattr(cfg, "ml_sqlite_table", None),
                force_retrain=bool(getattr(cfg, "ml_force_retrain", False)),
            )
            horizon_setting = getattr(cfg, "ml_forecast_horizon_hours", None)
            horizon_hours = int(horizon_setting) if horizon_setting else 24 * 7
            dynamic_long_range = predict_long_range_dynamic(
                artifacts=dynamic_artifacts,
                recent_frames=fused["frames"],
                horizon_hours=horizon_hours,
                tz=cfg.tz,
            )
            converted_long_range: dict[str, pd.DataFrame] = {}
            for location, df in dynamic_long_range.items():
                if df is None or df.empty:
                    continue
                working = df.copy()
                predicted_col = None
                for candidate in (dynamic_artifacts.target_column, "prediction", "predicted"):
                    if candidate in working.columns:
                        predicted_col = candidate
                        break
                if predicted_col is None:
                    continue
                if "location" not in working.columns:
                    working.insert(0, "location", location)
                working.rename(columns={predicted_col: "predicted_value"}, inplace=True)
                if "hs_value" not in working.columns:
                    working["hs_value"] = pd.NA
                if "wind_value" not in working.columns:
                    working["wind_value"] = pd.NA
                converted_long_range[location] = working
            long_range = converted_long_range
            anomalies_df = detect_dynamic_anomalies(dynamic_artifacts)
            if not anomalies_df.empty:
                grouped: dict[str, list[dict[str, object]]] = {}
                for record in anomalies_df.to_dict(orient="records"):
                    loc = str(record.get("location", "UNKNOWN"))
                    payload = record.copy()
                    payload.pop("location", None)
                    ts_value = payload.get("timestamp")
                    if hasattr(ts_value, "isoformat"):
                        payload["timestamp"] = ts_value.isoformat()  # type: ignore[assignment]
                    grouped.setdefault(loc, []).append(payload)
                anomalies = grouped
            else:
                anomalies = {}
            ml_metadata = {
                "mode": "dynamic",
                "target_column": dynamic_artifacts.target_column,
                "feature_columns": dynamic_artifacts.feature_columns,
                "rmse": dynamic_artifacts.rmse,
                "cache": str(dynamic_artifacts.cache_path) if dynamic_artifacts.cache_path else None,
                "rows_trained": (
                    dynamic_artifacts.metrics.get("rows_trained")
                    if dynamic_artifacts.metrics and dynamic_artifacts.metrics.get("rows_trained") is not None
                    else len(dynamic_artifacts.training_frame)
                ),
            }
            dynamic_success = True
        except ValueError as exc:
            print(f"[72H][ML] Dynamic model skipped: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"[72H][ML] Dynamic ML pipeline failed: {exc}")
    if not dynamic_success:
        model_dir = Path("cache/ml_forecast")
        model_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = model_dir / MODEL_FILENAME
        history_sources = [
            Path("data/historical_marine_metrics.csv"),
            Path("data/historical_marine_metrics.sqlite"),
        ]
        model = None
        training_metrics: dict[str, object] = {}
        if artifact_path.exists():
            try:
                model = load_model(artifact_path)
                print(f"[72H][ML] Loaded cached model from {artifact_path}")
            except Exception as exc:  # noqa: BLE001
                print(f"[72H][ML] Failed to load cached model: {exc}. Retraining...")
        if model is None:
            try:
                artifacts = train_model(history_sources, model_dir)
                model = artifacts.model
                training_metrics = artifacts.metrics
                artifact_path = artifacts.artifact_path
                print(
                    "[72H][ML] Trained RandomForest model "
                    f"({training_metrics.get('rows_trained', 0):.0f} rows, "
                    f"MAE={training_metrics.get('mae', 0.0):.2f})",
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[72H][ML] Training failed: {exc}")
                model = None
        long_range = {}
        anomalies = {}
        if model is not None:
            try:
                long_range = predict_long_range(model, fused["frames"])
            except Exception as exc:  # noqa: BLE001
                print(f"[72H][ML] Long-range prediction failed: {exc}")
                long_range = {}
            try:
                anomalies = detect_anomalies(fused["frames"])
            except Exception as exc:  # noqa: BLE001
                print(f"[72H][ML] Anomaly detection failed: {exc}")
                anomalies = {}
            ml_metadata = {
                "mode": "legacy-cache",
                "artifact": str(artifact_path),
                "metrics": training_metrics,
            }
        else:
            print("[72H][ML] Skipping ML outputs due to missing model")
            ml_metadata = {
                "mode": "legacy-cache",
                "artifact": str(artifact_path),
            }

    decisions = {}
    for loc in args.locations:
        frame = fused["frames"].get(loc, pd.DataFrame())
        summary = summarize_dayparts(frame, cfg.tz)
        decisions[loc] = decide_dayparts(summary, cfg, raw.get("ncm_alerts", []))
        point_count = sum(metrics.count for day_metrics in summary.values() for metrics in day_metrics.values())
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
        long_range=long_range,
        anomalies=anomalies,
        ml_metadata=ml_metadata,
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
        long_range=long_range,
        anomalies=anomalies,
        ml_metadata=ml_metadata,
        out_dir=args.out,
    )

    print(f"[72H] HTML report: {html_path}")
    for label, path in side_outputs.items():
        print(f"[72H] {label.upper()} saved to {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
