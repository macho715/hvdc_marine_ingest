"""Daypart summarisation and decision logic."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from zoneinfo import ZoneInfo

from src.marine_ops.pipeline.config import PipelineConfig

DAYPART_DEFINITION: List[Tuple[str, int, int]] = [
    ("dawn", 3, 6),
    ("morning", 6, 12),
    ("afternoon", 12, 17),
    ("evening", 17, 22),
]


@dataclass(frozen=True)
class DaypartMetrics:
    label: str
    start: pd.Timestamp
    end: pd.Timestamp
    count: int
    hs_mean: float | None
    hs_p90: float | None
    tp_mean: float | None
    swell_dir_mean: float | None
    swell_period_mean: float | None
    wind_mean_kt: float | None
    wind_p90_kt: float | None
    wind_dir_mean: float | None
    visibility_mean_km: float | None


def _quantile(series: pd.Series, q: float) -> float | None:
    if series is None:
        return None
    valid = series.dropna()
    if valid.empty:
        return None
    return float(valid.quantile(q))


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


def _mean(series: pd.Series) -> float | None:
    if series is None:
        return None
    valid = series.dropna()
    if valid.empty:
        return None
    return float(valid.mean())


def summarize_dayparts(df: pd.DataFrame, tz: str) -> Dict[str, Dict[str, DaypartMetrics]]:
    if df.empty:
        return {}

    localized = df.copy()
    if localized.index.tzinfo is None:
        localized.index = localized.index.tz_localize(ZoneInfo(tz))
    else:
        localized.index = localized.index.tz_convert(ZoneInfo(tz))

    summaries: Dict[str, Dict[str, DaypartMetrics]] = {}
    day_groups = list(localized.index.normalize().unique())
    for offset, day_start in enumerate(sorted(day_groups)[:3]):
        day_label = f"D+{offset}"
        summaries[day_label] = {}
        for name, start_hour, end_hour in DAYPART_DEFINITION:
            slot_start = day_start + pd.Timedelta(hours=start_hour)
            slot_end = day_start + pd.Timedelta(hours=end_hour)
            mask = (localized.index >= slot_start) & (localized.index < slot_end)
            slot = localized.loc[mask]
            summaries[day_label][name] = DaypartMetrics(
                label=name,
                start=slot_start,
                end=slot_end,
                count=len(slot),
                hs_mean=_mean(slot.get("wave_height")),
                hs_p90=_quantile(slot.get("wave_height"), 0.9),
                tp_mean=_mean(slot.get("wave_period")),
                swell_dir_mean=_circular_mean(slot.get("swell_wave_direction")),
                swell_period_mean=_mean(slot.get("swell_wave_period")),
                wind_mean_kt=_mean(slot.get("wind_speed_kt")),
                wind_p90_kt=_quantile(slot.get("wind_gusts_kt"), 0.9)
                if "wind_gusts_kt" in slot else _quantile(slot.get("wind_speed_kt"), 0.9),
                wind_dir_mean=_circular_mean(slot.get("wind_direction_10m")),
                visibility_mean_km=_mean(slot.get("visibility_km")),
            )
    return summaries


def _classify_sea_state(hs: float | None, thresholds: Dict[str, float]) -> str:
    if hs is None:
        return "Unknown"
    if hs <= thresholds.get("slight", 1.25):
        return "Slight"
    if hs <= thresholds.get("moderate", 2.5):
        return "Moderate"
    if hs <= thresholds.get("rough", 4.0):
        return "Rough"
    return "Very Rough"


def _apply_gamma(alerts: Iterable[str], weights: Dict[str, float]) -> Tuple[float, List[str]]:
    gamma = 0.0
    matched: List[str] = []
    for alert in alerts:
        key = alert.lower()
        if key in weights:
            gamma += weights[key]
            matched.append(alert)
    return gamma, matched


def decide_dayparts(
    summary: Dict[str, Dict[str, DaypartMetrics]],
    config: PipelineConfig,
    ncm_alerts: Iterable[str],
) -> Dict[str, Dict[str, Dict[str, object]]]:
    alerts_lower = [alert.lower() for alert in ncm_alerts]
    decisions: Dict[str, Dict[str, Dict[str, object]]] = {}

    go_gate = config.gate_thresholds.get("go", {"hs_m": 1.0, "wind_kt": 20.0})
    cond_gate = config.gate_thresholds.get("conditional", {"hs_m": 1.2, "wind_kt": 22.0})

    for day_label, parts in summary.items():
        decisions[day_label] = {}
        for name, metrics in parts.items():
            entry = {
                "start": metrics.start.isoformat(),
                "end": metrics.end.isoformat(),
                "count": metrics.count,
                "hs_mean": metrics.hs_mean,
                "hs_p90": metrics.hs_p90,
                "tp_mean": metrics.tp_mean,
                "swell_dir_mean": metrics.swell_dir_mean,
                "swell_period_mean": metrics.swell_period_mean,
                "wind_mean_kt": metrics.wind_mean_kt,
                "wind_p90_kt": metrics.wind_p90_kt,
                "wind_dir_mean": metrics.wind_dir_mean,
                "visibility_mean_km": metrics.visibility_mean_km,
            }
            sea_state = _classify_sea_state(metrics.hs_p90 or metrics.hs_mean, config.sea_state_thresholds)
            entry["sea_state"] = sea_state

            hs_ref = metrics.hs_p90 or metrics.hs_mean or 0.0
            wind_ref = metrics.wind_p90_kt or metrics.wind_mean_kt or 0.0

            decision = "UNKNOWN"
            if metrics.count == 0:
                decision = "DATA-MISS"
            else:
                if hs_ref <= go_gate.get("hs_m", 1.0) and wind_ref <= go_gate.get("wind_kt", 20.0):
                    decision = "GO"
                elif hs_ref <= cond_gate.get("hs_m", 1.2) and wind_ref <= cond_gate.get("wind_kt", 22.0):
                    decision = "CONDITIONAL"
                else:
                    decision = "NO-GO"

            gamma, matched_alerts = _apply_gamma(alerts_lower, config.alert_weights)
            entry["gamma"] = gamma
            entry["alerts_matched"] = matched_alerts

            if config.alert_fog_no_go and any("fog" in alert for alert in alerts_lower):
                decision = "NO-GO"

            entry["decision"] = decision
            entry["buffer_minutes"] = 0 if decision == "GO" else 45 if decision == "CONDITIONAL" else 120
            decisions[day_label][name] = entry
    return decisions


def route_window(
    agi: Dict[str, Dict[str, Dict[str, object]]],
    das: Dict[str, Dict[str, Dict[str, object]]],
    allowed: Iterable[str] | None = None,
) -> List[Dict[str, object]]:
    allowed_set = set(allowed or {"GO", "CONDITIONAL"})
    windows: List[Dict[str, object]] = []
    for day_label, agi_parts in agi.items():
        das_parts = das.get(day_label, {})
        for name, agi_entry in agi_parts.items():
            das_entry = das_parts.get(name)
            if not das_entry:
                continue
            if agi_entry.get("decision") in allowed_set and das_entry.get("decision") in allowed_set:
                windows.append(
                    {
                        "label": f"{day_label} {name}",
                        "start": agi_entry.get("start"),
                        "end": agi_entry.get("end"),
                        "agi_decision": agi_entry.get("decision"),
                        "das_decision": das_entry.get("decision"),
                        "buffer_minutes": max(
                            agi_entry.get("buffer_minutes", 0),
                            das_entry.get("buffer_minutes", 0),
                        ),
                    }
                )
    return windows
