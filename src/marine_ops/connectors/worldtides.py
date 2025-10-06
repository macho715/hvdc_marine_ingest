# src/marine_ops/connectors/worldtides.py
import httpx
from typing import Dict, Any, List
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
from src.marine_ops.core.units import normalize_to_si

WT = "https://www.worldtides.info/api/v3"

def fetch_worldtides_heights(lat: float, lon: float, key: str, hours: int = 72) -> Dict[str, Any]:
    """Return tide heights (30-min resolution where available)."""
    params = {"heights": "", "lat": lat, "lon": lon, "key": key, "duration": hours}
    r = httpx.get(WT, params=params, timeout=20)
    
    # API 응답 상태 확인
    if r.status_code == 400:
        error_data = r.json()
        if "Not enough credits" in error_data.get("error", ""):
            print(f"[WorldTides] 크레딧 부족: {error_data.get('error')}")
            raise Exception(f"WorldTides API 크레딧 부족: {error_data.get('error')}")
        else:
            print(f"[WorldTides] API 오류: {error_data}")
            raise Exception(f"WorldTides API 오류: {error_data.get('error', 'Unknown error')}")
    
    r.raise_for_status()
    return r.json()

def create_marine_timeseries_from_worldtides(
    lat: float, 
    lon: float, 
    api_key: str, 
    location: str = "AGI",
    forecast_hours: int = 72
) -> MarineTimeseries:
    """WorldTides API에서 해양 시계열 데이터 생성"""
    
    try:
        print(f"[WorldTides] 조석 데이터 수집 중: lat={lat}, lon={lon}")
        
        # WorldTides API 호출
        data = fetch_worldtides_heights(lat, lon, api_key, forecast_hours)
        
        data_points = []
        
        # 조석 높이 데이터 처리
        if 'heights' in data:
            for height_data in data['heights']:
                timestamp = height_data['dt']
                tide_height = height_data['height']  # 미터 단위
                
                # ISO8601 형식으로 변환
                if isinstance(timestamp, (int, float)):
                    dt = datetime.fromtimestamp(timestamp)
                    timestamp = dt.isoformat()
                
                # MarineDataPoint 생성 (조석 높이만)
                data_point = MarineDataPoint(
                    timestamp=timestamp,
                    wind_speed=0.0,  # WorldTides는 조석 데이터만 제공
                    wind_direction=0.0,
                    wave_height=0.0,
                    sea_state="Unknown",  # 조석 데이터로는 파도 상태 추정 불가
                    confidence=0.8  # WorldTides 조석 데이터 신뢰도
                )
                data_points.append(data_point)
        
        # 조석 데이터가 없는 경우 기본 구조 반환
        if not data_points:
            print("[WorldTides] 조석 데이터 없음, 폴백 데이터 생성")
            data_points = _create_fallback_tide_data(location, forecast_hours)
        
        return MarineTimeseries(
            source="worldtides",
            location=location,
            data_points=data_points,
            ingested_at=datetime.now().isoformat(),
            confidence=0.8  # WorldTides는 신뢰할 만한 조석 데이터
        )
        
    except Exception as e:
        print(f"WorldTides 데이터 수집 실패: {e}")
        # 실패 시 기본 데이터 반환
        return _create_fallback_tide_data(location, forecast_hours)

def _create_fallback_tide_data(location: str, forecast_hours: int) -> MarineTimeseries:
    """폴백 조석 데이터 생성"""
    data_points = []
    now = datetime.now()
    
    # 간단한 조석 시뮬레이션 (12.4시간 주기)
    for i in range(min(forecast_hours, 72)):
        timestamp = (now + timedelta(hours=i)).isoformat()
        
        # 조석 높이 시뮬레이션 (0.5m ~ 2.5m)
        tide_cycle = (i / 12.4) * 2 * 3.14159  # 12.4시간 주기
        tide_height = 1.5 + 1.0 * (tide_cycle % (2 * 3.14159))
        
        data_point = MarineDataPoint(
            timestamp=timestamp,
            wind_speed=0.0,
            wind_direction=0.0,
            wave_height=0.0,
            sea_state="Unknown",
            confidence=0.3  # 폴백 데이터 신뢰도
        )
        data_points.append(data_point)
    
    return MarineTimeseries(
        source="worldtides_fallback",
        location=location,
        data_points=data_points,
        ingested_at=datetime.now().isoformat(),
        confidence=0.3
    )

def save_worldtides_forecast(location: str, timeseries: MarineTimeseries) -> None:
    """WorldTides 예보를 JSON 파일로 저장"""
    import json
    from pathlib import Path
    
    output_dir = Path("out")
    output_dir.mkdir(exist_ok=True)
    
    filename = f"worldtides_{location}.json"
    output_path = output_dir / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'source': timeseries.source,
            'location': timeseries.location,
            'ingested_at': timeseries.ingested_at,
            'confidence': timeseries.confidence,
            'data_points': [
                {
                    'timestamp': dp.timestamp,
                    'wind_speed': dp.wind_speed,
                    'wind_direction': dp.wind_direction,
                    'wave_height': dp.wave_height,
                    'sea_state': dp.sea_state
                }
                for dp in timeseries.data_points
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"WorldTides 예보 저장됨: {output_path}")

if __name__ == "__main__":
    # 테스트 실행
    import os
    
    # API 키가 설정되어 있으면 실제 데이터 수집
    api_key = os.getenv("WORLDTIDES_API_KEY", "")
    if api_key:
        for location in ["AGI", "DAS"]:
            print(f"\n=== {location} WorldTides 데이터 수집 중 ===")
            
            # UAE 좌표 (대략적)
            if location == "AGI":
                lat, lon = 25.0667, 55.1333  # Abu Dhabi
            else:
                lat, lon = 25.2048, 55.2708  # Dubai
            
            timeseries = create_marine_timeseries_from_worldtides(
                lat, lon, api_key, location
            )
            save_worldtides_forecast(location, timeseries)
            print(f"데이터 포인트 수: {len(timeseries.data_points)}")
    else:
        print("WORLDTIDES_API_KEY가 설정되지 않음. 폴백 데이터 생성.")
        timeseries = _create_fallback_tide_data("AGI", 72)
        save_worldtides_forecast("AGI", timeseries)