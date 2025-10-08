"""장기 예측 모델 유틸리티입니다. / Long-horizon forecast model utilities."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ForecastArtifacts:
    """학습 결과와 메타데이터입니다. / Trained model and metadata bundle."""

    model: Pipeline
    feature_columns: list[str]
    target_column: str
    training_frame: pd.DataFrame
    rmse: float | None


def _coerce_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """타임스탬프 정규화. / Normalize timestamp column."""

    working = df.copy()
    if "timestamp" in working.columns:
        working["timestamp"] = pd.to_datetime(
            working["timestamp"], utc=True, errors="coerce"
        )
    elif isinstance(working.index, pd.DatetimeIndex):
        working = working.reset_index().rename(columns={"index": "timestamp"})
        working["timestamp"] = pd.to_datetime(
            working["timestamp"], utc=True, errors="coerce"
        )
    else:
        working["timestamp"] = pd.NaT
    working = working.dropna(subset=["timestamp"]).sort_values("timestamp")
    return working


def _load_historical_data(
    source: Path, sqlite_table: str | None = None
) -> pd.DataFrame:
    """CSV/SQLite 데이터를 적재합니다. / Load CSV or SQLite historical dataset."""

    if not source.exists():
        LOGGER.warning("Historical dataset not found at %s", source)
        return pd.DataFrame()
    suffix = source.suffix.lower()
    if suffix == ".csv":
        data = pd.read_csv(source)
    elif suffix in {".sqlite", ".db"}:
        table_name = sqlite_table or "historical_weather"
        with sqlite3.connect(source) as conn:
            data = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    else:
        raise ValueError(f"Unsupported historical data format: {source.suffix}")
    if "location" not in data.columns:
        data["location"] = "UNKNOWN"
    return _coerce_timestamp(data)


def _assemble_training_frame(
    historical: pd.DataFrame,
    recent_frames: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """히스토리+최근 데이터를 병합합니다. / Merge historical and recent data."""

    parts: list[pd.DataFrame] = []
    if not historical.empty:
        parts.append(historical.copy())
    for location, frame in recent_frames.items():
        if frame.empty:
            continue
        working = _coerce_timestamp(frame)
        working["location"] = location
        parts.append(working)
    if not parts:
        return pd.DataFrame()
    merged = pd.concat(parts, ignore_index=True, sort=False)
    merged = merged.drop_duplicates(subset=["location", "timestamp"], keep="last")
    merged = merged.sort_values(["location", "timestamp"])
    return merged.reset_index(drop=True)


def _derive_feature_columns(
    df: pd.DataFrame,
    target_column: str,
    feature_columns: Sequence[str] | None,
) -> list[str]:
    """모델 입력 컬럼을 계산합니다. / Resolve feature column set for the model."""

    if feature_columns:
        return [col for col in feature_columns if col in df.columns]
    numeric_cols = [
        col
        for col, dtype in df.dtypes.items()
        if col != target_column and pd.api.types.is_numeric_dtype(dtype)
    ]
    return numeric_cols


def train_model(
    history_source: str | Path | None,
    recent_frames: Mapping[str, pd.DataFrame],
    target_column: str = "wave_height",
    feature_columns: Sequence[str] | None = None,
    cache_path: str | Path | None = None,
    sqlite_table: str | None = None,
    force_retrain: bool = False,
) -> ForecastArtifacts:
    """랜덤 포레스트를 학습합니다. / Train the RandomForest regression model."""

    history_path = Path(history_source) if history_source else None
    historical = (
        _load_historical_data(history_path, sqlite_table)
        if history_path
        else pd.DataFrame()
    )
    training_frame = _assemble_training_frame(historical, recent_frames)
    if training_frame.empty:
        raise ValueError("No data available for training the long-range model")

    resolved_features = _derive_feature_columns(
        training_frame, target_column, feature_columns
    )
    if not resolved_features:
        raise ValueError("No feature columns available for model training")
    if target_column not in training_frame.columns:
        raise ValueError(
            f"Target column '{target_column}' is missing from training data"
        )

    model_cache_path = Path(cache_path) if cache_path else None
    cached_artifacts: ForecastArtifacts | None = None
    if model_cache_path and model_cache_path.exists() and not force_retrain:
        payload = joblib.load(model_cache_path)
        model = payload["model"]
        cached_features = payload.get("feature_columns", resolved_features)
        cached_target = payload.get("target_column", target_column)
        cached_rmse = payload.get("rmse")
        cached_artifacts = ForecastArtifacts(
            model=model,
            feature_columns=list(cached_features),
            target_column=str(cached_target),
            training_frame=training_frame,
            rmse=cached_rmse,
        )

    if cached_artifacts:
        LOGGER.info("Loaded long-range model from cache: %s", model_cache_path)
        return cached_artifacts

    features = training_frame[resolved_features].astype(float)
    target = training_frame[target_column].astype(float)

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=256,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(features, target)
    predictions = pipeline.predict(features)
    residuals = target.to_numpy() - predictions
    rmse = float(np.sqrt(np.mean(residuals**2))) if len(residuals) else None

    if model_cache_path:
        model_cache_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": pipeline,
                "feature_columns": list(resolved_features),
                "target_column": target_column,
                "rmse": rmse,
            },
            model_cache_path,
        )
        LOGGER.info("Stored long-range model cache at %s", model_cache_path)

    return ForecastArtifacts(
        model=pipeline,
        feature_columns=list(resolved_features),
        target_column=target_column,
        training_frame=training_frame,
        rmse=rmse,
    )


def predict_long_range(
    artifacts: ForecastArtifacts,
    recent_frames: Mapping[str, pd.DataFrame],
    horizon_hours: int = 168,
    tz: str = "UTC",
) -> Dict[str, pd.DataFrame]:
    """7일 예보를 계산합니다. / Produce 7-day forecasts for each location."""

    outputs: Dict[str, pd.DataFrame] = {}
    if horizon_hours <= 0:
        return outputs
    for location, frame in recent_frames.items():
        if frame.empty:
            continue
        working = _coerce_timestamp(frame)
        if working.empty:
            continue
        feature_tail = working[artifacts.feature_columns].tail(1).copy()
        if feature_tail.empty:
            continue
        feature_tail = feature_tail.ffill(axis=0).bfill(axis=0)
        replicated = pd.concat([feature_tail] * horizon_hours, ignore_index=True)
        predictions = artifacts.model.predict(replicated)
        last_ts = working["timestamp"].iloc[-1]
        if last_ts.tzinfo is None:
            last_ts = last_ts.tz_localize("UTC")
        timestamps = pd.date_range(
            last_ts.tz_convert(tz) + pd.Timedelta(hours=1),
            periods=horizon_hours,
            freq="H",
            tz=tz,
        )
        result = pd.DataFrame(
            {
                "timestamp": timestamps,
                artifacts.target_column: predictions,
                "location": location,
                "model_rmse": artifacts.rmse,
            }
        )
        outputs[location] = result
    return outputs


def detect_anomalies(
    artifacts: ForecastArtifacts,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """잔차 이상치를 탐지합니다. / Detect residual anomalies from training data."""

    frame = artifacts.training_frame
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "location",
                "observed",
                "predicted",
                "z_score",
                "message",
            ]
        )
    features = frame[artifacts.feature_columns]
    target = frame[artifacts.target_column]
    predictions = artifacts.model.predict(features)
    residuals = target.to_numpy() - predictions
    std = float(np.std(residuals))
    if std == 0 or np.isnan(std):
        return pd.DataFrame(
            columns=[
                "timestamp",
                "location",
                "observed",
                "predicted",
                "z_score",
                "message",
            ]
        )
    z_scores = residuals / std
    mask = np.abs(z_scores) >= threshold
    if not np.any(mask):
        return pd.DataFrame(
            columns=[
                "timestamp",
                "location",
                "observed",
                "predicted",
                "z_score",
                "message",
            ]
        )
    anomalies = frame.loc[
        mask, ["timestamp", "location", artifacts.target_column]
    ].copy()
    anomalies.rename(columns={artifacts.target_column: "observed"}, inplace=True)
    anomalies["predicted"] = predictions[mask]
    anomalies["z_score"] = z_scores[mask]
    anomalies["message"] = [
        f"Deviation of {abs(z):.2f}σ for {artifacts.target_column}"
        for z in anomalies["z_score"]
    ]
    return anomalies.reset_index(drop=True)
