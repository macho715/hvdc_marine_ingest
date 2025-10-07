# KR: Open-Meteo API ����
# EN: Open-Meteo API connector

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries
from src.marine_ops.core.units import normalize_to_si

MARINE_BASE_URL = "https://marine-api.open-meteo.com/v1/marine"
FORECAST_BASE_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class OpenMeteoResult:
    """Structured response used by the extended pipeline."""

    dataframe: pd.DataFrame
    metadata: Dict[str, Any]


class OpenMeteoConnector:
    """Open-Meteo API connector."""

    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"
        self.session = requests.Session()

    def get_marine_weather(
        self,
        lat: float,
        lon: float,
        start: datetime,
        end: datetime,
        location: str = "AGI",
    ) -> MarineTimeseries:
        """Legacy helper returning MarineTimeseries for backward compatibility."""

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start.date().isoformat(),
            "end_date": end.date().isoformat(),
            "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility",
            "timezone": "Asia/Dubai",
        }

        response = self.session.get(f"{self.base_url}/forecast", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        data_points: List[MarineDataPoint] = []
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        for i, time_str in enumerate(times):
            raw_data = {
                "wind_speed": hourly.get("wind_speed_10m", [0])[i],
                "wind_direction": hourly.get("wind_direction_10m", [0])[i],
                "wind_gust": hourly.get("wind_gusts_10m", [None])[i],
                "wave_height": 0.0,  # Placeholder: general forecast API lacks wave height
                "visibility": hourly.get("visibility", [None])[i],
                "wind_unit": "ms",  # Open-Meteo returns m/s
            }

            normalized = normalize_to_si(raw_data, "open_meteo")

            data_points.append(
                MarineDataPoint(
                    timestamp=time_str,
                    wind_speed=normalized["wind_speed"],
                    wind_direction=normalized["wind_direction"],
                    wind_gust=normalized.get("wind_gust"),
                    wave_height=normalized["wave_height"],
                    visibility=normalized.get("visibility"),
                    confidence=0.75,
                )
            )

        return MarineTimeseries(
            source="open_meteo",
            location=location,
            data_points=data_points,
            ingested_at=datetime.now(timezone.utc).isoformat(),
            confidence=0.75,
        )


def _fetch_open_meteo_dataframe(
    base_url: str,
    lat: float,
    lon: float,
    hours: int,
    hourly_vars: List[str],
    tz: str,
    extra_params: Dict[str, Any] | None = None,
) -> OpenMeteoResult:
    if hours <= 0:
        raise ValueError("forecast hours must be positive")

    params: Dict[str, Any] = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(hourly_vars),
        "timezone": tz,
    }
    if hours <= 168:
        params["forecast_hours"] = hours
    else:
        params["forecast_days"] = min(16, int((hours + 23) / 24))

    if extra_params:
        params.update(extra_params)

    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "hourly" not in payload:
        raise RuntimeError(f"Open-Meteo response missing 'hourly': {payload}")

    hourly = payload["hourly"]
    times = hourly.get("time", [])
    if not times:
        raise RuntimeError("Open-Meteo hourly response contains no timestamps")

    df = pd.DataFrame({var: hourly.get(var, []) for var in hourly_vars}, index=pd.to_datetime(times))
    if df.empty:
        raise RuntimeError("Open-Meteo returned empty dataframe")

    df.index = df.index.tz_localize(ZoneInfo(tz)) if df.index.tzinfo is None else df.index.tz_convert(tz)
    df.sort_index(inplace=True)

    return OpenMeteoResult(
        dataframe=df,
        metadata={
            "latitude": payload.get("latitude", lat),
            "longitude": payload.get("longitude", lon),
            "elevation": payload.get("elevation"),
            "units": payload.get("hourly_units", {}),
            "start": df.index[0].isoformat(),
            "end": df.index[-1].isoformat(),
        },
    )


def fetch_open_meteo_marine(
    lat: float,
    lon: float,
    hours: int,
    hourly: List[str],
    tz: str = "Asia/Dubai",
    cell_selection: str | None = None,
) -> OpenMeteoResult:
    extra: Dict[str, Any] = {}
    if cell_selection:
        extra["cell_selection"] = cell_selection
    return _fetch_open_meteo_dataframe(
        MARINE_BASE_URL,
        lat=lat,
        lon=lon,
        hours=hours,
        hourly_vars=hourly,
        tz=tz,
        extra_params=extra,
    )


def fetch_open_meteo_weather(
    lat: float,
    lon: float,
    hours: int,
    hourly: List[str],
    tz: str = "Asia/Dubai",
) -> OpenMeteoResult:
    extra = {"forecast_model": "ecmwf_ifs04"}
    return _fetch_open_meteo_dataframe(
        FORECAST_BASE_URL,
        lat=lat,
        lon=lon,
        hours=hours,
        hourly_vars=hourly,
        tz=tz,
        extra_params=extra,
    )


# Legacy constants used by other scripts
LOCATIONS = {
    "AGI": {"lat": 25.2111, "lon": 54.1578},
    "DAS": {"lat": 24.8667, "lon": 53.7333},
}
