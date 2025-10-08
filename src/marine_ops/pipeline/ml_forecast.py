"""Marine ML forecasting utilities for the extended 72h pipeline."""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_FILENAME = "marine_ml_forecast.joblib"
DEFAULT_TABLE_NAME = "marine_ml_history"
FEATURE_COLUMNS = [
    "hs_value",
    "wind_value",
    "eri_value",
    "eri_rolling_24h",
    "hour",
    "dayofweek",
]
TARGET_COLUMN = "eri_target_7d"
LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MLForecastArtifacts:
    """KR: 장기 예측 모델 산출물을 담는 컨테이너입니다. / EN: Container object describing long-range forecast artifacts."""

    model: Pipeline
    artifact_path: Path
    feature_columns: List[str]
    metrics: Dict[str, float]


@dataclass(slots=True)
class ForecastArtifacts:
    """Container describing dynamically trained long-range forecast artifacts."""

    model: Pipeline
    feature_columns: List[str]
    target_column: str
    training_frame: pd.DataFrame
    rmse: float | None
    cache_path: Path | None = None
    artifact_path: Path | None = None
    metrics: Dict[str, float] | None = None


def _normalise_paths(sources: Iterable[str | Path]) -> List[Path]:
    """KR: 데이터 소스 경로 리스트를 정규화합니다. / EN: Normalise iterable of dataset source paths."""

    paths: List[Path] = []
    for source in sources:
        if not source:
            continue
        path = Path(source).expanduser().resolve()
        paths.append(path)
    return paths


def _load_csv(path: Path) -> pd.DataFrame:
    """KR: CSV 파일을 로드합니다. / EN: Load a dataset from CSV."""

    return pd.read_csv(path, parse_dates=["timestamp"], infer_datetime_format=True)


def _load_sqlite(path: Path, table: str) -> pd.DataFrame:
    """KR: SQLite 테이블을 로드합니다. / EN: Load a dataset table from SQLite."""

    import sqlite3

    with sqlite3.connect(path) as conn:
        query = f"SELECT * FROM {table}"
        return pd.read_sql_query(query, conn, parse_dates=["timestamp"])


def _coalesce_column(frame: pd.DataFrame, candidates: Sequence[str], default: float = 0.0) -> pd.Series:
    """KR: 우선순위에 따라 열을 선택합니다. / EN: Pick the first available column by priority."""

    for name in candidates:
        if name in frame.columns:
            return pd.to_numeric(frame[name], errors="coerce").fillna(default)
    return pd.Series([default] * len(frame), index=frame.index)


def _safe_pick(row: Mapping[str, object], candidates: Sequence[str]) -> float:
    """KR: 행에서 첫 번째 유효 값을 선택합니다. / EN: Pick the first valid value from row mapping."""

    for key in candidates:
        if key in row:
            value = row.get(key)
            try:
                cast_value = float(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            if not np.isnan(cast_value):
                return cast_value
    return float("nan")


def _prepare_training_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """KR: 학습용 데이터프레임을 정리합니다. / EN: Prepare the training dataframe."""

    frame = raw.copy()
    if "timestamp" not in frame.columns:
        raise ValueError("Historical dataset requires a 'timestamp' column")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp")

    frame["hs_value"] = _coalesce_column(frame, ["hs", "hs_mean", "wave_height", "hs_p90"], default=0.0)
    frame["wind_value"] = _coalesce_column(
        frame,
        [
            "wind_speed_kt",
            "wind_mean_kt",
            "wind_speed",
            "wind_speed_10m",
            "wind_p90_kt",
        ],
        default=0.0,
    )
    if "wind_speed_10m" in frame.columns and "wind_value" in frame.columns:
        fallback = frame["wind_speed_10m"] * 1.9438444924406
        frame.loc[:, "wind_value"] = frame["wind_value"].where(frame["wind_value"] > 0.0, fallback)

    frame["eri_value"] = _coalesce_column(frame, ["eri", "eri_score", "eri_mean"], default=0.0)
    frame["eri_rolling_24h"] = frame["eri_value"].rolling(window=24, min_periods=1).mean()
    frame["hour"] = frame["timestamp"].dt.hour.astype(float)
    frame["dayofweek"] = frame["timestamp"].dt.dayofweek.astype(float)
    frame[TARGET_COLUMN] = frame["eri_value"].shift(-168)
    frame = frame.dropna(subset=[TARGET_COLUMN])
    if frame.empty:
        raise ValueError("Insufficient historical rows after preparing features")
    return frame


def _generate_synthetic_history(period_hours: int = 24 * 28, seed: int = 42) -> pd.DataFrame:
    """KR: 합성 학습 데이터를 생성합니다. / EN: Generate synthetic training history."""

    rng = np.random.default_rng(seed)
    now = pd.Timestamp.utcnow()
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")
    timestamps = pd.date_range(end=now, periods=period_hours, freq="h")
    hs = 1.5 + 0.4 * np.sin(np.linspace(0, 8 * np.pi, period_hours)) + rng.normal(0, 0.1, period_hours)
    wind = 12.0 + 1.5 * np.cos(np.linspace(0, 6 * np.pi, period_hours)) + rng.normal(0, 0.5, period_hours)
    eri = 0.25 + 0.05 * np.sin(np.linspace(0, 4 * np.pi, period_hours)) + 0.02 * rng.normal(0, 1, period_hours)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "hs_mean": hs,
            "wind_mean_kt": wind,
            "eri": eri,
        }
    )


def train_model(
    data_sources: Iterable[str | Path],
    artifact_dir: str | Path,
    *,
    sqlite_table: str = DEFAULT_TABLE_NAME,
    random_state: int = 42,
) -> MLForecastArtifacts:
    """KR: RandomForest 모델을 학습하고 저장합니다. / EN: Train and persist the RandomForest model."""

    paths = _normalise_paths(data_sources)
    frames: List[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() == ".csv":
            frames.append(_load_csv(path))
        elif path.suffix.lower() in {".sqlite", ".db"}:
            frames.append(_load_sqlite(path, sqlite_table))
    if not frames:
        frames.append(_generate_synthetic_history())

    combined = pd.concat(frames, ignore_index=True)
    prepared = _prepare_training_frame(combined)
    X = prepared[FEATURE_COLUMNS]
    y = prepared[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        shuffle=False,
    )

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=200,
                    max_depth=12,
                    min_samples_leaf=4,
                    random_state=random_state,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    mae = float(mean_absolute_error(y_test, predictions))

    artifact_directory = Path(artifact_dir).expanduser().resolve()
    artifact_directory.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_directory / MODEL_FILENAME
    joblib.dump(pipeline, artifact_path)

    metadata = {
        "rows_trained": float(len(prepared)),
        "mae": round(mae, 4),
    }

    return MLForecastArtifacts(
        model=pipeline,
        artifact_path=artifact_path,
        feature_columns=FEATURE_COLUMNS.copy(),
        metrics=metadata,
    )


def load_model(artifact_path: str | Path) -> Pipeline:
    """KR: 저장된 모델을 로드합니다. / EN: Load a persisted model."""

    return joblib.load(Path(artifact_path).expanduser().resolve())


def _extract_recent_features(frame: pd.DataFrame) -> dict:
    """KR: 최신 시점에서 피처를 산출합니다. / EN: Derive feature vector from the most recent window."""

    working = frame.copy()
    working = working.sort_index()
    if not isinstance(working.index, pd.DatetimeIndex):
        if "timestamp" in working.columns:
            working["timestamp"] = pd.to_datetime(working["timestamp"], utc=True, errors="coerce")
            working = working.dropna(subset=["timestamp"]).set_index("timestamp")
        else:
            raise ValueError("Fused frame requires DatetimeIndex or 'timestamp' column")

    if working.empty:
        recent = working
    else:
        last_ts = working.index.max()
        window_start = last_ts - pd.Timedelta(hours=24)
        recent = working.loc[window_start:last_ts]
    if recent.empty:
        return {
            "hs_value": 0.0,
            "wind_value": 0.0,
            "eri_value": 0.0,
            "eri_rolling_24h": 0.0,
        }

    hs_series = recent.filter(regex="hs|wave_height", axis=1)
    if "hs_value" in recent.columns:
        hs_series = recent[["hs_value"]]
    wind_series = recent.filter(regex="wind_speed|wind_mean", axis=1)
    if "wind_value" in recent.columns:
        wind_series = recent[["wind_value"]]
    eri_series = recent.filter(regex="eri", axis=1)
    if "eri_value" in recent.columns:
        eri_series = recent[["eri_value"]]

    hs_value = float(hs_series.mean(numeric_only=True).iloc[-1]) if not hs_series.empty else 0.0
    wind_value = float(wind_series.mean(numeric_only=True).iloc[-1]) if not wind_series.empty else 0.0
    eri_value = float(eri_series.mean(numeric_only=True).iloc[-1]) if not eri_series.empty else 0.0

    return {
        "hs_value": hs_value,
        "wind_value": wind_value,
        "eri_value": eri_value,
        "eri_rolling_24h": float(recent.filter(like="eri", axis=1).mean(numeric_only=True).mean())
        if not eri_series.empty
        else eri_value,
    }


def predict_long_range(
    model: Pipeline,
    fused_frames: Mapping[str, pd.DataFrame],
    *,
    horizon_hours: int = 168,
    step_hours: int = 24,
) -> Dict[str, pd.DataFrame]:
    """KR: 7일 장기 ERI 예측을 생성합니다. / EN: Produce 7-day ERI forecasts."""

    results: Dict[str, pd.DataFrame] = {}
    for location, frame in fused_frames.items():
        if frame is None or frame.empty:
            continue

        recent_features = _extract_recent_features(frame)
        if not isinstance(frame.index, pd.DatetimeIndex):
            if "timestamp" in frame.columns:
                last_ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dropna().max()
            else:
                continue
        else:
            last_ts = frame.index.max()
        if pd.isna(last_ts):
            continue
        last_ts = last_ts.tz_convert("UTC") if last_ts.tzinfo else last_ts.tz_localize("UTC")

        rows = []
        for offset in range(step_hours, horizon_hours + step_hours, step_hours):
            future_ts = last_ts + pd.Timedelta(hours=offset)
            feature_vector = {
                **recent_features,
                "hour": float(future_ts.hour),
                "dayofweek": float(future_ts.dayofweek),
            }
            input_df = pd.DataFrame([feature_vector])[FEATURE_COLUMNS]
            prediction = float(model.predict(input_df)[0])
            rows.append(
                {
                    "timestamp": future_ts,
                    "predicted_eri": prediction,
                    "hs_value": feature_vector["hs_value"],
                    "wind_value": feature_vector["wind_value"],
                }
            )
        results[location] = pd.DataFrame(rows)
    return results


def detect_anomalies(
    fused_frames: Mapping[str, pd.DataFrame],
    *,
    contamination: float = 0.15,
    random_state: int = 42,
) -> Dict[str, List[Dict[str, object]]]:
    """KR: 최근 시계열의 이상 징후를 탐지합니다. / EN: Detect anomalies from the recent fused timeseries."""

    anomalies: Dict[str, List[Dict[str, object]]] = {}
    for location, frame in fused_frames.items():
        if frame is None or frame.empty:
            continue
        working = frame.copy()
        if not isinstance(working.index, pd.DatetimeIndex):
            if "timestamp" in working.columns:
                working["timestamp"] = pd.to_datetime(working["timestamp"], utc=True, errors="coerce")
                working = working.dropna(subset=["timestamp"]).set_index("timestamp")
            else:
                continue
        last_ts = working.index.max()
        window_start = last_ts - pd.Timedelta(hours=72)
        recent = working.loc[window_start:last_ts]
        if recent.empty:
            continue
        feature_frame = pd.DataFrame(
            {
                "hs_value": _coalesce_column(recent, ["hs_value", "wave_height", "hs", "hs_mean"], default=0.0),
                "wind_value": _coalesce_column(
                    recent,
                    ["wind_value", "wind_speed_kt", "wind_mean_kt", "wind_speed"],
                    default=0.0,
                ),
                "eri_value": _coalesce_column(recent, ["eri_value", "eri", "eri_score"], default=0.0),
            }
        )
        detector = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
        )
        detector.fit(feature_frame)
        predictions = detector.predict(feature_frame)
        flagged_indices = feature_frame.index[predictions == -1]
        if flagged_indices.empty:
            continue
        location_anomalies: List[Dict[str, object]] = []
        for ts in flagged_indices:
            row = recent.loc[ts]
            if isinstance(row, pd.Series):
                row_mapping = row.to_dict()
            else:
                row_mapping = row.iloc[0].to_dict()
            location_anomalies.append(
                {
                    "timestamp": ts.isoformat(),
                    "eri_value": _safe_pick(row_mapping, ["eri", "eri_score", "eri_value"]),
                    "hs_value": _safe_pick(row_mapping, ["hs", "wave_height", "hs_value", "hs_mean"]),
                    "wind_value": _safe_pick(
                        row_mapping,
                        ["wind_speed_kt", "wind_mean_kt", "wind_speed", "wind_value"],
                    ),
                }
            )
        anomalies[location] = location_anomalies
    return anomalies


def _normalise_history_sources(
    history_source: str | Path | Iterable[str | Path] | None,
) -> List[Path]:
    """Normalise historical data source inputs into a list of paths."""
    if history_source is None:
        return []
    if isinstance(history_source, (str, Path)):
        return [Path(history_source).expanduser().resolve()]
    paths: List[Path] = []
    for item in history_source:
        if not item:
            continue
        paths.append(Path(item).expanduser().resolve())
    return paths


def _coerce_timestamp_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure that a dataframe has a proper UTC timestamp column."""
    working = df.copy()
    if "timestamp" in working.columns:
        working["timestamp"] = pd.to_datetime(working["timestamp"], utc=True, errors="coerce")
    elif isinstance(working.index, pd.DatetimeIndex):
        working = working.reset_index().rename(columns={"index": "timestamp"})
        working["timestamp"] = pd.to_datetime(working["timestamp"], utc=True, errors="coerce")
    else:
        working["timestamp"] = pd.NaT
    working = working.dropna(subset=["timestamp"]).sort_values("timestamp")
    return working


def _load_historical_dataset(source: Path, sqlite_table: str | None = None) -> pd.DataFrame:
    """Load a historical dataset from CSV or SQLite storage."""
    if not source.exists():
        LOGGER.warning("Historical dataset not found at %s", source)
        return pd.DataFrame()
    suffix = source.suffix.lower()
    if suffix == ".csv":
        data = pd.read_csv(source)
    elif suffix in {".sqlite", ".db"}:
        table_name = sqlite_table or DEFAULT_TABLE_NAME
        with sqlite3.connect(source) as conn:
            data = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    else:
        raise ValueError(f"Unsupported historical data format: {source.suffix}")
    if "location" not in data.columns:
        data["location"] = "UNKNOWN"
    return _coerce_timestamp_frame(data)


def _assemble_training_frame_dynamic(
    historical: pd.DataFrame,
    recent_frames: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Merge historical data with the latest fused frames for model training."""
    parts: List[pd.DataFrame] = []
    if not historical.empty:
        parts.append(historical.copy())
    for location, frame in recent_frames.items():
        if frame is None or frame.empty:
            continue
        working = _coerce_timestamp_frame(frame)
        if working.empty:
            continue
        working["location"] = location
        parts.append(working)
    if not parts:
        return pd.DataFrame()
    merged = pd.concat(parts, ignore_index=True, sort=False)
    merged = merged.drop_duplicates(subset=["location", "timestamp"], keep="last")
    merged = merged.sort_values(["location", "timestamp"])
    return merged.reset_index(drop=True)


def _derive_dynamic_feature_columns(
    df: pd.DataFrame,
    target_column: str,
    feature_columns: Sequence[str] | None,
) -> List[str]:
    """Determine the feature columns to use when training the dynamic model."""
    if feature_columns:
        return [col for col in feature_columns if col in df.columns]
    numeric_cols = [
        col
        for col, dtype in df.dtypes.items()
        if col != target_column and pd.api.types.is_numeric_dtype(dtype)
    ]
    return numeric_cols


def train_dynamic_model(
    *,
    history_source: str | Path | Iterable[str | Path] | None,
    recent_frames: Mapping[str, pd.DataFrame],
    target_column: str = "wave_height",
    feature_columns: Sequence[str] | None = None,
    cache_path: str | Path | None = None,
    sqlite_table: str | None = None,
    force_retrain: bool = False,
) -> ForecastArtifacts:
    """Train or load a dynamic RandomForest regression model for long-range forecasts."""
    sources = _normalise_history_sources(history_source)
    historical_frames: List[pd.DataFrame] = []
    for source in sources:
        historical_frames.append(_load_historical_dataset(source, sqlite_table))
    historical = (
        pd.concat(historical_frames, ignore_index=True, sort=False) if historical_frames else pd.DataFrame()
    )
    training_frame = _assemble_training_frame_dynamic(historical, recent_frames)
    if training_frame.empty:
        raise ValueError("No data available for training the long-range model")
    resolved_features = _derive_dynamic_feature_columns(training_frame, target_column, feature_columns)
    if not resolved_features:
        raise ValueError("No feature columns available for model training")
    if target_column not in training_frame.columns:
        raise ValueError(f"Target column '{target_column}' is missing from training data")
    cache_file = Path(cache_path).expanduser().resolve() if cache_path else None
    if cache_file and cache_file.exists() and not force_retrain:
        payload = joblib.load(cache_file)
        model = payload["model"]
        cached_features = list(payload.get("feature_columns", resolved_features))
        cached_target = str(payload.get("target_column", target_column))
        cached_rmse = payload.get("rmse")
        cached_metrics = payload.get("metrics")
        LOGGER.info("Loaded long-range model from cache: %s", cache_file)
        return ForecastArtifacts(
            model=model,
            feature_columns=cached_features,
            target_column=cached_target,
            training_frame=training_frame,
            rmse=float(cached_rmse) if cached_rmse is not None else None,
            cache_path=cache_file,
            artifact_path=cache_file,
            metrics=cached_metrics if isinstance(cached_metrics, dict) else None,
        )
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
    metrics = {
        "rows_trained": float(len(training_frame)),
        "rmse": float(rmse) if rmse is not None else None,
    }
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": pipeline,
                "feature_columns": list(resolved_features),
                "target_column": target_column,
                "rmse": rmse,
                "metrics": metrics,
            },
            cache_file,
        )
        LOGGER.info("Stored long-range model cache at %s", cache_file)
    return ForecastArtifacts(
        model=pipeline,
        feature_columns=list(resolved_features),
        target_column=target_column,
        training_frame=training_frame,
        rmse=rmse,
        cache_path=cache_file,
        artifact_path=cache_file,
        metrics=metrics,
    )


def predict_long_range_dynamic(
    artifacts: ForecastArtifacts,
    recent_frames: Mapping[str, pd.DataFrame],
    *,
    horizon_hours: int = 168,
    tz: str = "UTC",
) -> Dict[str, pd.DataFrame]:
    """Produce dynamic long-range forecasts for each configured location."""
    outputs: Dict[str, pd.DataFrame] = {}
    if horizon_hours <= 0:
        return outputs
    for location, frame in recent_frames.items():
        if frame is None or frame.empty:
            continue
        working = _coerce_timestamp_frame(frame)
        if working.empty:
            continue
        feature_tail = working[artifacts.feature_columns].tail(1).copy()
        if feature_tail.empty:
            continue
        feature_tail = feature_tail.ffill(axis=0).bfill(axis=0)
        replicated = pd.concat([feature_tail] * horizon_hours, ignore_index=True)
        predictions = artifacts.model.predict(replicated)
        last_ts = working["timestamp"].iloc[-1]
        if pd.isna(last_ts):
            continue
        if last_ts.tzinfo is None:
            last_ts = last_ts.tz_localize("UTC")
        timestamps = pd.date_range(
            last_ts.tz_convert(tz) + pd.Timedelta(hours=1),
            periods=horizon_hours,
            freq="H",
            tz=tz,
        )
        outputs[location] = pd.DataFrame(
            {
                "timestamp": timestamps,
                artifacts.target_column: predictions,
                "location": location,
                "model_rmse": artifacts.rmse,
            }
        )
    return outputs


def detect_dynamic_anomalies(
    artifacts: ForecastArtifacts,
    *,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """Detect residual anomalies from the dynamic training frame."""
    frame = artifacts.training_frame
    if frame is None or frame.empty:
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
    features = frame[artifacts.feature_columns].astype(float)
    target = frame[artifacts.target_column].astype(float)
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
    anomalies = frame.loc[mask, ["timestamp", "location", artifacts.target_column]].copy()
    anomalies.rename(columns={artifacts.target_column: "observed"}, inplace=True)
    anomalies["predicted"] = predictions[mask]
    anomalies["z_score"] = z_scores[mask]
    anomalies["message"] = [
        f"Deviation of {abs(z):.2f}σ for {artifacts.target_column}" for z in anomalies["z_score"]
    ]
    return anomalies.reset_index(drop=True)

