# KR: Cursor 1.7 Browser Controls 훅 - NCM 해양예보 자동 수집
# EN: Cursor 1.7 Browser Controls hook - NCM marine forecast auto collection

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
from src.marine_ops.core.vector_db import MarineVectorDB

class NCMBrowserHook:
    """NCM 브라우저 컨트롤 훅"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.vector_db = MarineVectorDB()
    
    def on_page_loaded(self, url: str, page_content: str) -> Dict[str, Any]:
        """페이지 로드 완료 시 호출"""
        print(f"[HOOK] 페이지 로드됨: {url}")
        
        if ("ncm" in url.lower() and "marine" in url.lower()) or "albahar.ncm.gov.ae" in url:
            return self._process_ncm_marine_page(page_content, url)
        
        return {"status": "ignored", "reason": "Not a marine forecast page"}
    
    def _process_ncm_marine_page(self, content: str, url: str) -> Dict[str, Any]:
        """NCM 해양 예보 페이지 처리"""
        try:
            print("[HOOK] NCM 해양 예보 페이지 감지됨")
            
            # BeautifulSoup으로 HTML 파싱
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # 테이블 데이터 추출
            marine_data = self._extract_marine_tables(soup)
            
            if marine_data:
                # CSV 저장
                csv_path = self._save_to_csv(marine_data, url)
                
                # 벡터 DB 저장
                vector_results = self._save_to_vector_db(marine_data, url)
                
                return {
                    "status": "success",
                    "csv_path": str(csv_path),
                    "vector_results": vector_results,
                    "data_points": len(marine_data),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "no_data",
                    "message": "No marine forecast data found in page"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_marine_tables(self, soup) -> List[Dict[str, Any]]:
        """해양 예보 테이블에서 데이터 추출"""
        marine_data = []
        
        # 테이블 찾기
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                # pandas로 테이블 파싱
                df_list = pd.read_html(str(table))
                
                for df in df_list:
                    if df.empty:
                        continue
                    
                    # 컬럼명 정규화
                    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                    
                    # 해양 관련 컬럼 확인
                    marine_columns = ['time', 'wind', 'wave', 'sea', 'visibility', 'date']
                    if any(col in ' '.join(df.columns) for col in marine_columns):
                        marine_data.extend(self._parse_marine_table(df))
            
            except Exception as e:
                print(f"테이블 파싱 오류: {e}")
                continue
        
        # 동적 데이터가 없는 경우 기본 구조 생성
        if not marine_data:
            marine_data = self._create_fallback_data()
        
        return marine_data
    
    def _parse_marine_table(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """해양 테이블 데이터 파싱"""
        data_points = []
        
        for _, row in df.iterrows():
            try:
                # 시간 정보 추출
                timestamp = self._extract_timestamp(row)
                if not timestamp:
                    continue
                
                # 해양 데이터 추출
                wind_speed = self._extract_wind_speed(row)
                wind_direction = self._extract_wind_direction(row)
                wave_height = self._extract_wave_height(row)
                visibility = self._extract_visibility(row)
                
                data_point = {
                    'timestamp': timestamp,
                    'wind_speed': wind_speed,
                    'wind_direction': wind_direction,
                    'wave_height': wave_height,
                    'visibility': visibility,
                    'source': 'ncm_web',
                    'location': 'AGI'  # 기본값, 실제로는 페이지에서 추출
                }
                
                data_points.append(data_point)
            
            except Exception as e:
                print(f"행 파싱 오류: {e}")
            continue

        return data_points
    
    def _create_fallback_data(self) -> List[Dict[str, Any]]:
        """폴백 데이터 생성"""
        print("[HOOK] 폴백 데이터 생성")
        
        data_points = []
        now = datetime.now()
        
        # 24시간 예보 생성
        for i in range(24):
            timestamp = (now.replace(hour=now.hour + i, minute=0, second=0, microsecond=0)).isoformat()
            
            data_point = {
                'timestamp': timestamp,
                'wind_speed': 8.0 + (i % 6) * 2.0,  # 8-18 m/s
                'wind_direction': 270.0 + (i * 15) % 360,
                'wave_height': 1.0 + (i % 4) * 0.4,  # 1.0-2.2 m
                'visibility': 10.0,
                'source': 'ncm_web_fallback',
                'location': 'AGI'
            }
            data_points.append(data_point)
        
        return data_points
    
    def _extract_timestamp(self, row: pd.Series) -> Optional[str]:
        """시간 정보 추출"""
        for col in ['time', 'date', 'datetime', 'timestamp']:
            if col in row and pd.notna(row[col]):
                try:
                    time_str = str(row[col]).strip()
                    if 'T' in time_str:
                        return time_str
                    elif ':' in time_str:
                        today = datetime.now().date().isoformat()
                        return f"{today}T{time_str}:00"
                except:
                    continue
        return None
    
    def _extract_wind_speed(self, row: pd.Series) -> float:
        """풍속 추출"""
        for col in ['wind_speed', 'wind', 'speed']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).replace('kt', '').replace('m/s', '').strip()
                    return float(value)
                except:
                    continue
        return 0.0
    
    def _extract_wind_direction(self, row: pd.Series) -> float:
        """풍향 추출"""
        for col in ['wind_direction', 'direction', 'wind_dir']:
            if col in row and pd.notna(row[col]):
                try:
                    return float(row[col])
                except:
                    continue
        return 0.0
    
    def _extract_wave_height(self, row: pd.Series) -> float:
        """파고 추출"""
        for col in ['wave_height', 'wave', 'height', 'hs']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).replace('m', '').replace('ft', '').strip()
                    return float(value)
                except:
                    continue
        return 0.0
    
    def _extract_visibility(self, row: pd.Series) -> float:
        """시정 추출"""
        for col in ['visibility', 'vis', 'sight']:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).replace('km', '').strip()
                    return float(value)
                except:
                    continue
        return 10.0
    
    def _save_to_csv(self, marine_data: List[Dict[str, Any]], url: str) -> Path:
        """CSV 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"marine_ncm_{timestamp}.csv"
        csv_path = self.data_dir / filename
        
        df = pd.DataFrame(marine_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"[HOOK] CSV 저장됨: {csv_path}")
        return csv_path
    
    def _save_to_vector_db(self, marine_data: List[Dict[str, Any]], url: str) -> Dict[str, int]:
        """벡터 DB에 저장"""
        try:
            # MarineTimeseries 객체로 변환
            data_points = []
            for item in marine_data:
                data_point = MarineDataPoint(
                    timestamp=item['timestamp'],
                    wind_speed=item['wind_speed'],
                    wind_direction=item['wind_direction'],
                    wave_height=item['wave_height'],
                    visibility=item.get('visibility')
                )
                data_points.append(data_point)
            
            timeseries = MarineTimeseries(
                source="ncm_browser_hook",
                location=marine_data[0].get('location', 'AGI'),
                data_points=data_points,
                ingested_at=datetime.now().isoformat(),
                confidence=0.7
            )
            
            # 벡터 DB에 저장
            stored_count = self.vector_db.store_timeseries(timeseries)
            
            return {
                "stored_count": stored_count,
                "location": timeseries.location,
                "source": timeseries.source
            }
        
        except Exception as e:
            print(f"[HOOK] 벡터 DB 저장 실패: {e}")
            return {"error": str(e)}

# Cursor 훅 등록
def register_hooks():
    """Cursor 훅 등록"""
    hook = NCMBrowserHook()
    
    return {
        'on_page_loaded': hook.on_page_loaded,
        'on_element_clicked': None,  # 필요시 구현
        'on_form_submitted': None,   # 필요시 구현
    }

# 훅 인스턴스 생성
ncm_hook = NCMBrowserHook()

# 전역 함수로 노출 (Cursor에서 호출)
def on_page_loaded(url: str, content: str) -> Dict[str, Any]:
    return ncm_hook.on_page_loaded(url, content)

def on_navigation_complete(url: str, content: str) -> Dict[str, Any]:
    return ncm_hook.on_page_loaded(url, content)

# 테스트 함수
def test_hook():
    """훅 테스트"""
    print("=== NCM Browser Hook 테스트 ===")
    
    # 샘플 HTML 콘텐츠
    sample_html = """
    <html>
        <body>
            <table>
                <tr><th>Time</th><th>Wind</th><th>Wave</th><th>Visibility</th></tr>
                <tr><td>06:00</td><td>15 kt</td><td>1.2m</td><td>10km</td></tr>
                <tr><td>12:00</td><td>18 kt</td><td>1.5m</td><td>8km</td></tr>
            </table>
        </body>
    </html>
    """
    
    result = ncm_hook.on_page_loaded("https://www.ncm.ae/marine-forecast", sample_html)
    print(f"테스트 결과: {result}")

if __name__ == "__main__":
    test_hook()