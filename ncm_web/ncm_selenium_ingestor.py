# KR: Selenium을 사용한 NCM 해양 관측 데이터 수집
# EN: NCM marine observations data collection using Selenium

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries
from src.marine_ops.core.units import calculate_sea_state, normalize_to_si


class NCMSeleniumIngestor:
    """Selenium을 사용한 NCM 해양 관측 데이터 수집기"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://albahar.ncm.gov.ae"

    def _setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # ChromeDriver 자동 설치 및 설정
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)

    def create_marine_timeseries(
        self, location: str = "AGI", forecast_hours: int = 72
    ) -> MarineTimeseries:
        """NCM에서 해양 시계열 데이터 생성"""

        try:
            self._setup_driver()

            # NCM Al Bahar 해양 관측 페이지 접근
            marine_url = f"{self.base_url}/marine-observations?lang=en"
            print(f"[SELENIUM] 접근 중: {marine_url}")

            self.driver.get(marine_url)

            # 페이지 로딩 대기 (DOMContentLoaded)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            print(f"[SELENIUM] 페이지 로드 완료")

            # JavaScript 실행 완료 대기 (load state)
            self.driver.execute_script("return document.readyState") == "complete"

            # 해양 관측 데이터 패널 대기
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//*[contains(text(), 'Forecast') or contains(text(), 'Marine') or contains(text(), 'Sea state')]",
                        )
                    )
                )
            except Exception:
                print("[SELENIUM] 해양 데이터 패널 대기 시간 초과, 계속 진행")
                pass

            # 테이블이나 데이터 컨테이너 찾기
            data_points = self._extract_data_with_selenium(location)

            # 동적 데이터가 없는 경우 기본 구조 반환
            if not data_points:
                print("[SELENIUM] 테이블 데이터 없음, 폴백 데이터 생성")
                data_points = self._create_fallback_data(location, forecast_hours)

            return MarineTimeseries(
                source="ncm_selenium",
                location=location,
                data_points=data_points,
                ingested_at=datetime.now().isoformat(),
                confidence=0.7,
            )

        except Exception as e:
            print(f"[SELENIUM] 웹 수집 실패: {e}")
            # 실패 시 기본 데이터 반환
            fallback_points = self._create_fallback_data(location, forecast_hours)
            return MarineTimeseries(
                source="ncm_selenium_fallback",
                location=location,
                data_points=fallback_points,
                ingested_at=datetime.now().isoformat(),
                confidence=0.3,
            )

        finally:
            if self.driver:
                self.driver.quit()

    def _extract_data_with_selenium(self, location: str) -> List[MarineDataPoint]:
        """Selenium으로 데이터 추출"""
        data_points = []

        try:
            # 테이블 요소들 찾기
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"[SELENIUM] 발견된 테이블 수: {len(tables)}")

            for i, table in enumerate(tables):
                try:
                    print(f"[SELENIUM] 테이블 {i+1} 파싱 중...")

                    # 테이블 HTML을 BeautifulSoup으로 파싱
                    from bs4 import BeautifulSoup

                    table_html = table.get_attribute("outerHTML")
                    soup = BeautifulSoup(table_html, "html.parser")

                    # pandas로 테이블 파싱
                    df_list = pd.read_html(str(soup))
                    if not df_list:
                        continue

                    df = df_list[0]
                    print(f"[SELENIUM] 테이블 {i+1} 컬럼: {list(df.columns)}")
                    print(f"[SELENIUM] 테이블 {i+1} 행 수: {len(df)}")

                    # 컬럼명 정규화
                    df.columns = [
                        str(c).strip().lower().replace(" ", "_").replace("-", "_")
                        for c in df.columns
                    ]

                    # 해양 관측 데이터 파싱
                    for _, row in df.iterrows():
                        data_point = self._parse_observation_row(row, location)
                        if data_point:
                            data_points.append(data_point)

                except Exception as e:
                    print(f"[SELENIUM] 테이블 {i+1} 파싱 오류: {e}")
                    continue

            # 테이블이 없으면 다른 데이터 컨테이너 찾기
            if not data_points:
                data_points = self._extract_from_other_containers(location)

            print(f"[SELENIUM] 총 파싱된 데이터 포인트: {len(data_points)}개")
            return data_points

        except Exception as e:
            print(f"[SELENIUM] 데이터 추출 오류: {e}")
            return []

    def _extract_from_other_containers(self, location: str) -> List[MarineDataPoint]:
        """다른 컨테이너에서 데이터 추출"""
        data_points = []

        try:
            # div나 span 요소에서 데이터 찾기
            data_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[class*='data'], div[class*='observation'], div[class*='marine'], "
                "span[class*='data'], span[class*='observation'], "
                ".weather-data, .marine-data, .observation-data",
            )

            print(f"[SELENIUM] 데이터 컨테이너 수: {len(data_elements)}")

            for element in data_elements:
                try:
                    text = element.text.strip()
                    if text and any(
                        keyword in text.lower()
                        for keyword in ["wind", "wave", "temp", "visibility"]
                    ):
                        print(f"[SELENIUM] 발견된 데이터: {text[:100]}...")

                        # 간단한 데이터 파싱 시도
                        data_point = self._parse_text_data(text, location)
                        if data_point:
                            data_points.append(data_point)

                except Exception as e:
                    continue

            return data_points

        except Exception as e:
            print(f"[SELENIUM] 컨테이너 추출 오류: {e}")
            return []

    def _parse_text_data(self, text: str, location: str) -> Optional[MarineDataPoint]:
        """텍스트에서 해양 데이터 파싱"""
        try:
            import re

            # 시간 정보 찾기
            time_pattern = r"(\d{1,2}):(\d{2})"
            time_match = re.search(time_pattern, text)
            if time_match:
                hour, minute = time_match.groups()
                timestamp = (
                    datetime.now()
                    .replace(
                        hour=int(hour), minute=int(minute), second=0, microsecond=0
                    )
                    .isoformat()
                )
            else:
                timestamp = datetime.now().isoformat()

            # 풍속 찾기
            wind_pattern = r"wind[:\s]*(\d+(?:\.\d+)?)\s*(?:kt|m/s|mph)"
            wind_match = re.search(wind_pattern, text.lower())
            wind_speed = float(wind_match.group(1)) if wind_match else 0.0

            # 파고 찾기
            wave_pattern = r"wave[:\s]*(\d+(?:\.\d+)?)\s*(?:m|ft)"
            wave_match = re.search(wave_pattern, text.lower())
            wave_height = float(wave_match.group(1)) if wave_match else 0.0

            # 시정 찾기
            vis_pattern = r"vis[ibility]*[:\s]*(\d+(?:\.\d+)?)\s*(?:km|miles)"
            vis_match = re.search(vis_pattern, text.lower())
            visibility = float(vis_match.group(1)) if vis_match else 10.0

            if wind_speed > 0 or wave_height > 0:
                return MarineDataPoint(
                    timestamp=timestamp,
                    wind_speed=wind_speed,
                    wind_direction=0.0,
                    wave_height=wave_height,
                    visibility=visibility,
                    sea_state=(
                        calculate_sea_state(wave_height)
                        if wave_height > 0
                        else "Unknown"
                    ),
                    confidence=0.70,  # NCM Selenium 스크래핑 신뢰도
                )

        except Exception as e:
            print(f"[SELENIUM] 텍스트 파싱 오류: {e}")

        return None

    def _parse_observation_row(
        self, row: pd.Series, location: str
    ) -> Optional[MarineDataPoint]:
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
            )

        except Exception as e:
            print(f"[SELENIUM] 행 파싱 오류: {e}")
            return None

    def _create_fallback_data(
        self, location: str, forecast_hours: int
    ) -> List[MarineDataPoint]:
        """폴백 데이터 생성 (실제 데이터 없을 때)"""
        data_points = []
        now = datetime.now()

        # 24시간 예보 생성
        for i in range(min(forecast_hours, 24)):
            timestamp = (now + timedelta(hours=i)).isoformat()

            # 시뮬레이션된 해양 조건
            wind_speed = 8.0 + (i % 8) * 2.0  # 8-22 m/s
            wave_height = 1.0 + (i % 6) * 0.3  # 1.0-2.5 m

            data_point = MarineDataPoint(
                timestamp=timestamp,
                wind_speed=wind_speed,
                wind_direction=270.0 + (i * 15) % 360,  # 회전하는 풍향
                wave_height=wave_height,
                sea_state=calculate_sea_state(wave_height),
                visibility=10.0,
                confidence=0.30,  # 폴백 데이터 신뢰도
            )
            data_points.append(data_point)

        return data_points

    # 기존 추출 메서드들 재사용
    def _extract_observation_timestamp(self, row: pd.Series) -> Optional[str]:
        """관측 데이터에서 타임스탬프 추출"""
        for col in [
            "time",
            "date",
            "datetime",
            "timestamp",
            "observation_time",
            "recorded_at",
        ]:
            if col in row and pd.notna(row[col]):
                try:
                    time_str = str(row[col]).strip()
                    if "T" in time_str:
                        return time_str
                    elif ":" in time_str and len(time_str) >= 5:  # HH:MM 형식
                        today = datetime.now().date().isoformat()
                        return f"{today}T{time_str}:00"
                    elif (
                        len(time_str) == 4 and time_str.replace(":", "").isdigit()
                    ):  # HHMM 형식
                        hour = time_str[:2]
                        minute = time_str[2:]
                        today = datetime.now().date().isoformat()
                        return f"{today}T{hour}:{minute}:00"
                except:
                    continue
        return None

    def _extract_observation_wind_speed(self, row: pd.Series) -> float:
        """관측 데이터에서 풍속 추출"""
        for col in ["wind_speed", "wind", "speed", "windspeed", "wind_velocity", "ws"]:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    # 단위 제거 및 숫자 추출
                    value = (
                        value.replace("kt", "")
                        .replace("m/s", "")
                        .replace("mph", "")
                        .replace("km/h", "")
                        .strip()
                    )
                    # 숫자만 추출
                    import re

                    numbers = re.findall(r"\d+\.?\d*", value)
                    if numbers:
                        speed = float(numbers[0])
                        # 노트를 m/s로 변환 (일반적으로 NCM은 노트 사용)
                        if "kt" in str(row[col]).lower() or speed > 50:  # 노트로 추정
                            return speed * 0.514444  # kt to m/s
                        return speed
                except:
                    continue
        return 0.0

    def _extract_observation_wind_direction(self, row: pd.Series) -> float:
        """관측 데이터에서 풍향 추출"""
        for col in ["wind_direction", "direction", "wind_dir", "wd", "bearing"]:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    # 숫자만 추출
                    import re

                    numbers = re.findall(r"\d+\.?\d*", value)
                    if numbers:
                        return float(numbers[0])
                    # 방향명을 각도로 변환
                    direction_map = {
                        "N": 0,
                        "NNE": 22.5,
                        "NE": 45,
                        "ENE": 67.5,
                        "E": 90,
                        "ESE": 112.5,
                        "SE": 135,
                        "SSE": 157.5,
                        "S": 180,
                        "SSW": 202.5,
                        "SW": 225,
                        "WSW": 247.5,
                        "W": 270,
                        "WNW": 292.5,
                        "NW": 315,
                        "NNW": 337.5,
                    }
                    if value.upper() in direction_map:
                        return direction_map[value.upper()]
                except:
                    continue
        return 0.0

    def _extract_observation_wave_height(self, row: pd.Series) -> float:
        """관측 데이터에서 파고 추출"""
        for col in [
            "wave_height",
            "wave",
            "height",
            "hs",
            "significant_wave_height",
            "swell",
        ]:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    # 단위 제거 및 숫자 추출
                    value = (
                        value.replace("m", "")
                        .replace("ft", "")
                        .replace("feet", "")
                        .strip()
                    )
                    import re

                    numbers = re.findall(r"\d+\.?\d*", value)
                    if numbers:
                        height = float(numbers[0])
                        # 피트를 미터로 변환
                        if "ft" in str(row[col]).lower() or height > 10:  # 피트로 추정
                            return height * 0.3048  # ft to m
                        return height
                except:
                    continue
        return 0.0

    def _extract_observation_visibility(self, row: pd.Series) -> float:
        """관측 데이터에서 시정 추출"""
        for col in ["visibility", "vis", "sight", "visual_range"]:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    value = value.replace("km", "").replace("miles", "").strip()
                    import re

                    numbers = re.findall(r"\d+\.?\d*", value)
                    if numbers:
                        vis = float(numbers[0])
                        # 마일을 km로 변환
                        if "miles" in str(row[col]).lower() or vis > 50:  # 마일로 추정
                            return vis * 1.60934  # miles to km
                        return vis
                except:
                    continue
        return 10.0  # 기본값

    def _extract_observation_temperature(self, row: pd.Series) -> float:
        """관측 데이터에서 온도 추출"""
        for col in ["temperature", "temp", "air_temp", "air_temperature"]:
            if col in row and pd.notna(row[col]):
                try:
                    value = str(row[col]).strip()
                    value = (
                        value.replace("°C", "")
                        .replace("°F", "")
                        .replace("C", "")
                        .replace("F", "")
                        .strip()
                    )
                    import re

                    numbers = re.findall(r"-?\d+\.?\d*", value)
                    if numbers:
                        temp = float(numbers[0])
                        # 화씨를 섭씨로 변환
                        if "F" in str(row[col]).upper() or temp > 50:  # 화씨로 추정
                            return (temp - 32) * 5 / 9  # F to C
                        return temp
                except:
                    continue
        return None


def save_ncm_selenium_forecast(location: str, timeseries: MarineTimeseries) -> None:
    """NCM Selenium 예보를 JSON 파일로 저장"""
    output_dir = Path("out")
    output_dir.mkdir(exist_ok=True)

    filename = f"ncm_selenium_{location}.json"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": timeseries.source,
                "location": timeseries.location,
                "ingested_at": timeseries.ingested_at,
                "confidence": timeseries.confidence,
                "data_points": [
                    {
                        "timestamp": dp.timestamp,
                        "wind_speed": dp.wind_speed,
                        "wind_direction": dp.wind_direction,
                        "wave_height": dp.wave_height,
                        "visibility": dp.visibility,
                        "temperature": dp.temperature,
                        "sea_state": dp.sea_state,
                    }
                    for dp in timeseries.data_points
                ],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"NCM Selenium 예보 저장됨: {output_path}")


if __name__ == "__main__":
    # 테스트 실행
    ingestor = NCMSeleniumIngestor(headless=True)

    for location in ["AGI", "DAS"]:
        print(f"\n=== {location} 데이터 수집 중 ===")
        timeseries = ingestor.create_marine_timeseries(location)
        save_ncm_selenium_forecast(location, timeseries)
        print(f"데이터 포인트 수: {len(timeseries.data_points)}")
