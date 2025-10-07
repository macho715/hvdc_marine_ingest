"""KR: GitHub Actions용 오프라인 지원 유틸 / EN: Offline support utilities for GitHub Actions."""
from __future__ import annotations

import os
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Sequence, Tuple

from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries


def decide_execution_mode(requested_mode: str, missing_secrets: Sequence[str], ncm_available: bool) -> Tuple[str, List[str]]:
    """KR: 실행 모드 결정 / EN: Decide execution mode."""

    normalized = requested_mode.lower()
    if normalized not in {"auto", "online", "offline"}:
        raise ValueError(f"지원하지 않는 실행 모드입니다: {requested_mode}")

    reasons: List[str] = []

    if normalized == "offline":
        reasons.append("사용자 지정 오프라인 모드")
        return "offline", reasons

    if normalized == "online":
        return "online", reasons

    if os.getenv("CI", "").lower() == "true":
        reasons.append("CI 환경 자동 전환")

    if missing_secrets:
        reasons.append(f"필수 시크릿 누락: {', '.join(missing_secrets)}")

    if not ncm_available:
        reasons.append("NCM Selenium 모듈 미로드")

    resolved_mode = "offline" if reasons else "online"
    return resolved_mode, reasons


def generate_offline_dataset(location: str, forecast_hours: int) -> Tuple[List[MarineTimeseries], Dict[str, Dict[str, float]]]:
    """KR: 합성 해양 시계열 생성 / EN: Generate synthetic marine timeseries."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    data_points: List[MarineDataPoint] = []

    for hour in range(max(forecast_hours, 6)):
        timestamp = now + timedelta(hours=hour)
        phase = hour / 6.0
        wind_speed = 8.5 + 1.8 * math.sin(phase)
        wind_direction = (120 + 20 * math.cos(phase * 0.8)) % 360
        wind_gust = wind_speed * 1.15
        wave_height = 0.6 + 0.25 * math.sin(phase + 0.6)
        wave_period = 7.5 + 0.4 * math.cos(phase)
        visibility = 11.0 - 0.8 * math.sin(phase * 0.5)
        temperature = 27.0 - 0.6 * math.cos(phase * 0.9)
        sea_state = "Slight" if wave_height < 1.0 else "Moderate"

        data_points.append(
            MarineDataPoint(
                timestamp=timestamp.isoformat(),
                wind_speed=round(wind_speed, 2),
                wind_direction=round(wind_direction, 2),
                wave_height=round(wave_height, 2),
                wind_gust=round(wind_gust, 2),
                wave_period=round(wave_period, 2),
                wave_direction=round((wind_direction + 5) % 360, 2),
                sea_state=sea_state,
                visibility=round(max(4.0, visibility), 2),
                temperature=round(temperature, 2),
                confidence=0.7,
            )
        )

    synthetic_series = MarineTimeseries(
        source="synthetic_offline",
        location=location,
        data_points=data_points,
        ingested_at=datetime.now(timezone.utc).isoformat(),
        confidence=0.7,
    )

    statuses: Dict[str, Dict[str, float]] = {
        "STORMGLASS": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
        "OPEN_METEO": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
        "NCM_SELENIUM": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
        "WORLDTIDES": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
        "SYNTHETIC": {"status": "✅ 오프라인 합성 데이터", "confidence": synthetic_series.confidence or 0.7},
    }

    return [synthetic_series], statuses
