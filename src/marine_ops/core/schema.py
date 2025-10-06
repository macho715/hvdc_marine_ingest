# KR: 해양 데이터 표준 스키마 정의
# EN: Standard marine data schema definitions

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from zoneinfo import ZoneInfo

@dataclass
class MarineDataPoint:
    """단일 시점 해양 데이터 (확장됨)"""
    timestamp: str  # ISO8601 format
    wind_speed: float  # m/s
    wind_direction: float  # degrees
    wave_height: float  # m (Hs)
    wind_gust: Optional[float] = None  # m/s
    wave_period: Optional[float] = None  # s (Tp)
    wave_direction: Optional[float] = None  # degrees
    sea_state: Optional[str] = None
    visibility: Optional[float] = None  # km
    fog_probability: Optional[float] = None  # 0-1
    temperature: Optional[float] = None  # °C
    humidity: Optional[float] = None  # 0-1
    # 확장된 해양 변수들
    swell_wave_height: Optional[float] = None  # m
    swell_wave_period: Optional[float] = None  # s
    swell_wave_direction: Optional[float] = None  # degrees
    wind_wave_height: Optional[float] = None  # m
    wind_wave_period: Optional[float] = None  # s
    wind_wave_direction: Optional[float] = None  # degrees
    ocean_current_speed: Optional[float] = None  # m/s
    ocean_current_direction: Optional[float] = None  # degrees
    sea_surface_temperature: Optional[float] = None  # °C
    sea_level: Optional[float] = None  # m
    confidence: Optional[float] = None  # 0-1, 데이터 신뢰도

@dataclass
class MarineTimeseries:
    """해양 시계열 데이터"""
    source: str  # "stormglass", "worldtides", "open_meteo", "ncm"
    location: str  # "AGI", "DAS"
    data_points: List[MarineDataPoint]
    ingested_at: str  # ISO8601
    confidence: Optional[float] = None  # 0-1

@dataclass
class ERIPoint:
    """ERI 계산 결과"""
    timestamp: str
    eri_value: float  # 0-100
    wind_contribution: float
    wave_contribution: float
    visibility_contribution: float
    fog_contribution: float

@dataclass
class FusedForecast:
    """융합된 예보 데이터"""
    location: str
    timestamp: str
    wind_speed_fused: float  # m/s
    wave_height_fused: float  # m
    confidence: float  # 0-1
    sources_used: List[str]
    weights: Dict[str, float]

@dataclass
class OperationalDecision:
    """운항 판정 결과"""
    location: str
    timestamp: str
    decision: str  # "GO", "CONDITIONAL", "NO-GO"
    reasoning: str
    limiting_factor: Optional[str] = None
    eta_impact: Optional[str] = None
    gamma_alert: Optional[float] = None

@dataclass
class MarineReport:
    """최종 해양 보고서"""
    report_id: str
    generated_at: str
    locations: List[str]
    forecast_horizon: int  # hours
    decisions: List[OperationalDecision]
    fused_forecasts: List[FusedForecast]
    eri_timeseries: List[ERIPoint]
    warnings: List[str]
    metadata: Dict[str, Any]
