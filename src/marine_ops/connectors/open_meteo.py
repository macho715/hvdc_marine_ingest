# KR: Open-Meteo API 연동
# EN: Open-Meteo API connector

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo

from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
from src.marine_ops.core.units import normalize_to_si

class OpenMeteoConnector:
    """Open-Meteo API 커넥터 (무료)"""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"
        self.session = requests.Session()
    
    def get_marine_weather(
        self, 
        lat: float, 
        lon: float, 
        start: datetime, 
        end: datetime,
        location: str = "AGI"
    ) -> MarineTimeseries:
        """해양 날씨 데이터 조회"""
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start.date().isoformat(),
            'end_date': end.date().isoformat(),
            'hourly': 'wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility',
            'timezone': 'Asia/Dubai'
        }
        
        try:
            response = self.session.get(f"{self.base_url}/forecast", params=params)
            response.raise_for_status()
            data = response.json()
            
            data_points = []
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            
            for i, time_str in enumerate(times):
                raw_data = {
                    'wind_speed': hourly.get('wind_speed_10m', [0])[i],
                    'wind_direction': hourly.get('wind_direction_10m', [0])[i],
                    'wind_gust': hourly.get('wind_gusts_10m', [None])[i],
                    'wave_height': 0.0,  # Open-Meteo 일반 API에서는 파고 데이터 없음
                    'visibility': hourly.get('visibility', [None])[i],
                    'wind_unit': 'ms'  # Open-Meteo returns m/s
                }
                
                # SI 단위로 정규화 (이미 m/s이지만 일관성을 위해)
                normalized = normalize_to_si(raw_data, 'open_meteo')
                
                data_point = MarineDataPoint(
                    timestamp=time_str,
                    wind_speed=normalized['wind_speed'],
                    wind_direction=normalized['wind_direction'],
                    wind_gust=normalized.get('wind_gust'),
                    wave_height=normalized['wave_height'],
                    visibility=normalized.get('visibility')
                )
                data_points.append(data_point)
            
            return MarineTimeseries(
                source="open_meteo",
                location=location,
                data_points=data_points,
                ingested_at=datetime.now().isoformat(),
                confidence=0.75
            )
        
        except requests.RequestException as e:
            raise Exception(f"Open-Meteo API error: {e}")

# AGI와 DAS 위치 정보
LOCATIONS = {
    'AGI': {'lat': 25.2111, 'lon': 54.1578},  # Al Ghallan Island
    'DAS': {'lat': 24.8667, 'lon': 53.7333}   # Das Island
}
