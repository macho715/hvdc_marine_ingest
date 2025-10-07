diff --git a/ncm_web/ncm_selenium_ingestor.py b/ncm_web/ncm_selenium_ingestor.py
index 6153437862d2db4c89e6ded8101c46581bfe4c85..6e0b5302f23cca5874c26d3d712bb0bafacf7ee9 100644
--- a/ncm_web/ncm_selenium_ingestor.py
+++ b/ncm_web/ncm_selenium_ingestor.py
@@ -1,458 +1,550 @@
 # KR: Selenium을 사용한 NCM 해양 관측 데이터 수집
 # EN: NCM marine observations data collection using Selenium
 
-import time
 import json
-import pandas as pd
+import time
 from datetime import datetime, timedelta
-from typing import List, Dict, Any, Optional
 from pathlib import Path
+from typing import Any, Dict, List, Optional
 
+import pandas as pd
 from selenium import webdriver
+from selenium.webdriver.chrome.options import Options
+from selenium.webdriver.chrome.service import Service
 from selenium.webdriver.common.by import By
-from selenium.webdriver.support.ui import WebDriverWait
 from selenium.webdriver.support import expected_conditions as EC
-from selenium.webdriver.chrome.service import Service
-from selenium.webdriver.chrome.options import Options
+from selenium.webdriver.support.ui import WebDriverWait
 from webdriver_manager.chrome import ChromeDriverManager
 
-from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
-from src.marine_ops.core.units import normalize_to_si, calculate_sea_state
+from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries
+from src.marine_ops.core.units import calculate_sea_state, normalize_to_si
+
 
 class NCMSeleniumIngestor:
     """Selenium을 사용한 NCM 해양 관측 데이터 수집기"""
-    
+
     def __init__(self, headless: bool = True):
         self.headless = headless
         self.driver = None
         self.base_url = "https://albahar.ncm.gov.ae"
-    
+
     def _setup_driver(self):
         """Chrome 드라이버 설정"""
         chrome_options = Options()
-        
+
         if self.headless:
             chrome_options.add_argument("--headless")
-        
+
         chrome_options.add_argument("--no-sandbox")
         chrome_options.add_argument("--disable-dev-shm-usage")
         chrome_options.add_argument("--disable-gpu")
         chrome_options.add_argument("--window-size=1920,1080")
-        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
-        
+        chrome_options.add_argument(
+            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
+        )
+
         # ChromeDriver 자동 설치 및 설정
         service = Service(ChromeDriverManager().install())
         self.driver = webdriver.Chrome(service=service, options=chrome_options)
         self.driver.implicitly_wait(10)
-    
+
     def create_marine_timeseries(
-        self, 
-        location: str = "AGI",
-        forecast_hours: int = 72
+        self, location: str = "AGI", forecast_hours: int = 72
     ) -> MarineTimeseries:
         """NCM에서 해양 시계열 데이터 생성"""
-        
+
         try:
             self._setup_driver()
-            
+
             # NCM Al Bahar 해양 관측 페이지 접근
             marine_url = f"{self.base_url}/marine-observations?lang=en"
             print(f"[SELENIUM] 접근 중: {marine_url}")
-            
+
             self.driver.get(marine_url)
-            
+
             # 페이지 로딩 대기 (DOMContentLoaded)
             WebDriverWait(self.driver, 30).until(
                 EC.presence_of_element_located((By.TAG_NAME, "body"))
             )
-            
+
             print(f"[SELENIUM] 페이지 로드 완료")
-            
+
             # JavaScript 실행 완료 대기 (load state)
             self.driver.execute_script("return document.readyState") == "complete"
-            
+
             # 해양 관측 데이터 패널 대기
             try:
                 WebDriverWait(self.driver, 8).until(
-                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Forecast') or contains(text(), 'Marine') or contains(text(), 'Sea state')]"))
+                    EC.presence_of_element_located(
+                        (
+                            By.XPATH,
+                            "//*[contains(text(), 'Forecast') or contains(text(), 'Marine') or contains(text(), 'Sea state')]",
+                        )
+                    )
                 )
             except Exception:
                 print("[SELENIUM] 해양 데이터 패널 대기 시간 초과, 계속 진행")
                 pass
-            
+
             # 테이블이나 데이터 컨테이너 찾기
             data_points = self._extract_data_with_selenium(location)
-            
+
             # 동적 데이터가 없는 경우 기본 구조 반환
             if not data_points:
                 print("[SELENIUM] 테이블 데이터 없음, 폴백 데이터 생성")
                 data_points = self._create_fallback_data(location, forecast_hours)
-            
+
             return MarineTimeseries(
                 source="ncm_selenium",
                 location=location,
                 data_points=data_points,
                 ingested_at=datetime.now().isoformat(),
-                confidence=0.7
+                confidence=0.7,
             )
-        
+
         except Exception as e:
             print(f"[SELENIUM] 웹 수집 실패: {e}")
             # 실패 시 기본 데이터 반환
-            return self._create_fallback_data(location, forecast_hours)
-        
+            fallback_points = self._create_fallback_data(location, forecast_hours)
+            return MarineTimeseries(
+                source="ncm_selenium_fallback",
+                location=location,
+                data_points=fallback_points,
+                ingested_at=datetime.now().isoformat(),
+                confidence=0.3,
+            )
+
         finally:
             if self.driver:
                 self.driver.quit()
-    
+
     def _extract_data_with_selenium(self, location: str) -> List[MarineDataPoint]:
         """Selenium으로 데이터 추출"""
         data_points = []
-        
+
         try:
             # 테이블 요소들 찾기
             tables = self.driver.find_elements(By.TAG_NAME, "table")
             print(f"[SELENIUM] 발견된 테이블 수: {len(tables)}")
-            
+
             for i, table in enumerate(tables):
                 try:
                     print(f"[SELENIUM] 테이블 {i+1} 파싱 중...")
-                    
+
                     # 테이블 HTML을 BeautifulSoup으로 파싱
                     from bs4 import BeautifulSoup
-                    table_html = table.get_attribute('outerHTML')
-                    soup = BeautifulSoup(table_html, 'html.parser')
-                    
+
+                    table_html = table.get_attribute("outerHTML")
+                    soup = BeautifulSoup(table_html, "html.parser")
+
                     # pandas로 테이블 파싱
                     df_list = pd.read_html(str(soup))
                     if not df_list:
                         continue
-                    
+
                     df = df_list[0]
                     print(f"[SELENIUM] 테이블 {i+1} 컬럼: {list(df.columns)}")
                     print(f"[SELENIUM] 테이블 {i+1} 행 수: {len(df)}")
-                    
+
                     # 컬럼명 정규화
-                    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
-                    
+                    df.columns = [
+                        str(c).strip().lower().replace(" ", "_").replace("-", "_")
+                        for c in df.columns
+                    ]
+
                     # 해양 관측 데이터 파싱
                     for _, row in df.iterrows():
                         data_point = self._parse_observation_row(row, location)
                         if data_point:
                             data_points.append(data_point)
-                
+
                 except Exception as e:
                     print(f"[SELENIUM] 테이블 {i+1} 파싱 오류: {e}")
                     continue
-            
+
             # 테이블이 없으면 다른 데이터 컨테이너 찾기
             if not data_points:
                 data_points = self._extract_from_other_containers(location)
-            
+
             print(f"[SELENIUM] 총 파싱된 데이터 포인트: {len(data_points)}개")
             return data_points
-        
+
         except Exception as e:
             print(f"[SELENIUM] 데이터 추출 오류: {e}")
             return []
-    
+
     def _extract_from_other_containers(self, location: str) -> List[MarineDataPoint]:
         """다른 컨테이너에서 데이터 추출"""
         data_points = []
-        
+
         try:
             # div나 span 요소에서 데이터 찾기
-            data_elements = self.driver.find_elements(By.CSS_SELECTOR, 
+            data_elements = self.driver.find_elements(
+                By.CSS_SELECTOR,
                 "div[class*='data'], div[class*='observation'], div[class*='marine'], "
                 "span[class*='data'], span[class*='observation'], "
-                ".weather-data, .marine-data, .observation-data"
+                ".weather-data, .marine-data, .observation-data",
             )
-            
+
             print(f"[SELENIUM] 데이터 컨테이너 수: {len(data_elements)}")
-            
+
             for element in data_elements:
                 try:
                     text = element.text.strip()
-                    if text and any(keyword in text.lower() for keyword in ['wind', 'wave', 'temp', 'visibility']):
+                    if text and any(
+                        keyword in text.lower()
+                        for keyword in ["wind", "wave", "temp", "visibility"]
+                    ):
                         print(f"[SELENIUM] 발견된 데이터: {text[:100]}...")
-                        
+
                         # 간단한 데이터 파싱 시도
                         data_point = self._parse_text_data(text, location)
                         if data_point:
                             data_points.append(data_point)
-                
+
                 except Exception as e:
                     continue
-            
+
             return data_points
-        
+
         except Exception as e:
             print(f"[SELENIUM] 컨테이너 추출 오류: {e}")
             return []
-    
+
     def _parse_text_data(self, text: str, location: str) -> Optional[MarineDataPoint]:
         """텍스트에서 해양 데이터 파싱"""
         try:
             import re
-            
+
             # 시간 정보 찾기
-            time_pattern = r'(\d{1,2}):(\d{2})'
+            time_pattern = r"(\d{1,2}):(\d{2})"
             time_match = re.search(time_pattern, text)
             if time_match:
                 hour, minute = time_match.groups()
-                timestamp = datetime.now().replace(hour=int(hour), minute=int(minute), second=0, microsecond=0).isoformat()
+                timestamp = (
+                    datetime.now()
+                    .replace(
+                        hour=int(hour), minute=int(minute), second=0, microsecond=0
+                    )
+                    .isoformat()
+                )
             else:
                 timestamp = datetime.now().isoformat()
-            
+
             # 풍속 찾기
-            wind_pattern = r'wind[:\s]*(\d+(?:\.\d+)?)\s*(?:kt|m/s|mph)'
+            wind_pattern = r"wind[:\s]*(\d+(?:\.\d+)?)\s*(?:kt|m/s|mph)"
             wind_match = re.search(wind_pattern, text.lower())
             wind_speed = float(wind_match.group(1)) if wind_match else 0.0
-            
+
             # 파고 찾기
-            wave_pattern = r'wave[:\s]*(\d+(?:\.\d+)?)\s*(?:m|ft)'
+            wave_pattern = r"wave[:\s]*(\d+(?:\.\d+)?)\s*(?:m|ft)"
             wave_match = re.search(wave_pattern, text.lower())
             wave_height = float(wave_match.group(1)) if wave_match else 0.0
-            
+
             # 시정 찾기
-            vis_pattern = r'vis[ibility]*[:\s]*(\d+(?:\.\d+)?)\s*(?:km|miles)'
+            vis_pattern = r"vis[ibility]*[:\s]*(\d+(?:\.\d+)?)\s*(?:km|miles)"
             vis_match = re.search(vis_pattern, text.lower())
             visibility = float(vis_match.group(1)) if vis_match else 10.0
-            
+
             if wind_speed > 0 or wave_height > 0:
                 return MarineDataPoint(
                     timestamp=timestamp,
                     wind_speed=wind_speed,
                     wind_direction=0.0,
                     wave_height=wave_height,
                     visibility=visibility,
-                    sea_state=calculate_sea_state(wave_height) if wave_height > 0 else "Unknown",
-                    confidence=0.70  # NCM Selenium 스크래핑 신뢰도
+                    sea_state=(
+                        calculate_sea_state(wave_height)
+                        if wave_height > 0
+                        else "Unknown"
+                    ),
+                    confidence=0.70,  # NCM Selenium 스크래핑 신뢰도
                 )
-        
+
         except Exception as e:
             print(f"[SELENIUM] 텍스트 파싱 오류: {e}")
-        
+
         return None
-    
-    def _parse_observation_row(self, row: pd.Series, location: str) -> Optional[MarineDataPoint]:
+
+    def _parse_observation_row(
+        self, row: pd.Series, location: str
+    ) -> Optional[MarineDataPoint]:
         """관측 데이터 행 파싱"""
         try:
             # 시간 정보 추출
             timestamp = self._extract_observation_timestamp(row)
             if not timestamp:
                 return None
-            
+
             # 해양 데이터 추출
             wind_speed = self._extract_observation_wind_speed(row)
             wind_direction = self._extract_observation_wind_direction(row)
             wave_height = self._extract_observation_wave_height(row)
             visibility = self._extract_observation_visibility(row)
             temperature = self._extract_observation_temperature(row)
-            
+
             # 바다 상태 계산
             sea_state = calculate_sea_state(wave_height) if wave_height else "Unknown"
-            
+
             return MarineDataPoint(
                 timestamp=timestamp,
                 wind_speed=wind_speed,
                 wind_direction=wind_direction,
                 wave_height=wave_height,
                 visibility=visibility,
                 temperature=temperature,
-                sea_state=sea_state
+                sea_state=sea_state,
             )
-        
+
         except Exception as e:
             print(f"[SELENIUM] 행 파싱 오류: {e}")
             return None
-    
-    def _create_fallback_data(self, location: str, forecast_hours: int) -> List[MarineDataPoint]:
+
+    def _create_fallback_data(
+        self, location: str, forecast_hours: int
+    ) -> List[MarineDataPoint]:
         """폴백 데이터 생성 (실제 데이터 없을 때)"""
         data_points = []
         now = datetime.now()
-        
+
         # 24시간 예보 생성
         for i in range(min(forecast_hours, 24)):
             timestamp = (now + timedelta(hours=i)).isoformat()
-            
+
             # 시뮬레이션된 해양 조건
             wind_speed = 8.0 + (i % 8) * 2.0  # 8-22 m/s
             wave_height = 1.0 + (i % 6) * 0.3  # 1.0-2.5 m
-            
+
             data_point = MarineDataPoint(
                 timestamp=timestamp,
                 wind_speed=wind_speed,
                 wind_direction=270.0 + (i * 15) % 360,  # 회전하는 풍향
                 wave_height=wave_height,
                 sea_state=calculate_sea_state(wave_height),
                 visibility=10.0,
-                confidence=0.30  # 폴백 데이터 신뢰도
+                confidence=0.30,  # 폴백 데이터 신뢰도
             )
             data_points.append(data_point)
-        
+
         return data_points
-    
+
     # 기존 추출 메서드들 재사용
     def _extract_observation_timestamp(self, row: pd.Series) -> Optional[str]:
         """관측 데이터에서 타임스탬프 추출"""
-        for col in ['time', 'date', 'datetime', 'timestamp', 'observation_time', 'recorded_at']:
+        for col in [
+            "time",
+            "date",
+            "datetime",
+            "timestamp",
+            "observation_time",
+            "recorded_at",
+        ]:
             if col in row and pd.notna(row[col]):
                 try:
                     time_str = str(row[col]).strip()
-                    if 'T' in time_str:
+                    if "T" in time_str:
                         return time_str
-                    elif ':' in time_str and len(time_str) >= 5:  # HH:MM 형식
+                    elif ":" in time_str and len(time_str) >= 5:  # HH:MM 형식
                         today = datetime.now().date().isoformat()
                         return f"{today}T{time_str}:00"
-                    elif len(time_str) == 4 and time_str.replace(':', '').isdigit():  # HHMM 형식
+                    elif (
+                        len(time_str) == 4 and time_str.replace(":", "").isdigit()
+                    ):  # HHMM 형식
                         hour = time_str[:2]
                         minute = time_str[2:]
                         today = datetime.now().date().isoformat()
                         return f"{today}T{hour}:{minute}:00"
                 except:
                     continue
         return None
-    
+
     def _extract_observation_wind_speed(self, row: pd.Series) -> float:
         """관측 데이터에서 풍속 추출"""
-        for col in ['wind_speed', 'wind', 'speed', 'windspeed', 'wind_velocity', 'ws']:
+        for col in ["wind_speed", "wind", "speed", "windspeed", "wind_velocity", "ws"]:
             if col in row and pd.notna(row[col]):
                 try:
                     value = str(row[col]).strip()
                     # 단위 제거 및 숫자 추출
-                    value = value.replace('kt', '').replace('m/s', '').replace('mph', '').replace('km/h', '').strip()
+                    value = (
+                        value.replace("kt", "")
+                        .replace("m/s", "")
+                        .replace("mph", "")
+                        .replace("km/h", "")
+                        .strip()
+                    )
                     # 숫자만 추출
                     import re
-                    numbers = re.findall(r'\d+\.?\d*', value)
+
+                    numbers = re.findall(r"\d+\.?\d*", value)
                     if numbers:
                         speed = float(numbers[0])
                         # 노트를 m/s로 변환 (일반적으로 NCM은 노트 사용)
-                        if 'kt' in str(row[col]).lower() or speed > 50:  # 노트로 추정
+                        if "kt" in str(row[col]).lower() or speed > 50:  # 노트로 추정
                             return speed * 0.514444  # kt to m/s
                         return speed
                 except:
                     continue
         return 0.0
-    
+
     def _extract_observation_wind_direction(self, row: pd.Series) -> float:
         """관측 데이터에서 풍향 추출"""
-        for col in ['wind_direction', 'direction', 'wind_dir', 'wd', 'bearing']:
+        for col in ["wind_direction", "direction", "wind_dir", "wd", "bearing"]:
             if col in row and pd.notna(row[col]):
                 try:
                     value = str(row[col]).strip()
                     # 숫자만 추출
                     import re
-                    numbers = re.findall(r'\d+\.?\d*', value)
+
+                    numbers = re.findall(r"\d+\.?\d*", value)
                     if numbers:
                         return float(numbers[0])
                     # 방향명을 각도로 변환
                     direction_map = {
-                        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
-                        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
-                        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
-                        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
+                        "N": 0,
+                        "NNE": 22.5,
+                        "NE": 45,
+                        "ENE": 67.5,
+                        "E": 90,
+                        "ESE": 112.5,
+                        "SE": 135,
+                        "SSE": 157.5,
+                        "S": 180,
+                        "SSW": 202.5,
+                        "SW": 225,
+                        "WSW": 247.5,
+                        "W": 270,
+                        "WNW": 292.5,
+                        "NW": 315,
+                        "NNW": 337.5,
                     }
                     if value.upper() in direction_map:
                         return direction_map[value.upper()]
                 except:
                     continue
         return 0.0
-    
+
     def _extract_observation_wave_height(self, row: pd.Series) -> float:
         """관측 데이터에서 파고 추출"""
-        for col in ['wave_height', 'wave', 'height', 'hs', 'significant_wave_height', 'swell']:
+        for col in [
+            "wave_height",
+            "wave",
+            "height",
+            "hs",
+            "significant_wave_height",
+            "swell",
+        ]:
             if col in row and pd.notna(row[col]):
                 try:
                     value = str(row[col]).strip()
                     # 단위 제거 및 숫자 추출
-                    value = value.replace('m', '').replace('ft', '').replace('feet', '').strip()
+                    value = (
+                        value.replace("m", "")
+                        .replace("ft", "")
+                        .replace("feet", "")
+                        .strip()
+                    )
                     import re
-                    numbers = re.findall(r'\d+\.?\d*', value)
+
+                    numbers = re.findall(r"\d+\.?\d*", value)
                     if numbers:
                         height = float(numbers[0])
                         # 피트를 미터로 변환
-                        if 'ft' in str(row[col]).lower() or height > 10:  # 피트로 추정
+                        if "ft" in str(row[col]).lower() or height > 10:  # 피트로 추정
                             return height * 0.3048  # ft to m
                         return height
                 except:
                     continue
         return 0.0
-    
+
     def _extract_observation_visibility(self, row: pd.Series) -> float:
         """관측 데이터에서 시정 추출"""
-        for col in ['visibility', 'vis', 'sight', 'visual_range']:
+        for col in ["visibility", "vis", "sight", "visual_range"]:
             if col in row and pd.notna(row[col]):
                 try:
                     value = str(row[col]).strip()
-                    value = value.replace('km', '').replace('miles', '').strip()
+                    value = value.replace("km", "").replace("miles", "").strip()
                     import re
-                    numbers = re.findall(r'\d+\.?\d*', value)
+
+                    numbers = re.findall(r"\d+\.?\d*", value)
                     if numbers:
                         vis = float(numbers[0])
                         # 마일을 km로 변환
-                        if 'miles' in str(row[col]).lower() or vis > 50:  # 마일로 추정
+                        if "miles" in str(row[col]).lower() or vis > 50:  # 마일로 추정
                             return vis * 1.60934  # miles to km
                         return vis
                 except:
                     continue
         return 10.0  # 기본값
-    
+
     def _extract_observation_temperature(self, row: pd.Series) -> float:
         """관측 데이터에서 온도 추출"""
-        for col in ['temperature', 'temp', 'air_temp', 'air_temperature']:
+        for col in ["temperature", "temp", "air_temp", "air_temperature"]:
             if col in row and pd.notna(row[col]):
                 try:
                     value = str(row[col]).strip()
-                    value = value.replace('°C', '').replace('°F', '').replace('C', '').replace('F', '').strip()
+                    value = (
+                        value.replace("°C", "")
+                        .replace("°F", "")
+                        .replace("C", "")
+                        .replace("F", "")
+                        .strip()
+                    )
                     import re
-                    numbers = re.findall(r'-?\d+\.?\d*', value)
+
+                    numbers = re.findall(r"-?\d+\.?\d*", value)
                     if numbers:
                         temp = float(numbers[0])
                         # 화씨를 섭씨로 변환
-                        if 'F' in str(row[col]).upper() or temp > 50:  # 화씨로 추정
-                            return (temp - 32) * 5/9  # F to C
+                        if "F" in str(row[col]).upper() or temp > 50:  # 화씨로 추정
+                            return (temp - 32) * 5 / 9  # F to C
                         return temp
                 except:
                     continue
         return None
 
+
 def save_ncm_selenium_forecast(location: str, timeseries: MarineTimeseries) -> None:
     """NCM Selenium 예보를 JSON 파일로 저장"""
     output_dir = Path("out")
     output_dir.mkdir(exist_ok=True)
-    
+
     filename = f"ncm_selenium_{location}.json"
     output_path = output_dir / filename
-    
-    with open(output_path, 'w', encoding='utf-8') as f:
-        json.dump({
-            'source': timeseries.source,
-            'location': timeseries.location,
-            'ingested_at': timeseries.ingested_at,
-            'confidence': timeseries.confidence,
-            'data_points': [
-                {
-                    'timestamp': dp.timestamp,
-                    'wind_speed': dp.wind_speed,
-                    'wind_direction': dp.wind_direction,
-                    'wave_height': dp.wave_height,
-                    'visibility': dp.visibility,
-                    'temperature': dp.temperature,
-                    'sea_state': dp.sea_state
-                }
-                for dp in timeseries.data_points
-            ]
-        }, f, ensure_ascii=False, indent=2)
-    
+
+    with open(output_path, "w", encoding="utf-8") as f:
+        json.dump(
+            {
+                "source": timeseries.source,
+                "location": timeseries.location,
+                "ingested_at": timeseries.ingested_at,
+                "confidence": timeseries.confidence,
+                "data_points": [
+                    {
+                        "timestamp": dp.timestamp,
+                        "wind_speed": dp.wind_speed,
+                        "wind_direction": dp.wind_direction,
+                        "wave_height": dp.wave_height,
+                        "visibility": dp.visibility,
+                        "temperature": dp.temperature,
+                        "sea_state": dp.sea_state,
+                    }
+                    for dp in timeseries.data_points
+                ],
+            },
+            f,
+            ensure_ascii=False,
+            indent=2,
+        )
+
     print(f"NCM Selenium 예보 저장됨: {output_path}")
 
+
 if __name__ == "__main__":
     # 테스트 실행
     ingestor = NCMSeleniumIngestor(headless=True)
-    
+
     for location in ["AGI", "DAS"]:
         print(f"\n=== {location} 데이터 수집 중 ===")
         timeseries = ingestor.create_marine_timeseries(location)
         save_ncm_selenium_forecast(location, timeseries)
         print(f"데이터 포인트 수: {len(timeseries.data_points)}")
diff --git a/scripts/weather_job.py b/scripts/weather_job.py
index 27b12faf118ed05277a848f71abc0a1268f8afde..7abdd6987629c2a0a39bc40e40c8c30ca8c283f9 100644
--- a/scripts/weather_job.py
+++ b/scripts/weather_job.py
@@ -1,385 +1,585 @@
 #!/usr/bin/env python3
 """
 GitHub Actions용 해양 날씨 작업 스크립트
 매시간 실행되어 해양 날씨 데이터를 수집하고 요약 보고서를 생성합니다.
 """
 
+import argparse
+import json
+import math
 import os
 import sys
-import json
-import argparse
+from datetime import datetime, timedelta, timezone
 from pathlib import Path
-from datetime import datetime, timedelta
+from typing import List, Tuple
+
 import pandas as pd
 
 # 프로젝트 루트를 Python 경로에 추가
 project_root = Path(__file__).parent.parent
 sys.path.insert(0, str(project_root))
 
-from src.marine_ops.connectors.stormglass import StormglassConnector, LOCATIONS as SG_LOCATIONS
-from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
-from src.marine_ops.connectors.worldtides import create_marine_timeseries_from_worldtides
 from ncm_web.ncm_selenium_ingestor import NCMSeleniumIngestor
-from src.marine_ops.eri.compute import ERICalculator
+from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
+from src.marine_ops.connectors.stormglass import LOCATIONS as SG_LOCATIONS
+from src.marine_ops.connectors.stormglass import StormglassConnector
+from src.marine_ops.connectors.worldtides import (
+    create_marine_timeseries_from_worldtides,
+)
+from src.marine_ops.core.schema import (
+    ERIPoint,
+    MarineDataPoint,
+    MarineTimeseries,
+    OperationalDecision,
+)
 from src.marine_ops.decision.fusion import ForecastFusion, OperationalDecisionMaker
-from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint, OperationalDecision, ERIPoint
+from src.marine_ops.eri.compute import ERICalculator
+
+
+def create_mock_timeseries(
+    source_name: str,
+    location: str,
+    forecast_hours: int,
+    base_time: datetime,
+    reason: str,
+    confidence: float = 0.35,
+) -> Tuple[MarineTimeseries, dict]:
+    """모의 해양 시계열 생성 / Generate mock marine timeseries."""
+
+    data_points: List[MarineDataPoint] = []
+    for hour_index in range(max(forecast_hours, 12)):
+        timestamp = base_time + timedelta(hours=hour_index)
+        phase = (hour_index % 12) / 12
+        wind_speed = 6.0 + 1.5 * math.sin(math.tau * phase)
+        wave_height = 0.8 + 0.3 * math.cos(math.tau * phase)
+        data_points.append(
+            MarineDataPoint(
+                timestamp=timestamp.isoformat(),
+                wind_speed=round(wind_speed, 2),
+                wind_direction=(90 + hour_index * 15) % 360,
+                wave_height=round(max(wave_height, 0.2), 2),
+                wind_gust=round(wind_speed * 1.2, 2),
+                wave_period=5.0 + 0.5 * math.sin(math.tau * phase),
+                wave_direction=(120 + hour_index * 10) % 360,
+                visibility=9.5,
+                temperature=28.0,
+                humidity=0.68,
+                swell_wave_height=round(max(wave_height - 0.1, 0.15), 2),
+                swell_wave_period=6.0,
+                swell_wave_direction=(150 + hour_index * 12) % 360,
+                wind_wave_height=round(max(wave_height - 0.05, 0.10), 2),
+                wind_wave_period=4.5,
+                wind_wave_direction=(60 + hour_index * 14) % 360,
+                ocean_current_speed=0.35,
+                ocean_current_direction=45.0,
+                sea_surface_temperature=27.5,
+                sea_level=0.2 * math.sin(math.tau * phase),
+                confidence=confidence,
+            )
+        )
+
+    mock_timeseries = MarineTimeseries(
+        source=f"{source_name}_mock",
+        location=location,
+        data_points=data_points,
+        ingested_at=datetime.now(timezone.utc).isoformat(),
+        confidence=confidence,
+    )
+
+    status_payload = {
+        "status": f"⚠️ 모의 데이터 ({reason})",
+        "confidence": confidence,
+    }
+
+    return mock_timeseries, status_payload
+
 
 def load_config(config_path: str) -> dict:
     """설정 파일 로드"""
     try:
-        with open(config_path, 'r', encoding='utf-8') as f:
-            if config_path.endswith('.yml') or config_path.endswith('.yaml'):
+        with open(config_path, "r", encoding="utf-8") as f:
+            if config_path.endswith(".yml") or config_path.endswith(".yaml"):
                 import yaml
+
                 return yaml.safe_load(f)
             else:
                 return json.load(f)
     except FileNotFoundError:
         print(f"설정 파일을 찾을 수 없습니다: {config_path}")
         return {}
 
+
 def collect_weather_data(location_name: str = "AGI", forecast_hours: int = 24) -> dict:
-    """해양 날씨 데이터 수집"""
+    """해양 날씨 데이터 수집 / Collect marine weather data."""
     print(f"🌊 {location_name} 해역 날씨 데이터 수집 시작...")
-    
-    lat, lon = SG_LOCATIONS[location_name]['lat'], SG_LOCATIONS[location_name]['lon']
+
+    lat, lon = SG_LOCATIONS[location_name]["lat"], SG_LOCATIONS[location_name]["lon"]
     now = datetime.now()
     end_date = now + timedelta(hours=forecast_hours)
-    
+
     all_timeseries = []
     api_status = {}
-    
+    resilience_notes: List[str] = []
+
     # API 키 로드
-    stormglass_key = os.getenv('STORMGLASS_API_KEY', '')
-    worldtides_key = os.getenv('WORLDTIDES_API_KEY', '')
-    
+    stormglass_key = os.getenv("STORMGLASS_API_KEY", "")
+    worldtides_key = os.getenv("WORLDTIDES_API_KEY", "")
+
     # 1. Stormglass 데이터 수집
     try:
         if stormglass_key:
             sg_connector = StormglassConnector(api_key=stormglass_key)
-            sg_timeseries = sg_connector.get_marine_weather(lat, lon, now, end_date, location=location_name)
+            sg_timeseries = sg_connector.get_marine_weather(
+                lat, lon, now, end_date, location=location_name
+            )
             all_timeseries.append(sg_timeseries)
-            api_status['STORMGLASS'] = {
-                'status': '✅ 실제 데이터',
-                'confidence': getattr(sg_timeseries, 'confidence', 0.5)
+            api_status["STORMGLASS"] = {
+                "status": "✅ 실제 데이터",
+                "confidence": getattr(sg_timeseries, "confidence", 0.5),
             }
             print(f"✅ Stormglass: {len(sg_timeseries.data_points)}개 데이터 포인트")
         else:
-            api_status['STORMGLASS'] = {'status': '❌ API 키 없음', 'confidence': 0.0}
+            api_status["STORMGLASS"] = {"status": "❌ API 키 없음", "confidence": 0.0}
             print("❌ Stormglass API 키 없음")
+            mock_ts, status_payload = create_mock_timeseries(
+                "stormglass",
+                location_name,
+                forecast_hours,
+                now,
+                "API 키 없음",
+            )
+            all_timeseries.append(mock_ts)
+            api_status["STORMGLASS_FALLBACK"] = status_payload
+            resilience_notes.append(
+                "Stormglass 실데이터 대신 모의 데이터를 사용했습니다."
+            )
     except Exception as e:
         print(f"❌ Stormglass 수집 실패: {e}")
-        api_status['STORMGLASS'] = {'status': '❌ 실패', 'confidence': 0.0}
-    
+        api_status["STORMGLASS"] = {"status": "❌ 실패", "confidence": 0.0}
+        mock_ts, status_payload = create_mock_timeseries(
+            "stormglass",
+            location_name,
+            forecast_hours,
+            now,
+            "요청 실패",
+        )
+        all_timeseries.append(mock_ts)
+        api_status["STORMGLASS_FALLBACK"] = status_payload
+        resilience_notes.append(
+            "Stormglass 호출 실패로 자동 생성 데이터를 사용했습니다."
+        )
+
     # 2. Open-Meteo 데이터 수집
     try:
         om_connector = OpenMeteoConnector()
-        om_timeseries = om_connector.get_marine_weather(lat, lon, now, end_date, location=location_name)
+        om_timeseries = om_connector.get_marine_weather(
+            lat, lon, now, end_date, location=location_name
+        )
         all_timeseries.append(om_timeseries)
-        api_status['OPEN_METEO'] = {
-            'status': '✅ 실제 데이터',
-            'confidence': getattr(om_timeseries, 'confidence', 0.5)
+        api_status["OPEN_METEO"] = {
+            "status": "✅ 실제 데이터",
+            "confidence": getattr(om_timeseries, "confidence", 0.5),
         }
         print(f"✅ Open-Meteo: {len(om_timeseries.data_points)}개 데이터 포인트")
     except Exception as e:
         print(f"❌ Open-Meteo 수집 실패: {e}")
-        api_status['OPEN_METEO'] = {'status': '❌ 실패', 'confidence': 0.0}
-    
+        api_status["OPEN_METEO"] = {"status": "❌ 실패", "confidence": 0.0}
+        mock_ts, status_payload = create_mock_timeseries(
+            "open_meteo",
+            location_name,
+            forecast_hours,
+            now,
+            "요청 실패",
+            confidence=0.4,
+        )
+        all_timeseries.append(mock_ts)
+        api_status["OPEN_METEO_FALLBACK"] = status_payload
+        resilience_notes.append("Open-Meteo 응답 실패로 모의 데이터를 합성했습니다.")
+
     # 3. NCM Selenium 데이터 수집
     try:
         ncm_ingestor = NCMSeleniumIngestor(headless=True)
-        ncm_timeseries = ncm_ingestor.create_marine_timeseries(location=location_name, forecast_hours=forecast_hours)
+        ncm_timeseries = ncm_ingestor.create_marine_timeseries(
+            location=location_name, forecast_hours=forecast_hours
+        )
         all_timeseries.append(ncm_timeseries)
-        api_status['NCM_SELENIUM'] = {
-            'status': '✅ 실제 데이터' if "fallback" not in ncm_timeseries.source else '⚠️ 폴백 데이터', 
-            'confidence': getattr(ncm_timeseries, 'confidence', 0.5)
+        api_status["NCM_SELENIUM"] = {
+            "status": (
+                "✅ 실제 데이터"
+                if "fallback" not in ncm_timeseries.source
+                else "⚠️ 폴백 데이터"
+            ),
+            "confidence": getattr(ncm_timeseries, "confidence", 0.5),
         }
         print(f"✅ NCM Selenium: {len(ncm_timeseries.data_points)}개 데이터 포인트")
     except Exception as e:
         print(f"❌ NCM Selenium 수집 실패: {e}")
-        api_status['NCM_SELENIUM'] = {'status': '❌ 실패', 'confidence': 0.0}
-    
+        api_status["NCM_SELENIUM"] = {"status": "❌ 실패", "confidence": 0.0}
+        mock_ts, status_payload = create_mock_timeseries(
+            "ncm",
+            location_name,
+            forecast_hours,
+            now,
+            "셀레늄 실패",
+            confidence=0.3,
+        )
+        all_timeseries.append(mock_ts)
+        api_status["NCM_SELENIUM_FALLBACK"] = status_payload
+        resilience_notes.append("NCM Selenium 대신 모의 운항 데이터를 주입했습니다.")
+
     # 4. WorldTides 데이터 수집 (선택사항)
     if worldtides_key:
         try:
-            wt_timeseries = create_marine_timeseries_from_worldtides(lat, lon, worldtides_key, forecast_hours, location_name)
+            wt_timeseries = create_marine_timeseries_from_worldtides(
+                lat, lon, worldtides_key, forecast_hours, location_name
+            )
             all_timeseries.append(wt_timeseries)
-            api_status['WORLDTIDES'] = {
-                'status': '✅ 실제 데이터',
-                'confidence': getattr(wt_timeseries, 'confidence', 0.5)
+            api_status["WORLDTIDES"] = {
+                "status": "✅ 실제 데이터",
+                "confidence": getattr(wt_timeseries, "confidence", 0.5),
             }
             print(f"✅ WorldTides: {len(wt_timeseries.data_points)}개 데이터 포인트")
         except Exception as e:
             print(f"⚠️ WorldTides 수집 실패: {e}")
-            api_status['WORLDTIDES'] = {'status': '⚠️ 크레딧 부족', 'confidence': 0.3}
+            api_status["WORLDTIDES"] = {"status": "⚠️ 크레딧 부족", "confidence": 0.3}
+            mock_ts, status_payload = create_mock_timeseries(
+                "worldtides",
+                location_name,
+                forecast_hours,
+                now,
+                "크레딧 부족",
+                confidence=0.32,
+            )
+            all_timeseries.append(mock_ts)
+            api_status["WORLDTIDES_FALLBACK"] = status_payload
+            resilience_notes.append(
+                "WorldTides 크레딧 부족 시뮬레이션 데이터를 결합했습니다."
+            )
     else:
-        api_status['WORLDTIDES'] = {'status': '❌ API 키 없음', 'confidence': 0.0}
-    
+        api_status["WORLDTIDES"] = {"status": "❌ API 키 없음", "confidence": 0.0}
+        mock_ts, status_payload = create_mock_timeseries(
+            "worldtides",
+            location_name,
+            forecast_hours,
+            now,
+            "API 키 없음",
+            confidence=0.3,
+        )
+        all_timeseries.append(mock_ts)
+        api_status["WORLDTIDES_FALLBACK"] = status_payload
+        resilience_notes.append(
+            "WorldTides API 키 부재 시 모의 조석 데이터를 사용했습니다."
+        )
+
     return {
-        'timeseries': all_timeseries,
-        'api_status': api_status,
-        'location': location_name,
-        'forecast_hours': forecast_hours,
-        'collected_at': now.isoformat()
+        "timeseries": all_timeseries,
+        "api_status": api_status,
+        "location": location_name,
+        "forecast_hours": forecast_hours,
+        "collected_at": now.isoformat(),
+        "resilience_notes": resilience_notes,
     }
 
+
 def analyze_weather_data(data: dict) -> dict:
     """수집된 날씨 데이터 분석"""
     print("📊 날씨 데이터 분석 중...")
-    
-    all_timeseries = data['timeseries']
+
+    all_timeseries = data["timeseries"]
     if not all_timeseries:
-        return {'error': '수집된 데이터가 없습니다'}
-    
+        return {"error": "수집된 데이터가 없습니다"}
+
     # ERI 계산
     eri_calculator = ERICalculator()
     all_eri_points = []
-    
+
     for timeseries in all_timeseries:
         eri_points = eri_calculator.compute_eri_timeseries(timeseries)
         all_eri_points.extend(eri_points)
-    
+
     # 예보 융합
     fusion_settings = {
-        'ncm_weight': 0.60,
-        'system_weight': 0.40,
-        'alpha': 0.7,
-        'beta': 0.3
+        "ncm_weight": 0.60,
+        "system_weight": 0.40,
+        "alpha": 0.7,
+        "beta": 0.3,
     }
-    
+
     forecast_fusion = ForecastFusion(fusion_settings)
-    fused_forecasts = forecast_fusion.fuse_forecast_sources(all_timeseries, data['location'])
-    
+    fused_forecasts = forecast_fusion.fuse_forecast_sources(
+        all_timeseries, data["location"]
+    )
+
     # 운항 판정
     decision_settings = {
-        'gate': {
-            'go': {'hs_m': 1.0, 'wind_kt': 20.0},
-            'conditional': {'hs_m': 1.2, 'wind_kt': 22.0}
+        "gate": {
+            "go": {"hs_m": 1.0, "wind_kt": 20.0},
+            "conditional": {"hs_m": 1.2, "wind_kt": 22.0},
         },
-        'alert_gamma': {
-            'rough_at_times': 0.15,
-            'high_seas': 0.30
-        }
+        "alert_gamma": {"rough_at_times": 0.15, "high_seas": 0.30},
     }
-    
+
     decision_maker = OperationalDecisionMaker(decision_settings)
     decisions = decision_maker.decide_and_eta(fused_forecasts, all_eri_points)
-    
+
     # 통계 계산
-    go_count = sum(1 for d in decisions if d.decision == 'GO')
-    conditional_count = sum(1 for d in decisions if d.decision == 'CONDITIONAL')
-    no_go_count = sum(1 for d in decisions if d.decision == 'NO-GO')
-    
-    avg_eri = sum(p.eri_value for p in all_eri_points) / len(all_eri_points) if all_eri_points else 0
-    avg_wind_speed = sum(f.wind_speed_fused for f in fused_forecasts) / len(fused_forecasts) if fused_forecasts else 0
-    avg_wave_height = sum(f.wave_height_fused for f in fused_forecasts) / len(fused_forecasts) if fused_forecasts else 0
-    
+    go_count = sum(1 for d in decisions if d.decision == "GO")
+    conditional_count = sum(1 for d in decisions if d.decision == "CONDITIONAL")
+    no_go_count = sum(1 for d in decisions if d.decision == "NO-GO")
+
+    avg_eri = (
+        sum(p.eri_value for p in all_eri_points) / len(all_eri_points)
+        if all_eri_points
+        else 0
+    )
+    avg_wind_speed = (
+        sum(f.wind_speed_fused for f in fused_forecasts) / len(fused_forecasts)
+        if fused_forecasts
+        else 0
+    )
+    avg_wave_height = (
+        sum(f.wave_height_fused for f in fused_forecasts) / len(fused_forecasts)
+        if fused_forecasts
+        else 0
+    )
+
     return {
-        'total_data_points': sum(len(ts.data_points) for ts in all_timeseries),
-        'fused_forecasts': len(fused_forecasts),
-        'decisions': {
-            'total': len(decisions),
-            'GO': go_count,
-            'CONDITIONAL': conditional_count,
-            'NO-GO': no_go_count
+        "total_data_points": sum(len(ts.data_points) for ts in all_timeseries),
+        "fused_forecasts": len(fused_forecasts),
+        "decisions": {
+            "total": len(decisions),
+            "GO": go_count,
+            "CONDITIONAL": conditional_count,
+            "NO-GO": no_go_count,
         },
-        'averages': {
-            'eri': avg_eri,
-            'wind_speed_ms': avg_wind_speed,
-            'wave_height_m': avg_wave_height
+        "averages": {
+            "eri": avg_eri,
+            "wind_speed_ms": avg_wind_speed,
+            "wave_height_m": avg_wave_height,
         },
-        'eri_points': len(all_eri_points),
-        'confidence_scores': [getattr(ts, 'confidence', 0.5) for ts in all_timeseries]
+        "eri_points": len(all_eri_points),
+        "confidence_scores": [getattr(ts, "confidence", 0.5) for ts in all_timeseries],
     }
 
+
 def generate_summary_report(data: dict, analysis: dict, output_dir: str) -> dict:
-    """요약 보고서 생성"""
+    """요약 보고서 생성 / Generate summary report."""
     print("📝 요약 보고서 생성 중...")
-    
+
     output_path = Path(output_dir)
     output_path.mkdir(exist_ok=True)
-    
+
     timestamp = datetime.now().strftime("%Y%m%d_%H%M")
-    
+
     # JSON 요약
+    resilience_notes = data.get("resilience_notes", [])
+
     summary_json = {
-        'metadata': {
-            'generated_at': datetime.now().isoformat(),
-            'location': data['location'],
-            'forecast_hours': data['forecast_hours'],
-            'system_version': 'v2.1'
+        "metadata": {
+            "generated_at": datetime.now().isoformat(),
+            "location": data["location"],
+            "forecast_hours": data["forecast_hours"],
+            "system_version": "v2.1",
+            "resilience_mode": bool(resilience_notes),
         },
-        'api_status': data['api_status'],
-        'analysis': analysis,
-        'collection_stats': {
-            'total_timeseries': len(data['timeseries']),
-            'total_data_points': analysis.get('total_data_points', 0),
-            'data_collection_rate': len([s for s in data['api_status'].values() if '✅' in s['status']]) / len(data['api_status']) * 100
-        }
+        "api_status": data["api_status"],
+        "analysis": analysis,
+        "collection_stats": {
+            "total_timeseries": len(data["timeseries"]),
+            "total_data_points": analysis.get("total_data_points", 0),
+            "data_collection_rate": len(
+                [s for s in data["api_status"].values() if "✅" in s["status"]]
+            )
+            / len(data["api_status"])
+            * 100,
+        },
+        "resilience_notes": resilience_notes,
     }
-    
+
     json_path = output_path / f"summary_{timestamp}.json"
-    with open(json_path, 'w', encoding='utf-8') as f:
+    with open(json_path, "w", encoding="utf-8") as f:
         json.dump(summary_json, f, ensure_ascii=False, indent=2)
-    
+
     # CSV 요약
     csv_data = []
-    for api_name, status in data['api_status'].items():
-        csv_data.append({
-            'API': api_name,
-            'Status': status['status'],
-            'Confidence': status['confidence'],
-            'Timestamp': datetime.now().isoformat()
-        })
-    
+    for api_name, status in data["api_status"].items():
+        csv_data.append(
+            {
+                "API": api_name,
+                "Status": status["status"],
+                "Confidence": status["confidence"],
+                "Timestamp": datetime.now().isoformat(),
+            }
+        )
+
     csv_path = output_path / f"api_status_{timestamp}.csv"
     df = pd.DataFrame(csv_data)
-    df.to_csv(csv_path, index=False, encoding='utf-8')
-    
+    df.to_csv(csv_path, index=False, encoding="utf-8")
+
     # 텍스트 요약
     txt_content = f"""🌊 UAE 해역 해양 날씨 보고서
 ========================================
 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
 위치: {data['location']} (Al Ghallan Island)
 예보 기간: {data['forecast_hours']}시간
 
 📊 데이터 수집 현황:
 """
-    
-    for api_name, status in data['api_status'].items():
-        conf = status.get('confidence', None)
+
+    for api_name, status in data["api_status"].items():
+        conf = status.get("confidence", None)
         conf_txt = f"{conf:.2f}" if isinstance(conf, (int, float)) else "N/A"
         txt_content += f"  {api_name}: {status['status']} (신뢰도: {conf_txt})\n"
-    
+
     txt_content += f"""
 📈 분석 결과:
   - 총 데이터 포인트: {analysis.get('total_data_points', 0):,}개
   - 융합 예보: {analysis.get('fused_forecasts', 0)}개
   - 평균 ERI: {analysis.get('averages', {}).get('eri', 0):.3f}
   - 평균 풍속: {analysis.get('averages', {}).get('wind_speed_ms', 0):.1f} m/s
   - 평균 파고: {analysis.get('averages', {}).get('wave_height_m', 0):.2f} m
 
 🚢 운항 판정:
   - GO: {analysis.get('decisions', {}).get('GO', 0)}회
   - CONDITIONAL: {analysis.get('decisions', {}).get('CONDITIONAL', 0)}회
   - NO-GO: {analysis.get('decisions', {}).get('NO-GO', 0)}회
 
 📋 상세 보고서: {json_path.name}
 """
-    
+
+    if resilience_notes:
+        txt_content += "\n🛡️ 시스템 안정화 메모:\n"
+        for note in resilience_notes:
+            txt_content += f"  - {note}\n"
+
     txt_path = output_path / "summary.txt"
-    with open(txt_path, 'w', encoding='utf-8') as f:
+    with open(txt_path, "w", encoding="utf-8") as f:
         f.write(txt_content)
-    
+
     print(f"✅ 요약 보고서 생성 완료:")
     print(f"  - JSON: {json_path}")
     print(f"  - CSV: {csv_path}")
     print(f"  - TXT: {txt_path}")
-    
+
     return {
-        'json_path': str(json_path),
-        'csv_path': str(csv_path),
-        'txt_path': str(txt_path),
-        'summary_json': summary_json
+        "json_path": str(json_path),
+        "csv_path": str(csv_path),
+        "txt_path": str(txt_path),
+        "summary_json": summary_json,
     }
 
+
 def main():
     """메인 함수"""
-    parser = argparse.ArgumentParser(description='GitHub Actions 해양 날씨 작업')
-    parser.add_argument('--config', default='config/locations.yml', help='설정 파일 경로')
-    parser.add_argument('--out', default='out', help='출력 디렉터리')
-    parser.add_argument('--location', default='AGI', help='위치 코드')
-    parser.add_argument('--hours', type=int, default=24, help='예보 시간')
-    
+    parser = argparse.ArgumentParser(description="GitHub Actions 해양 날씨 작업")
+    parser.add_argument(
+        "--config", default="config/locations.yml", help="설정 파일 경로"
+    )
+    parser.add_argument("--out", default="out", help="출력 디렉터리")
+    parser.add_argument("--location", default="AGI", help="위치 코드")
+    parser.add_argument("--hours", type=int, default=24, help="예보 시간")
+
     args = parser.parse_args()
-    
+
     print("🤖 GitHub Actions 해양 날씨 작업 시작")
     print("=" * 50)
-    
+
     try:
         # 설정 로드
         config = load_config(args.config)
         print(f"✅ 설정 로드: {args.config}")
-        
+
         # 날씨 데이터 수집
         data = collect_weather_data(args.location, args.hours)
-        
+
         # 데이터 분석
         analysis = analyze_weather_data(data)
-        
+
         # 요약 보고서 생성
         report = generate_summary_report(data, analysis, args.out)
-        
+
         # 운항 가능성 예측 실행
         try:
             print("\n🚢 운항 가능성 예측 실행 중...")
             from src.marine_ops.operability.api import create_operability_report
-            
+
             # 항로 정보 정의
             routes = [
                 {
                     "name": "Abu Dhabi to AGI or DAS",
                     "distance_nm": 65.0,
                     "planned_speed_kt": 12.0,
-                    "hs_forecast": 1.2
+                    "hs_forecast": 1.2,
                 }
             ]
-            
+
             # 운항 가능성 보고서 생성
             # data는 딕셔너리이므로 MarineTimeseries 리스트 추출
-            weather_timeseries = data.get('timeseries', [])
-            operability_report = create_operability_report(weather_timeseries, routes, forecast_days=7)
-            
+            weather_timeseries = data.get("timeseries", [])
+            operability_report = create_operability_report(
+                weather_timeseries, routes, forecast_days=7
+            )
+
             # 운항 가능성 결과를 메인 보고서에 추가
-            report['operability_summary'] = {
-                'total_forecasts': operability_report['summary']['total_forecasts'],
-                'go_count': operability_report['summary']['go_count'],
-                'conditional_count': operability_report['summary']['conditional_count'],
-                'nogo_count': operability_report['summary']['nogo_count'],
-                'average_confidence': operability_report['summary']['average_confidence']
+            report["operability_summary"] = {
+                "total_forecasts": operability_report["summary"]["total_forecasts"],
+                "go_count": operability_report["summary"]["go_count"],
+                "conditional_count": operability_report["summary"]["conditional_count"],
+                "nogo_count": operability_report["summary"]["nogo_count"],
+                "average_confidence": operability_report["summary"][
+                    "average_confidence"
+                ],
             }
-            
+
             # 운항 가능성 CSV 저장
             import pandas as pd
-            if operability_report['operability_forecasts']:
+
+            if operability_report["operability_forecasts"]:
                 csv_data = []
-                for forecast in operability_report['operability_forecasts']:
-                    csv_data.append({
-                        'day': forecast.day,
-                        'daypart': forecast.daypart,
-                        'P_go': forecast.probabilities.P_go,
-                        'P_cond': forecast.probabilities.P_cond,
-                        'P_nogo': forecast.probabilities.P_nogo,
-                        'decision': forecast.decision,
-                        'confidence': forecast.confidence
-                    })
-                
+                for forecast in operability_report["operability_forecasts"]:
+                    csv_data.append(
+                        {
+                            "day": forecast.day,
+                            "daypart": forecast.daypart,
+                            "P_go": forecast.probabilities.P_go,
+                            "P_cond": forecast.probabilities.P_cond,
+                            "P_nogo": forecast.probabilities.P_nogo,
+                            "decision": forecast.decision,
+                            "confidence": forecast.confidence,
+                        }
+                    )
+
                 df = pd.DataFrame(csv_data)
                 operability_csv = Path(args.out) / "operability_forecasts.csv"
                 df.to_csv(operability_csv, index=False)
                 print(f"  ✅ 운항 가능성 예측 저장: {operability_csv}")
-            
-            print(f"  ✅ 운항 가능성 예측 완료: GO {operability_report['summary']['go_count']}개, "
-                  f"CONDITIONAL {operability_report['summary']['conditional_count']}개, "
-                  f"NO-GO {operability_report['summary']['nogo_count']}개")
-                  
+
+            print(
+                f"  ✅ 운항 가능성 예측 완료: GO {operability_report['summary']['go_count']}개, "
+                f"CONDITIONAL {operability_report['summary']['conditional_count']}개, "
+                f"NO-GO {operability_report['summary']['nogo_count']}개"
+            )
+
         except Exception as e:
             print(f"  ⚠️ 운항 가능성 예측 실패: {e}")
-            report['operability_summary'] = {'error': str(e)}
-        
+            report["operability_summary"] = {"error": str(e)}
+
         # 성공 메시지
-        data_rate = report['summary_json']['collection_stats']['data_collection_rate']
+        data_rate = report["summary_json"]["collection_stats"]["data_collection_rate"]
         print(f"\n🎉 작업 완료!")
         print(f"📊 데이터 수집률: {data_rate:.1f}%")
         print(f"📁 출력 디렉터리: {args.out}")
-        
+
         return True
-        
+
     except Exception as e:
         print(f"❌ 작업 실패: {e}")
         import traceback
+
         traceback.print_exc()
         return False
 
+
 if __name__ == "__main__":
     success = main()
     sys.exit(0 if success else 1)
diff --git a/src/marine_ops/eri/compute.py b/src/marine_ops/eri/compute.py
index 969961a25b5d2a77af4d665bdcc8691a12b55366..a4418c2948c6a4fae010b2d575b77873f8e292cc 100644
--- a/src/marine_ops/eri/compute.py
+++ b/src/marine_ops/eri/compute.py
@@ -1,258 +1,288 @@
 # KR: ERI (Environmental Risk Index) 계산
 # EN: Environmental Risk Index computation
 
-import yaml
 import json
-from pathlib import Path
-from typing import Dict, List, Any, Tuple
+from copy import deepcopy
 from datetime import datetime
+from pathlib import Path
+from typing import Any, Dict, List, Tuple
+
+import yaml
+
+from src.marine_ops.core.schema import ERIPoint, MarineTimeseries
+
+DEFAULT_ERI_RULES: Dict[str, Any] = {
+    "wind": {
+        "thresholds": [10, 15, 20, 25],
+        "weights": [0.2, 0.4, 0.7, 1.0],
+    },
+    "wave": {
+        "thresholds": [1.0, 1.5, 2.0, 2.5],
+        "weights": [0.2, 0.4, 0.7, 1.0],
+    },
+    "swell": {
+        "thresholds": [0.5, 1.0, 1.5, 2.0],
+        "weights": [0.1, 0.3, 0.6, 1.0],
+    },
+    "wind_wave": {
+        "thresholds": [0.5, 1.0, 1.5, 2.0],
+        "weights": [0.1, 0.3, 0.6, 1.0],
+    },
+    "ocean_current": {
+        "thresholds": [0.5, 1.0, 1.5, 2.0],
+        "weights": [0.1, 0.3, 0.6, 1.0],
+    },
+    "visibility": {
+        "thresholds": [10, 5, 2, 1],
+        "weights": [0.1, 0.3, 0.6, 1.0],
+    },
+    "fog": {
+        "thresholds": [0.1, 0.3, 0.5, 0.7],
+        "weights": [0.2, 0.4, 0.7, 1.0],
+    },
+    "sea_surface_temp": {
+        "thresholds": [20, 25, 30, 35],
+        "weights": [0.1, 0.2, 0.3, 0.5],
+    },
+}
 
-from src.marine_ops.core.schema import MarineTimeseries, ERIPoint
 
 class ERICalculator:
     """ERI 계산기"""
-    
+
     def __init__(self, rules_file: str = "config/eri_rules.yaml"):
         self.rules_file = Path(rules_file)
         self.rules = self._load_rules()
-    
+
     def _load_rules(self) -> Dict[str, Any]:
-        """ERI 규칙 로드"""
+        """ERI 규칙 로드 / Load ERI rules."""
+        merged_rules = deepcopy(DEFAULT_ERI_RULES)
+
         if self.rules_file.exists():
-            with open(self.rules_file, 'r', encoding='utf-8') as f:
-                return yaml.safe_load(f)
-        else:
-            # 기본 규칙 (확장됨)
-            return {
-                'wind': {
-                    'thresholds': [10, 15, 20, 25],  # m/s
-                    'weights': [0.2, 0.4, 0.7, 1.0]
-                },
-                'wave': {
-                    'thresholds': [1.0, 1.5, 2.0, 2.5],  # m
-                    'weights': [0.2, 0.4, 0.7, 1.0]
-                },
-                'swell': {
-                    'thresholds': [0.5, 1.0, 1.5, 2.0],  # m
-                    'weights': [0.1, 0.3, 0.6, 1.0]
-                },
-                'wind_wave': {
-                    'thresholds': [0.5, 1.0, 1.5, 2.0],  # m
-                    'weights': [0.1, 0.3, 0.6, 1.0]
-                },
-                'ocean_current': {
-                    'thresholds': [0.5, 1.0, 1.5, 2.0],  # m/s
-                    'weights': [0.1, 0.3, 0.6, 1.0]
-                },
-                'visibility': {
-                    'thresholds': [10, 5, 2, 1],  # km
-                    'weights': [0.1, 0.3, 0.6, 1.0]
-                },
-                'fog': {
-                    'thresholds': [0.1, 0.3, 0.5, 0.7],  # probability
-                    'weights': [0.2, 0.4, 0.7, 1.0]
-                },
-                'sea_surface_temp': {
-                    'thresholds': [20, 25, 30, 35],  # °C
-                    'weights': [0.1, 0.2, 0.3, 0.5]  # 온도는 낮은 위험도
-                }
-            }
-    
+            with open(self.rules_file, "r", encoding="utf-8") as f:
+                file_rules = yaml.safe_load(f) or {}
+                merged_rules = self._merge_rules(merged_rules, file_rules)
+
+        return merged_rules
+
+    def _merge_rules(
+        self, base: Dict[str, Any], overrides: Dict[str, Any]
+    ) -> Dict[str, Any]:
+        """ERI 규칙 병합 / Merge ERI rule dictionaries."""
+        for key, value in overrides.items():
+            if isinstance(value, dict) and isinstance(base.get(key), dict):
+                base[key] = self._merge_rules(base[key], value)
+            else:
+                base[key] = value
+        return base
+
     def compute_eri_timeseries(self, timeseries: MarineTimeseries) -> List[ERIPoint]:
         """시계열 데이터에 대한 ERI 계산"""
         eri_points = []
-        
+
         for data_point in timeseries.data_points:
             # 각 요소별 위험도 계산
             wind_risk = self._calculate_wind_risk(data_point.wind_speed)
             wave_risk = self._calculate_wave_risk(data_point.wave_height)
             visibility_risk = self._calculate_visibility_risk(data_point.visibility)
             fog_risk = self._calculate_fog_risk(data_point.fog_probability)
-            
+
             # 가중 평균으로 전체 ERI 계산 (확장된 변수 포함)
             total_eri = (
-                wind_risk * 0.3 +      # 풍속 30%
-                wave_risk * 0.25 +     # 파고 25%
-                self._calculate_swell_risk(data_point.swell_wave_height) * 0.15 +  # 스웰 15%
-                self._calculate_wind_wave_risk(data_point.wind_wave_height) * 0.1 +  # 바람파 10%
-                self._calculate_ocean_current_risk(data_point.ocean_current_speed) * 0.05 +  # 해류 5%
-                visibility_risk * 0.1 + # 시정 10%
-                fog_risk * 0.05        # 안개 5%
+                wind_risk * 0.3  # 풍속 30%
+                + wave_risk * 0.25  # 파고 25%
+                + self._calculate_swell_risk(data_point.swell_wave_height)
+                * 0.15  # 스웰 15%
+                + self._calculate_wind_wave_risk(data_point.wind_wave_height)
+                * 0.1  # 바람파 10%
+                + self._calculate_ocean_current_risk(data_point.ocean_current_speed)
+                * 0.05  # 해류 5%
+                + visibility_risk * 0.1  # 시정 10%
+                + fog_risk * 0.05  # 안개 5%
             )
-            
+
             eri_point = ERIPoint(
                 timestamp=data_point.timestamp,
                 eri_value=total_eri,
                 wind_contribution=wind_risk,
                 wave_contribution=wave_risk,
                 visibility_contribution=visibility_risk,
-                fog_contribution=fog_risk
+                fog_contribution=fog_risk,
             )
             eri_points.append(eri_point)
-        
+
         return eri_points
-    
+
     def _calculate_wind_risk(self, wind_speed: float) -> float:
         """풍속 위험도 계산"""
-        thresholds = self.rules['wind']['thresholds']
-        weights = self.rules['wind']['weights']
-        
+        thresholds = self.rules["wind"]["thresholds"]
+        weights = self.rules["wind"]["weights"]
+
         if wind_speed < thresholds[0]:
             return weights[0]
         elif wind_speed < thresholds[1]:
             return weights[1]
         elif wind_speed < thresholds[2]:
             return weights[2]
         elif wind_speed < thresholds[3]:
             return weights[3]
         else:
             return 1.0  # 최대 위험
-    
+
     def _calculate_wave_risk(self, wave_height: float) -> float:
         """파고 위험도 계산"""
-        thresholds = self.rules['wave']['thresholds']
-        weights = self.rules['wave']['weights']
-        
+        thresholds = self.rules["wave"]["thresholds"]
+        weights = self.rules["wave"]["weights"]
+
         if wave_height < thresholds[0]:
             return weights[0]
         elif wave_height < thresholds[1]:
             return weights[1]
         elif wave_height < thresholds[2]:
             return weights[2]
         elif wave_height < thresholds[3]:
             return weights[3]
         else:
             return 1.0  # 최대 위험
-    
+
     def _calculate_visibility_risk(self, visibility: float) -> float:
         """시정 위험도 계산"""
         if visibility is None:
             return 0.5  # 중간 위험 (데이터 없음)
-        
-        thresholds = self.rules['visibility']['thresholds']
-        weights = self.rules['visibility']['weights']
-        
+
+        thresholds = self.rules["visibility"]["thresholds"]
+        weights = self.rules["visibility"]["weights"]
+
         if visibility > thresholds[0]:
             return weights[0]
         elif visibility > thresholds[1]:
             return weights[1]
         elif visibility > thresholds[2]:
             return weights[2]
         elif visibility > thresholds[3]:
             return weights[3]
         else:
             return 1.0  # 최대 위험
-    
+
     def _calculate_fog_risk(self, fog_probability: float) -> float:
         """안개 위험도 계산"""
         if fog_probability is None:
             return 0.1  # 낮은 위험 (데이터 없음)
-        
-        thresholds = self.rules['fog']['thresholds']
-        weights = self.rules['fog']['weights']
-        
+
+        thresholds = self.rules["fog"]["thresholds"]
+        weights = self.rules["fog"]["weights"]
+
         if fog_probability < thresholds[0]:
             return weights[0]
         elif fog_probability < thresholds[1]:
             return weights[1]
         elif fog_probability < thresholds[2]:
             return weights[2]
         elif fog_probability < thresholds[3]:
             return weights[3]
         else:
             return 1.0  # 최대 위험
-    
+
     def _calculate_swell_risk(self, swell_height: float) -> float:
         """스웰 파고 위험도 계산"""
         if swell_height is None:
             return 0.1  # 낮은 위험 (데이터 없음)
-        
-        thresholds = self.rules['swell']['thresholds']
-        weights = self.rules['swell']['weights']
-        
+
+        thresholds = self.rules["swell"]["thresholds"]
+        weights = self.rules["swell"]["weights"]
+
         if swell_height < thresholds[0]:
             return weights[0]
         elif swell_height < thresholds[1]:
             return weights[1]
         elif swell_height < thresholds[2]:
             return weights[2]
         elif swell_height < thresholds[3]:
             return weights[3]
         else:
             return 1.0  # 최대 위험
-    
+
     def _calculate_wind_wave_risk(self, wind_wave_height: float) -> float:
         """바람파 위험도 계산"""
         if wind_wave_height is None:
             return 0.1  # 낮은 위험 (데이터 없음)
-        
-        thresholds = self.rules['wind_wave']['thresholds']
-        weights = self.rules['wind_wave']['weights']
-        
+
+        thresholds = self.rules["wind_wave"]["thresholds"]
+        weights = self.rules["wind_wave"]["weights"]
+
         if wind_wave_height < thresholds[0]:
             return weights[0]
         elif wind_wave_height < thresholds[1]:
             return weights[1]
         elif wind_wave_height < thresholds[2]:
             return weights[2]
         elif wind_wave_height < thresholds[3]:
             return weights[3]
         else:
             return 1.0  # 최대 위험
-    
+
     def _calculate_ocean_current_risk(self, current_speed: float) -> float:
         """해류 속도 위험도 계산"""
         if current_speed is None:
             return 0.1  # 낮은 위험 (데이터 없음)
-        
-        thresholds = self.rules['ocean_current']['thresholds']
-        weights = self.rules['ocean_current']['weights']
-        
+
+        thresholds = self.rules["ocean_current"]["thresholds"]
+        weights = self.rules["ocean_current"]["weights"]
+
         if current_speed < thresholds[0]:
             return weights[0]
         elif current_speed < thresholds[1]:
             return weights[1]
         elif current_speed < thresholds[2]:
             return weights[2]
         elif current_speed < thresholds[3]:
             return weights[3]
         else:
             return 1.0  # 최대 위험
 
-def compute_eri_for_ncm(timeseries: MarineTimeseries, ncm_discount: float = 0.8) -> List[ERIPoint]:
+
+def compute_eri_for_ncm(
+    timeseries: MarineTimeseries, ncm_discount: float = 0.8
+) -> List[ERIPoint]:
     """NCM 데이터에 대한 특별 ERI 계산 (할인 적용)"""
     calculator = ERICalculator()
     eri_points = calculator.compute_eri_timeseries(timeseries)
-    
+
     # NCM 데이터는 신뢰도가 낮으므로 위험도를 할인
     for point in eri_points:
         point.eri_value *= ncm_discount
         point.wind_contribution *= ncm_discount
         point.wave_contribution *= ncm_discount
         point.visibility_contribution *= ncm_discount
         point.fog_contribution *= ncm_discount
-    
+
     return eri_points
 
+
 def save_eri_timeseries(location: str, eri_points: List[ERIPoint]) -> None:
     """ERI 시계열을 JSON 파일로 저장"""
     output_dir = Path("out")
     output_dir.mkdir(exist_ok=True)
-    
+
     filename = f"eri_{location}.json"
     output_path = output_dir / filename
-    
-    with open(output_path, 'w', encoding='utf-8') as f:
-        json.dump([
-            {
-                'timestamp': point.timestamp,
-                'eri_value': point.eri_value,
-                'wind_contribution': point.wind_contribution,
-                'wave_contribution': point.wave_contribution,
-                'visibility_contribution': point.visibility_contribution,
-                'fog_contribution': point.fog_contribution
-            }
-            for point in eri_points
-        ], f, ensure_ascii=False, indent=2)
-    
+
+    with open(output_path, "w", encoding="utf-8") as f:
+        json.dump(
+            [
+                {
+                    "timestamp": point.timestamp,
+                    "eri_value": point.eri_value,
+                    "wind_contribution": point.wind_contribution,
+                    "wave_contribution": point.wave_contribution,
+                    "visibility_contribution": point.visibility_contribution,
+                    "fog_contribution": point.fog_contribution,
+                }
+                for point in eri_points
+            ],
+            f,
+            ensure_ascii=False,
+            indent=2,
+        )
+
     print(f"ERI 데이터 저장됨: {output_path}")
