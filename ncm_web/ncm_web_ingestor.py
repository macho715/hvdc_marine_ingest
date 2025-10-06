# KR: NCM 웹 페이지에서 해양 데이터 수집
# EN: NCM web page marine data ingestion

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
import time
import os

from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
from src.marine_ops.core.units import normalize_to_si, calculate_sea_state

class NCMWebIngestor:
    """NCM 웹 페이지 데이터 수집기 (업데이트됨)"""
    
    def __init__(self, base_url: str = "https://albahar.ncm.gov.ae", use_selenium: bool = True):
        self.base_url = base_url
        self.use_selenium = use_selenium
        
        if use_selenium:
            # Selenium 사용
            from .ncm_selenium_ingestor import NCMSeleniumIngestor
            self.selenium_ingestor = NCMSeleniumIngestor(headless=True)
        else:
            # 기존 requests 방식
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
    
    def create_marine_timeseries(
        self, 
        location: str = "AGI",
        forecast_hours: int = 72
    ) -> MarineTimeseries:
        """NCM에서 해양 시계열 데이터 생성"""
        
        if self.use_selenium:
            # Selenium 사용하여 동적 페이지 처리
            print(f"[NCM] Selenium 모드로 수집 중...")
            return self.selenium_ingestor.create_marine_timeseries(location, forecast_hours)
        else:
            # 기존 requests 방식
            try:
                # NCM Al Bahar 해양 관측 페이지 접근
                marine_url = f"{self.base_url}/marine-observations?lang=en"
                print(f"[NCM] 접근 중: {marine_url}")
                
                response = self.session.get(marine_url, timeout=30)
                response.raise_for_status()
                print(f"[NCM] 응답 상태: {response.status_code}")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                data_points = []
                
                # 해양 관측 데이터 테이블 찾기
                tables = soup.find_all('table')
                print(f"[NCM] 발견된 테이블 수: {len(tables)}")
                
                if tables:
                    data_points = self._parse_marine_observations(tables, location)
                
                # 동적 데이터가 없는 경우 기본 구조 반환
                if not data_points:
                    print("[NCM] 테이블 데이터 없음, 폴백 데이터 생성")
                    data_points = self._create_fallback_data(location, forecast_hours)
                
                return MarineTimeseries(
                    source="ncm_web",
                    location=location,
                    data_points=data_points,
                    ingested_at=datetime.now().isoformat(),
                    confidence=0.60  # 웹 스크래핑이므로 낮은 신뢰도
                )
            
            except Exception as e:
                print(f"NCM 웹 수집 실패: {e}")
                # 실패 시 기본 데이터 반환
                return self._create_fallback_data(location, forecast_hours)
    
    def _parse_marine_observations(self, tables: List, location: str) -> List[MarineDataPoint]:
        """해양 관측 테이블에서 데이터 파싱"""
        data_points = []
        
        for i, table in enumerate(tables):
            try:
                print(f"[NCM] 테이블 {i+1} 파싱 중...")
                
                # pandas로 테이블 파싱
                df_list = pd.read_html(str(table))
                if not df_list:
                    continue
                    
                df = df_list[0]
                print(f"[NCM] 테이블 {i+1} 컬럼: {list(df.columns)}")
                print(f"[NCM] 테이블 {i+1} 행 수: {len(df)}")
                
                # 컬럼명 정규화
                df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
                
                # 해양 관측 데이터 컬럼 매핑
                for _, row in df.iterrows():
                    data_point = self._parse_observation_row(row, location)
                    if data_point:
                        data_points.append(data_point)
            
            except Exception as e:
                print(f"[NCM] 테이블 {i+1} 파싱 오류: {e}")
                continue
        
        print(f"[NCM] 총 파싱된 데이터 포인트: {len(data_points)}개")
        return data_points
    
    def _parse_observation_row(self, row: pd.Series, location: str) -> Optional[MarineDataPoint]:
        """관측 데이터 행 파싱"""
        try:
            # 시간 정보 추출
            timestamp = self._extract_observation_timestamp(row)
            if not timestamp:
                return None
            
            # 해양 데이터 추출
            wind_speed = self._extract_observation_wind_speed(row)
            wind_direction = self._extract_observation_wind_direction(row)
            wave_height = self._extract_observation_wave_height(row)
            visibility = self._extract_observation_visibility(row)
            temperature = self._extract_observation_temperature(row)
            
            # 바다 상태 계산
            sea_state = calculate_sea_state(wave_height) if wave_height else "Unknown"
            
                   return MarineDataPoint(
                       timestamp=timestamp,
                       wind_speed=wind_speed,
                       wind_direction=wind_direction,
                       wave_height=wave_height,
                       visibility=visibility,
                       temperature=temperature,
                       sea_state=sea_state,
                       confidence=0.60  # NCM 웹 스크래핑 신뢰도
                   )
        
        except Exception as e:
            print(f"[NCM] 행 파싱 오류: {e}")
            return None
    
    def _create_fallback_data(self, location: str, forecast_hours: int) -> List[MarineDataPoint]:
        """폴백 데이터 생성 (실제 데이터 없을 때)"""
        data_points = []
        now = datetime.now()
        
        for i in range(forecast_hours):
            timestamp = (now + timedelta(hours=i)).isoformat()
            
            # 기본값 설정 (보수적 추정)
            data_point = MarineDataPoint(
                timestamp=timestamp,
                wind_speed=8.0,  # 8 m/s (약 15.5 kt)
                wind_direction=270.0,  # 서풍
                wave_height=1.2,  # 1.2m
                sea_state="Slight",
                confidence=0.30  # 폴백 데이터 신뢰도
            )
            data_points.append(data_point)
        
        return data_points
    
    def _extract_observation_timestamp(self, row: pd.Series) -> Optional[str]:
        """관측 데이터에서 타임스탬프 추출"""
        for col in ['time', 'date', 'datetime', 'timestamp', 'observation_time', 'recorded_at']:
            if col in row and pd.notna(row[col]):
                try:
                    time_str = str(row[col]).strip()
                    if 'T' in time_str:
                        return time_str
                    elif ':' in time_str and len(time_str) >= 5:  # HH:MM 형식
                        today = datetime.now().date().isoformat()
                        return f"{today}T{time_str}:00"
                    elif len(time_str) == 4 and time_str.replace(':', '').isdigit():  # HHMM 형식
                        hour = time_str[:2]
                        minute = time_str[2:]
                        today = datetime.now().date().isoformat()
                        return f"{today}T{hour}:{minute}:00"
                except:
                    continue
        return None
    
    def _extract_observation_wind_speed(self, row: pd.Series) -> float:
        """관측 데이터에서 풍속 추출"""
        for col in ['wind_speed', 'wind', 'speed', 'windspeed', 'wind_velocity', 'ws']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    # 단위 제거 및 숫자 추출
                    value = value.replace('kt', '').replace('m/s', '').replace('mph', '').replace('km/h', '').strip()
                    # 숫자만 추출
                    import re
                    numbers = re.findall(r'\d+\.?\d*', value)
                    if numbers:
                        speed = float(numbers[0])
                        # 노트를 m/s로 변환 (일반적으로 NCM은 노트 사용)
                        if 'kt' in str(row[col]).lower() or speed > 50:  # 노트로 추정
                            return speed * 0.514444  # kt to m/s
                        return speed
                except:
                    continue
        return 0.0
    
    def _extract_observation_wind_direction(self, row: pd.Series) -> float:
        """관측 데이터에서 풍향 추출"""
        for col in ['wind_direction', 'direction', 'wind_dir', 'wd', 'bearing']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    # 숫자만 추출
                    import re
                    numbers = re.findall(r'\d+\.?\d*', value)
                    if numbers:
                        return float(numbers[0])
                    # 방향명을 각도로 변환
                    direction_map = {
                        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
                        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
                        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
                        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
                    }
                    if value.upper() in direction_map:
                        return direction_map[value.upper()]
                except:
                    continue
        return 0.0
    
    def _extract_observation_wave_height(self, row: pd.Series) -> float:
        """관측 데이터에서 파고 추출"""
        for col in ['wave_height', 'wave', 'height', 'hs', 'significant_wave_height', 'swell']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    # 단위 제거 및 숫자 추출
                    value = value.replace('m', '').replace('ft', '').replace('feet', '').strip()
                    import re
                    numbers = re.findall(r'\d+\.?\d*', value)
                    if numbers:
                        height = float(numbers[0])
                        # 피트를 미터로 변환
                        if 'ft' in str(row[col]).lower() or height > 10:  # 피트로 추정
                            return height * 0.3048  # ft to m
                        return height
                except:
                    continue
        return 0.0
    
    def _extract_observation_visibility(self, row: pd.Series) -> float:
        """관측 데이터에서 시정 추출"""
        for col in ['visibility', 'vis', 'sight', 'visual_range']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    value = value.replace('km', '').replace('miles', '').strip()
                    import re
                    numbers = re.findall(r'\d+\.?\d*', value)
                    if numbers:
                        vis = float(numbers[0])
                        # 마일을 km로 변환
                        if 'miles' in str(row[col]).lower() or vis > 50:  # 마일로 추정
                            return vis * 1.60934  # miles to km
                        return vis
                except:
                    continue
        return 10.0  # 기본값
    
    def _extract_observation_temperature(self, row: pd.Series) -> float:
        """관측 데이터에서 온도 추출"""
        for col in ['temperature', 'temp', 'air_temp', 'air_temperature']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    value = value.replace('°C', '').replace('°F', '').replace('C', '').replace('F', '').strip()
                    import re
                    numbers = re.findall(r'-?\d+\.?\d*', value)
                    if numbers:
                        temp = float(numbers[0])
                        # 화씨를 섭씨로 변환
                        if 'F' in str(row[col]).upper() or temp > 50:  # 화씨로 추정
                            return (temp - 32) * 5/9  # F to C
                        return temp
                except:
                    continue
        return None
    
    def _extract_wind_speed(self, row: pd.Series) -> float:
        """행에서 풍속 추출"""
        for col in ['wind_speed', 'wind', 'speed']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).replace('kt', '').replace('m/s', '').strip()
                    return float(value)
                except:
                    continue
        return 0.0
    
    def _extract_wind_direction(self, row: pd.Series) -> float:
        """행에서 풍향 추출"""
        for col in ['wind_direction', 'direction', 'wind_dir']:
            if col in row and pd.notna(row[col]):
                try:
                    return float(row[col])
                except:
                    continue
        return 0.0
    
    def _extract_wave_height(self, row: pd.Series) -> float:
        """행에서 파고 추출"""
        for col in ['wave_height', 'wave', 'height', 'hs']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).replace('m', '').replace('ft', '').strip()
                    return float(value)
                except:
                    continue
        return 0.0
    
    def _extract_sea_state(self, row: pd.Series) -> str:
        """행에서 바다 상태 추출"""
        for col in ['sea_state', 'condition', 'state']:
            if col in row and pd.notna(row[col]):
                state = str(row[col]).strip()
                if state and state != 'nan':
                    return state
        return "Unknown"

def save_ncm_forecast(location: str, timeseries: MarineTimeseries) -> None:
    """NCM 예보를 JSON 파일로 저장"""
    output_dir = Path("out")
    output_dir.mkdir(exist_ok=True)
    
    filename = f"ncm_forecast_{location}.json"
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
    
    print(f"NCM 예보 저장됨: {output_path}")

if __name__ == "__main__":
    # 테스트 실행
    ingestor = NCMWebIngestor()
    
    for location in ["AGI", "DAS"]:
        print(f"\n=== {location} 데이터 수집 중 ===")
        timeseries = ingestor.create_marine_timeseries(location)
        save_ncm_forecast(location, timeseries)
        print(f"데이터 포인트 수: {len(timeseries.data_points)}")
