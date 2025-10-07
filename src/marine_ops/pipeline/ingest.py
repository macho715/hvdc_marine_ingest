"""Data ingestion utilities for the 72-hour marine pipeline."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.marine_ops.connectors.open_meteo import (
    OpenMeteoResult,
    fetch_open_meteo_marine,
    fetch_open_meteo_weather,
)
from src.marine_ops.connectors.stormglass import StormglassConnector
from src.marine_ops.connectors.worldtides import create_marine_timeseries_from_worldtides
from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries
from src.marine_ops.pipeline.config import LocationSpec, PipelineConfig

KT_PER_MS = 1.9438444924406


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):  # type: ignore[arg-type]
            return None
    except TypeError:
        pass
    return float(value)


def _merge_marine_weather(
    marine: OpenMeteoResult | None,
    weather: OpenMeteoResult | None,
    tz: str,
) -> pd.DataFrame:
    frames = []
    if marine is not None:
        frames.append(marine.dataframe)
    if weather is not None:
        frames.append(weather.dataframe)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, axis=1)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep="first")]
    df = df.tz_convert(tz)
    if "wind_speed_10m" in df:
        df["wind_speed_kt"] = df["wind_speed_10m"] * KT_PER_MS
    if "wind_gusts_10m" in df:
        df["wind_gusts_kt"] = df["wind_gusts_10m"] * KT_PER_MS
    if "visibility" in df:
        df["visibility_km"] = df["visibility"] * 0.001
    return df


def _dataframe_to_timeseries(location: str, df: pd.DataFrame) -> MarineTimeseries:
    data_points: List[MarineDataPoint] = []
    for ts, row in df.iterrows():
        timestamp = ts.tz_convert(timezone.utc).isoformat()
        data_points.append(
            MarineDataPoint(
                timestamp=timestamp,
                wind_speed=_safe_float(row.get("wind_speed_10m")) or 0.0,
                wind_direction=_safe_float(row.get("wind_direction_10m")) or 0.0,
                wind_gust=_safe_float(row.get("wind_gusts_10m")),
                wave_height=_safe_float(row.get("wave_height")) or 0.0,
                wave_period=_safe_float(row.get("wave_period")),
                wave_direction=_safe_float(row.get("wave_direction")),
                swell_wave_height=_safe_float(row.get("swell_wave_height")),
                swell_wave_period=_safe_float(row.get("swell_wave_period")),
                swell_wave_direction=_safe_float(row.get("swell_wave_direction")),
                wind_wave_height=_safe_float(row.get("wind_wave_height")),
                wind_wave_period=_safe_float(row.get("wind_wave_period")),
                wind_wave_direction=_safe_float(row.get("wind_wave_direction")),
                ocean_current_speed=_safe_float(row.get("ocean_current_velocity")),
                sea_surface_temperature=_safe_float(row.get("sea_surface_temperature")),
                visibility=_safe_float(row.get("visibility_km")),
            )
        )
    return MarineTimeseries(
        source="open_meteo_fused",
        location=location,
        data_points=data_points,
        ingested_at=datetime.now(timezone.utc).isoformat(),
        confidence=0.75,
    )


def _try_stormglass(loc: LocationSpec, hours: int) -> Tuple[MarineTimeseries | None, str]:
    api_key = os.getenv("STORMGLASS_API_KEY")
    if not api_key:
        return None, "skipped (missing STORMGLASS_API_KEY)"
    connector = StormglassConnector(api_key=api_key)
    try:
        start = datetime.now(timezone.utc)
        end = start + pd.Timedelta(hours=hours)
        series = connector.get_marine_weather(loc.lat, loc.lon, start, end, location=loc.id)
        return series, "ok"
    except Exception as exc:  # pragma: no cover - network path
        return None, f"error: {exc}"


def _try_worldtides(loc: LocationSpec, hours: int) -> Tuple[MarineTimeseries | None, str]:
    api_key = os.getenv("WORLDTIDES_API_KEY")
    if not api_key:
        return None, "skipped (missing WORLDTIDES_API_KEY)"
    try:
        series = create_marine_timeseries_from_worldtides(
            lat=loc.lat,
            lon=loc.lon,
            api_key=api_key,
            location=loc.id,
            forecast_hours=hours,
        )
        return series, "ok"
    except Exception as exc:  # pragma: no cover - network path
        return None, f"error: {exc}"


NCM_URL = "https://albahar.ncm.gov.ae/marine-observations?lang=en"
_ALERT_KEYWORDS = ("rough at times", "high seas", "fog")


def fetch_ncm_alerts(timeout: int = 20) -> Dict[str, List[str] | str]:
    try:
        resp = requests.get(NCM_URL, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = " ".join(soup.stripped_strings).lower()
        alerts = [keyword for keyword in _ALERT_KEYWORDS if keyword in text]
        return {"status": "ok", "alerts": alerts, "raw_text": text[:5000]}
    except Exception as exc:  # pragma: no cover - network path
        return {"status": f"error: {exc}", "alerts": [], "raw_text": ""}


def collect_weather_data_3d(
    config: PipelineConfig,
    mode: str = "auto",
) -> Dict[str, object]:
    """Collect 72-hour marine and weather timeseries for all configured locations."""

    per_location: Dict[str, Dict[str, object]] = {}
    per_location_series: Dict[str, Dict[str, MarineTimeseries]] = {}
    api_status: Dict[str, Dict[str, str]] = {}

    for loc in config.locations:
        sources: Dict[str, object] = {}
        series_bucket: Dict[str, MarineTimeseries] = {}
        # Open-Meteo marine
        marine_result: OpenMeteoResult | None = None
        try:
            marine_result = fetch_open_meteo_marine(
                lat=loc.lat,
                lon=loc.lon,
                hours=config.forecast_hours,
                hourly=config.marine_vars or [
                    "wave_height",
                    "wind_wave_height",
                    "swell_wave_height",
                    "wave_period",
                    "wind_wave_period",
                    "swell_wave_period",
                    "wave_direction",
                    "wind_wave_direction",
                    "swell_wave_direction",
                    "ocean_current_velocity",
                    "sea_surface_temperature",
                ],
                tz=config.tz,
                cell_selection="sea",
            )
            sources["open_meteo_marine"] = marine_result
            api_status.setdefault(loc.id, {})["open_meteo_marine"] = "ok"
        except Exception as exc:  # pragma: no cover - network path
            api_status.setdefault(loc.id, {})["open_meteo_marine"] = f"error: {exc}"

        # Open-Meteo weather (ECMWF)
        weather_result: OpenMeteoResult | None = None
        try:
            weather_result = fetch_open_meteo_weather(
                lat=loc.lat,
                lon=loc.lon,
                hours=config.forecast_hours,
                hourly=config.weather_vars or [
                    "wind_speed_10m",
                    "wind_gusts_10m",
                    "wind_direction_10m",
                    "visibility",
                ],
                tz=config.tz,
            )
            sources["open_meteo_weather"] = weather_result
            api_status.setdefault(loc.id, {})["open_meteo_weather"] = "ok"
        except Exception as exc:  # pragma: no cover - network path
            api_status.setdefault(loc.id, {})["open_meteo_weather"] = f"error: {exc}"

        # Merge to fused dataframe & convert to timeseries for ERI
        fused_df = _merge_marine_weather(marine_result, weather_result, config.tz)
        sources["fused_dataframe"] = fused_df
        series_bucket["open_meteo_fused"] = _dataframe_to_timeseries(loc.id, fused_df) if not fused_df.empty else MarineTimeseries(
            source="open_meteo_fused",
            location=loc.id,
            data_points=[],
            ingested_at=datetime.now(timezone.utc).isoformat(),
            confidence=0.1,
        )

        # Optional sources
        stormglass_ts, stormglass_status = _try_stormglass(loc, config.forecast_hours)
        api_status.setdefault(loc.id, {})["stormglass"] = stormglass_status
        if stormglass_ts is not None:
            series_bucket["stormglass"] = stormglass_ts

        worldtides_ts, worldtides_status = _try_worldtides(loc, config.forecast_hours)
        api_status.setdefault(loc.id, {})["worldtides"] = worldtides_status
        if worldtides_ts is not None:
            series_bucket["worldtides"] = worldtides_ts

        per_location[loc.id] = sources
        per_location_series[loc.id] = series_bucket

    ncm_info = fetch_ncm_alerts()

    return {
        "config": config,
        "sources": per_location,
        "timeseries": per_location_series,
        "api_status": api_status,
        "ncm_alerts": ncm_info.get("alerts", []),
        "ncm_raw": ncm_info,
        "mode": mode,
    }
