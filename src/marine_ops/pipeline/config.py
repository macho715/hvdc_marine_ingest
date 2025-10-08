"""Configuration helpers for the 72-hour marine pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass(frozen=True)
class LocationSpec:
    """Location metadata used by the extended pipeline."""

    id: str
    name: str
    lat: float
    lon: float
    description: str | None = None


@dataclass(frozen=True)
class PipelineConfig:
    """Top-level configuration for the 72-hour pipeline."""

    locations: List[LocationSpec]
    tz: str
    forecast_hours: int
    report_times: List[str]
    marine_vars: List[str]
    weather_vars: List[str]
    sea_state_thresholds: dict[str, float]
    gate_thresholds: dict[str, dict[str, float]]
    alert_weights: dict[str, float]
    alert_fog_no_go: bool
    ml_history_path: Optional[str] = None
    ml_model_cache: Optional[str] = None
    ml_sqlite_table: Optional[str] = None
    ml_feature_columns: Optional[List[str]] = None
    ml_target_column: Optional[str] = None
    ml_force_retrain: bool = False
    ml_forecast_horizon_hours: Optional[int] = None

    def location_ids(self) -> List[str]:
        return [loc.id for loc in self.locations]


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("locations.yaml must define a mapping")
    return data


def _coerce_locations(raw_locations) -> List[LocationSpec]:
    locations: List[LocationSpec] = []
    if isinstance(raw_locations, dict):
        iterable = raw_locations.items()
        for loc_id, payload in iterable:
            if not isinstance(payload, dict):
                raise ValueError("Location entries must be mappings")
            locations.append(
                LocationSpec(
                    id=str(payload.get("id", loc_id)),
                    name=str(payload.get("name", loc_id)),
                    lat=float(payload["lat"]),
                    lon=float(payload["lon"]),
                    description=payload.get("description"),
                )
            )
    elif isinstance(raw_locations, list):
        for entry in raw_locations:
            if not isinstance(entry, dict):
                raise ValueError("Location list must contain mappings")
            loc_id = str(entry.get("id") or entry.get("name"))
            if not loc_id:
                raise ValueError("Each location must define an 'id' or 'name'")
            locations.append(
                LocationSpec(
                    id=loc_id,
                    name=str(entry.get("name", loc_id)),
                    lat=float(entry["lat"]),
                    lon=float(entry["lon"]),
                    description=entry.get("description"),
                )
            )
    else:
        raise ValueError("locations must be a list or mapping")
    if not locations:
        raise ValueError("At least one location must be configured")
    return locations


def load_pipeline_config(path: str | Path = "config/locations.yaml") -> PipelineConfig:
    raw = _load_yaml(Path(path))
    locations = _coerce_locations(raw.get("locations", []))
    tz = str(raw.get("tz", "Asia/Dubai"))
    forecast_hours = int(raw.get("forecast_hours", 72))
    report_times = [str(item) for item in raw.get("report_times", ["06:00", "17:00"])]
    marine_vars = [str(var) for var in raw.get("marine_vars", [])]
    weather_vars = [str(var) for var in raw.get("weather_vars", [])]

    thresholds = raw.get("thresholds", {})
    sea_state_thresholds = thresholds.get("sea_state", {})
    gate_thresholds = thresholds.get("gate", {})

    alerts = raw.get("alerts", {})
    alert_weights = alerts.get("gamma_weights", {})
    alert_fog_no_go = bool(alerts.get("fog_no_go", True))

    ml_section = raw.get("ml", {})
    if ml_section is None:
        ml_section = {}
    if not isinstance(ml_section, dict):
        raise ValueError("ml section, if provided, must be a mapping")

    def _coalesce_ml_value(*keys, default=None):
        for key in keys:
            if key in raw:
                return raw.get(key)
            if key in ml_section:
                return ml_section.get(key)
        return default

    ml_history_path = _coalesce_ml_value("ml_history_path", "history_path")
    ml_model_cache = _coalesce_ml_value("ml_model_cache", "model_cache", "cache_path")
    ml_sqlite_table = _coalesce_ml_value("ml_sqlite_table", "sqlite_table")
    ml_feature_columns = _coalesce_ml_value("ml_feature_columns", "feature_columns")
    if ml_feature_columns is not None:
        if not isinstance(ml_feature_columns, list):
            raise ValueError("ml_feature_columns must be a list when provided")
        ml_feature_columns = [str(col) for col in ml_feature_columns]
    ml_target_column = _coalesce_ml_value("ml_target_column", "target_column")
    ml_force_retrain = bool(_coalesce_ml_value("ml_force_retrain", "force_retrain", default=False))
    ml_forecast_horizon_hours = _coalesce_ml_value("ml_forecast_horizon_hours", "forecast_horizon_hours")
    if ml_forecast_horizon_hours is not None:
        ml_forecast_horizon_hours = int(ml_forecast_horizon_hours)

    return PipelineConfig(
        locations=locations,
        tz=tz,
        forecast_hours=forecast_hours,
        report_times=report_times,
        marine_vars=marine_vars,
        weather_vars=weather_vars,
        sea_state_thresholds={str(k): float(v) for k, v in sea_state_thresholds.items()},
        gate_thresholds={region: {key: float(value) for key, value in params.items()} for region, params in gate_thresholds.items()},
        alert_weights={str(k).lower(): float(v) for k, v in alert_weights.items()},
        alert_fog_no_go=alert_fog_no_go,
        ml_history_path=str(ml_history_path) if ml_history_path else None,
        ml_model_cache=str(ml_model_cache) if ml_model_cache else None,
        ml_sqlite_table=str(ml_sqlite_table) if ml_sqlite_table else None,
        ml_feature_columns=ml_feature_columns,
        ml_target_column=str(ml_target_column) if ml_target_column else None,
        ml_force_retrain=ml_force_retrain,
        ml_forecast_horizon_hours=ml_forecast_horizon_hours,
    )
