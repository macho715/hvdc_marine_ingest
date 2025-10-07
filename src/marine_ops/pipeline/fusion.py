"""Forecast fusion utilities for the 72-hour pipeline."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

import numpy as np
import pandas as pd

from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries

KT_PER_MS = 1.9438444924406
KM_PER_M = 0.001


def _nan_to_none(value):
    if value is None:
        return None
    try:
        if pd.isna(value):  # type: ignore[arg-type]
            return None
    except TypeError:
        pass
    return float(value)


def _dataframe_to_timeseries(location: str, df: pd.DataFrame) -> MarineTimeseries:
    data_points: list[MarineDataPoint] = []
    for ts, row in df.iterrows():
        timestamp = ts.tz_convert(timezone.utc).isoformat()
        data_points.append(
            MarineDataPoint(
                timestamp=timestamp,
                wind_speed=_nan_to_none(row.get("wind_speed_10m")) or 0.0,
                wind_direction=_nan_to_none(row.get("wind_direction_10m")) or 0.0,
                wind_gust=_nan_to_none(row.get("wind_gusts_10m")),
                wave_height=_nan_to_none(row.get("wave_height")) or 0.0,
                wave_period=_nan_to_none(row.get("wave_period")),
                wave_direction=_nan_to_none(row.get("wave_direction")),
                swell_wave_height=_nan_to_none(row.get("swell_wave_height")),
                swell_wave_period=_nan_to_none(row.get("swell_wave_period")),
                swell_wave_direction=_nan_to_none(row.get("swell_wave_direction")),
                wind_wave_height=_nan_to_none(row.get("wind_wave_height")),
                wind_wave_period=_nan_to_none(row.get("wind_wave_period")),
                wind_wave_direction=_nan_to_none(row.get("wind_wave_direction")),
                ocean_current_speed=_nan_to_none(row.get("ocean_current_velocity")),
                sea_surface_temperature=_nan_to_none(row.get("sea_surface_temperature")),
                visibility=_nan_to_none(row.get("visibility_km")),
            )
        )
    return MarineTimeseries(
        source="fused",
        location=location,
        data_points=data_points,
        ingested_at=datetime.now(timezone.utc).isoformat(),
        confidence=0.75,
    )


def _circular_mean(series: pd.Series) -> float | None:
    if series is None:
        return None
    valid = series.dropna()
    if valid.empty:
        return None
    radians = np.deg2rad(valid.to_numpy())
    sin_mean = np.sin(radians).mean()
    cos_mean = np.cos(radians).mean()
    angle = np.degrees(np.arctan2(sin_mean, cos_mean))
    return (angle + 360.0) % 360.0


def fuse_timeseries_3d(
    sources: Dict[str, Dict[str, object]],
) -> Dict[str, object]:
    """Fuse multiple source dataframes into a single view per location."""

    frames: Dict[str, pd.DataFrame] = {}
    timeseries_map: Dict[str, MarineTimeseries] = {}
    weights: Dict[str, Dict[str, float]] = {}

    for location, source_map in sources.items():
        collected_frames: list[tuple[str, pd.DataFrame]] = []
        for source_name, payload in source_map.items():
            if source_name == "fused_dataframe":
                continue
            if isinstance(payload, pd.DataFrame):
                collected_frames.append((source_name, payload))
            elif hasattr(payload, "dataframe"):
                df = getattr(payload, "dataframe")
                if isinstance(df, pd.DataFrame):
                    collected_frames.append((source_name, df))
        if not collected_frames:
            frames[location] = pd.DataFrame()
            timeseries_map[location] = MarineTimeseries(
                source="empty",
                location=location,
                data_points=[],
                ingested_at=datetime.now(timezone.utc).isoformat(),
                confidence=0.0,
            )
            weights[location] = {}
            continue

        merged = pd.concat([frame for _, frame in collected_frames], axis=1)
        merged = merged.loc[:, ~merged.columns.duplicated()].copy()
        merged.sort_index(inplace=True)
        merged = merged[~merged.index.duplicated(keep="first")]
        if merged.index.tzinfo is None:
            merged.index = merged.index.tz_localize("UTC")

        if "wind_speed_10m" in merged.columns:
            merged["wind_speed_kt"] = merged["wind_speed_10m"] * KT_PER_MS
        if "wind_gusts_10m" in merged.columns:
            merged["wind_gusts_kt"] = merged["wind_gusts_10m"] * KT_PER_MS
        if "visibility" in merged.columns:
            merged["visibility_km"] = merged["visibility"] * KM_PER_M
        if "swell_wave_direction" in merged.columns:
            merged["swell_wave_direction_mean"] = _circular_mean(merged["swell_wave_direction"])
        if "wind_wave_direction" in merged.columns:
            merged["wind_wave_direction_mean"] = _circular_mean(merged["wind_wave_direction"])

        frames[location] = merged
        timeseries_map[location] = _dataframe_to_timeseries(location, merged)

        base_weight = 1.0 / len(collected_frames)
        weights[location] = {source_name: base_weight for source_name, _ in collected_frames}

    return {
        "frames": frames,
        "timeseries": timeseries_map,
        "weights": weights,
    }
