# KR: Stormglass API 연동
# EN: Stormglass API connector

import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo

from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
from src.marine_ops.core.units import normalize_to_si

class StormglassConnector:
    """Stormglass API 커넥터"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('STORMGLASS_API_KEY')
        self.base_url = "https://api.stormglass.io/v2"
        self.session = requests.Session()
        self.session.headers.update({'Authorization': self.api_key})
    
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
            'lat': lat,
            'lng': lon,
            'start': start.strftime('%Y-%m-%d'),
            'end': end.strftime('%Y-%m-%d'),
            'params': 'windSpeed,windDirection,waveHeight,wavePeriod,visibility',
            'source': 'noaa'
        }
        
        try:
            response = self.session.get(f"{self.base_url}/weather/point", params=params)
            response.raise_for_status()
            data = response.json()
            
            data_points = []
            for hour_data in data.get('hours', []):
                raw_data = {
                    'wind_speed': hour_data.get('windSpeed', {}).get('noaa', 0),
                    'wind_direction': hour_data.get('windDirection', {}).get('noaa', 0),
                    'wave_height': hour_data.get('waveHeight', {}).get('noaa', 0),
                    'wave_period': hour_data.get('wavePeriod', {}).get('noaa'),
                    'visibility': hour_data.get('visibility', {}).get('noaa'),
                    'wind_unit': 'ms',  # Stormglass NOAA source returns m/s
                    'wave_unit': 'm'    # Stormglass returns meters
                }
                
                # SI 단위로 정규화
                normalized = normalize_to_si(raw_data, 'stormglass')
                
                data_point = MarineDataPoint(
                    timestamp=hour_data['time'],
                    wind_speed=normalized['wind_speed'],
                    wind_direction=normalized['wind_direction'],
                    wave_height=normalized['wave_height'],
                    wave_period=normalized.get('wave_period'),
                    visibility=normalized.get('visibility'),
                    confidence=0.85  # Stormglass NOAA 데이터 신뢰도
                )
                data_points.append(data_point)
            
            return MarineTimeseries(
                source="stormglass",
                location=location,
                data_points=data_points,
                ingested_at=datetime.now().isoformat(),
                confidence=0.85
            )
        
        except requests.RequestException as e:
            raise Exception(f"Stormglass API error: {e}")

# AGI와 DAS 위치 정보
LOCATIONS = {
    'AGI': {'lat': 25.2111, 'lon': 54.1578},  # Al Ghallan Island
    'DAS': {'lat': 24.8667, 'lon': 53.7333}   # Das Island
}
