#!/usr/bin/env python3
"""KR: 장기 예측 모델 학습 유틸리티입니다. / EN: CLI utility for long-range model training."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.marine_ops.pipeline.ml_forecast import MODEL_FILENAME, train_model


def _parse_args() -> argparse.Namespace:
    """KR: 명령행 인자를 파싱합니다. / EN: Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Train the marine long-range forecast model")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=[
            "data/historical_marine_metrics.csv",
            "data/historical_marine_metrics.sqlite",
        ],
        help="Historical dataset sources (CSV or SQLite)",
    )
    parser.add_argument(
        "--table",
        default="marine_ml_history",
        help="SQLite table name to read when a database source is provided",
    )
    parser.add_argument(
        "--output",
        default="cache/ml_forecast",
        help="Directory where the trained model artifact will be stored",
    )
    parser.add_argument(
        "--metadata",
        default="cache/ml_forecast/metadata.json",
        help="Optional path to write training metadata as JSON",
    )
    return parser.parse_args()


def main() -> int:
    """KR: 모델을 학습하고 메타데이터를 저장합니다. / EN: Train the model and store metadata."""

    args = _parse_args()
    artifact_dir = Path(args.output)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    sources = [Path(item) for item in args.sources]

    artifacts = train_model(sources, artifact_dir, sqlite_table=args.table)
    metadata = {
        "artifact": str(artifacts.artifact_path),
        "rows_trained": artifacts.metrics.get("rows_trained"),
        "mae": artifacts.metrics.get("mae"),
        "feature_columns": artifacts.feature_columns,
        "model_filename": MODEL_FILENAME,
    }

    metadata_path = Path(args.metadata)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    rows_trained = float(metadata.get("rows_trained") or 0.0)
    mae_value = float(metadata.get("mae") or 0.0)
    print(
        "[ML] Training complete: "
        f"artifact={metadata['artifact']} rows={rows_trained:.0f} "
        f"mae={mae_value:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
