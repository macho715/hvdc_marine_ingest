"""ML 예측 파이프라인 테스트입니다. / Tests for the ML forecast pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.marine_ops.pipeline.ml_forecast import (
    detect_anomalies,
    predict_long_range,
    train_model,
)


def _synthetic_history(periods: int, seed: int = 7) -> pd.DataFrame:
    """합성 히스토리 데이터를 생성합니다. / Build synthetic historical samples."""

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2024-01-01", periods=periods, freq="H", tz="UTC")
    base_wave = 1.2 + 0.4 * np.sin(np.linspace(0.0, 6.0, periods))
    wave_height = base_wave + rng.normal(0.0, 0.05, periods)
    wind_speed = 8.0 + 2.0 * np.cos(np.linspace(0.0, 3.0, periods))
    sea_temp = 28.0 + 0.3 * np.sin(np.linspace(0.0, 2.0, periods))
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "location": "AGI",
            "wave_height": wave_height,
            "wind_speed_10m": wind_speed,
            "sea_surface_temperature": sea_temp,
        }
    )


def test_train_predict_and_anomalies(tmp_path: Path) -> None:
    """랜덤 포레스트 흐름을 검증합니다. / Validate training, prediction, anomalies."""

    history = _synthetic_history(240)
    history_path = tmp_path / "history.csv"
    history.to_csv(history_path, index=False)

    recent_frame = history.set_index("timestamp").iloc[-72:]
    artifacts = train_model(
        history_source=history_path,
        recent_frames={"AGI": recent_frame},
        cache_path=tmp_path / "model.joblib",
    )

    forecasts = predict_long_range(
        artifacts=artifacts,
        recent_frames={"AGI": recent_frame},
        horizon_hours=48,
        tz="Asia/Dubai",
    )

    assert "AGI" in forecasts
    assert len(forecasts["AGI"]) == 48
    assert set(forecasts["AGI"].columns) >= {"timestamp", "wave_height", "location"}

    anomalies = detect_anomalies(artifacts, threshold=2.0)
    if not anomalies.empty:
        assert {"timestamp", "observed", "predicted", "z_score"}.issubset(
            anomalies.columns
        )


def test_train_with_recent_only(tmp_path: Path) -> None:
    """히스토리 없이 학습 fallback을 검증합니다. / Train with only recent frames."""

    timestamps = pd.date_range("2024-02-01", periods=96, freq="H", tz="UTC")
    wave_height = np.linspace(0.8, 1.6, 96)
    wind_speed = np.linspace(6.0, 12.0, 96)
    recent = pd.DataFrame(
        {
            "timestamp": timestamps,
            "wave_height": wave_height,
            "wind_speed_10m": wind_speed,
            "sea_surface_temperature": 28.5,
        }
    ).set_index("timestamp")

    artifacts = train_model(
        history_source=None,
        recent_frames={"DAS": recent},
        cache_path=tmp_path / "recent_model.joblib",
    )

    forecasts = predict_long_range(
        artifacts=artifacts,
        recent_frames={"DAS": recent},
        horizon_hours=24,
        tz="Asia/Dubai",
    )

    assert "DAS" in forecasts
    assert len(forecasts["DAS"]) == 24
