"""Tests for the ML forecast plugin."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.marine_ops.pipeline.ml_forecast import (
    MODEL_FILENAME,
    detect_anomalies,
    predict_long_range,
    train_model,
)


def _synth_frame() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=72, freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "hs_mean": np.linspace(0.8, 1.4, len(index)),
            "wind_speed_kt": np.linspace(10.0, 16.0, len(index)),
            "eri": np.linspace(0.25, 0.45, len(index)),
        },
        index=index,
    )


def test_train_model_and_predict(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifacts = train_model([], artifact_dir)
    assert artifact_dir.joinpath(MODEL_FILENAME).exists()

    frames = {"AGI": _synth_frame()}
    forecasts = predict_long_range(artifacts.model, frames)

    assert "AGI" in forecasts
    agi_forecast = forecasts["AGI"]
    assert isinstance(agi_forecast, pd.DataFrame)
    assert len(agi_forecast) == 7
    assert {"timestamp", "predicted_eri", "hs_value", "wind_value"}.issubset(agi_forecast.columns)


def test_detect_anomalies_returns_mapping(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    train_model([], artifact_dir)

    frames = {"DAS": _synth_frame()}
    anomalies = detect_anomalies(frames)

    assert isinstance(anomalies, dict)
    assert "DAS" in anomalies
    for record in anomalies["DAS"]:
        assert "timestamp" in record
