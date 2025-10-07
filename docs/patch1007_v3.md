diff --git a/FINAL_TEST_REPORT.md b/FINAL_TEST_REPORT.md
index ce4410684df686316487b5c40a0c4712fd45637e..7a85abfe63f9f12ac12c15759458a0a6fbfc9bbb 100644
--- a/FINAL_TEST_REPORT.md
+++ b/FINAL_TEST_REPORT.md
@@ -21,57 +21,57 @@
 - **융합 예보**: 120개
 - **평균 ERI**: 0.237
 - **평균 풍속**: 10.9 m/s
 - **평균 파고**: 0.35 m
 
 ### **3. 운항 가능성 예측**
 - **GO**: 28개 예측
 - **CONDITIONAL**: 0개
 - **NO-GO**: 0개
 - **예측 기간**: 7일
 
 ## 📁 **생성된 파일 목록**
 
 | 파일명 | 크기 | 설명 |
 |--------|------|------|
 | `summary.txt` | 727 bytes | 텍스트 요약 보고서 |
 | `summary_20251007_0152.json` | 1,097 bytes | JSON 상세 보고서 |
 | `api_status_20251007_0152.csv` | 288 bytes | API 상태 CSV |
 | `operability_forecasts.csv` | 1,783 bytes | 운항 가능성 예측 |
 | `operability_report.json` | 8,528 bytes | 운항 가능성 상세 보고서 |
 
 ## 🔧 **GitHub Secrets 설정 상태**
 
 ### **필수 Secrets (설정 필요)**
 ```
-TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk
-TELEGRAM_CHAT_ID: 470962761
-MAIL_USERNAME: mscho715@gmail.com
-MAIL_PASSWORD: svomdxwnvdzedfle
-MAIL_TO: mscho715@gmail.com
-STORMGLASS_API_KEY: [API 키 입력 필요]
-WORLDTIDES_API_KEY: [API 키 입력 필요]
+TELEGRAM_BOT_TOKEN: <YOUR_TELEGRAM_BOT_TOKEN>
+TELEGRAM_CHAT_ID: <YOUR_TELEGRAM_CHAT_ID>
+MAIL_USERNAME: <YOUR_GMAIL_ADDRESS>
+MAIL_PASSWORD: <YOUR_16_CHAR_APP_PASSWORD>
+MAIL_TO: <RECIPIENT_EMAIL>
+STORMGLASS_API_KEY: <STORMGLASS_API_KEY>
+WORLDTIDES_API_KEY: <WORLDTIDES_API_KEY>
 ```
 
 ### **알림 시스템 검증**
 - ✅ **Telegram**: Bot Token + Chat ID 검증 완료
 - ✅ **Gmail**: App Password 인증 성공
 - ✅ **GitHub Actions**: 워크플로우 정상 작동
 
 ## 🎯 **GitHub Actions 워크플로우 상태**
 
 ### **워크플로우 파일 검증**
 - ✅ `marine-hourly.yml` 파일 존재
 - ✅ 권한 설정 완료 (`contents: read`, `actions: read`, `secrets: read`)
 - ✅ 시크릿 진단 스텝 포함
 - ✅ Telegram ping 검증 스텝 포함
 - ✅ 조건부 알림 실행 설정
 
 ### **스케줄 설정**
 - **크론**: `7 * * * *` (UTC, 매시간 7분)
 - **수동 실행**: `workflow_dispatch` 활성화
 
 ## 📈 **데이터 품질 분석**
 
 ### **수집 성공률**
 - **현재**: 50.0% (2/4 소스)
 - **API 키 설정 후 예상**: 75.0% (3/4 소스)
diff --git a/check_github_secrets_status.md b/check_github_secrets_status.md
index a4de53938e5586534b55eab382c1247c9499c363..0849655dccf6b494bbaa33c48879a4ab32f3b7ab 100644
--- a/check_github_secrets_status.md
+++ b/check_github_secrets_status.md
@@ -1,52 +1,52 @@
 # 🔍 GitHub Secrets 설정 상태 확인 가이드
 
 ## 🚨 **문제 진단 결과**
 - ✅ GitHub Actions 워크플로우: **성공 실행**
 - ✅ Telegram Bot: **정상 작동** (테스트 메시지 전송 성공)
 - ✅ Gmail SMTP: **정상 작동** (테스트 이메일 전송 성공)
 - ❌ **알림 수신 실패**: GitHub Secrets 미설정 가능성 높음
 
 ## 📋 **GitHub Secrets 설정 확인 방법**
 
 ### **1단계: GitHub 리포지토리 접속**
 1. **GitHub** → **macho715/hvdc_marine_ingest** 리포지토리
 2. **Settings** 탭 클릭
 3. **Secrets and variables** → **Actions** 클릭
 
 ### **2단계: 필수 Secrets 확인**
 다음 7개 시크릿이 모두 설정되어 있는지 확인:
 
 | Secret Name | 설정 상태 | 값 예시 |
 |-------------|-----------|---------|
-| `TELEGRAM_BOT_TOKEN` | ❓ 확인 필요 | `8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk` |
-| `TELEGRAM_CHAT_ID` | ❓ 확인 필요 | `470962761` |
-| `MAIL_USERNAME` | ❓ 확인 필요 | `mscho715@gmail.com` |
-| `MAIL_PASSWORD` | ❓ 확인 필요 | `svomdxwnvdzedfle` |
-| `MAIL_TO` | ❓ 확인 필요 | `mscho715@gmail.com` |
-| `STORMGLASS_API_KEY` | ❓ 확인 필요 | `[API 키]` |
-| `WORLDTIDES_API_KEY` | ❓ 확인 필요 | `[API 키]` |
+| `TELEGRAM_BOT_TOKEN` | ❓ 확인 필요 | `<YOUR_TELEGRAM_BOT_TOKEN>` |
+| `TELEGRAM_CHAT_ID` | ❓ 확인 필요 | `<YOUR_TELEGRAM_CHAT_ID>` |
+| `MAIL_USERNAME` | ❓ 확인 필요 | `<YOUR_GMAIL_ADDRESS>` |
+| `MAIL_PASSWORD` | ❓ 확인 필요 | `<YOUR_16_CHAR_APP_PASSWORD>` |
+| `MAIL_TO` | ❓ 확인 필요 | `<RECIPIENT_EMAIL>` |
+| `STORMGLASS_API_KEY` | ❓ 확인 필요 | `<STORMGLASS_API_KEY>` |
+| `WORLDTIDES_API_KEY` | ❓ 확인 필요 | `<WORLDTIDES_API_KEY>` |
 
 ### **3단계: Secrets 설정 방법**
 1. **"New repository secret"** 클릭
 2. **Name**: 위 표의 Secret Name 입력
 3. **Secret**: 해당 값 입력
 4. **"Add secret"** 클릭
 5. 7개 모두 반복
 
 ## 🔧 **GitHub Actions 수동 실행 테스트**
 
 ### **1단계: 워크플로우 수동 실행**
 1. **Actions** 탭 클릭
 2. **"Marine Weather Hourly Collection"** 워크플로우 선택
 3. **"Run workflow"** 클릭
 4. **"Run workflow"** 버튼 다시 클릭
 
 ### **2단계: 실행 로그 확인**
 워크플로우 실행 중 다음 단계들을 확인:
 
 ```
 ✅ Compute gates - 시크릿 상태 진단
 ✅ Telegram ping (secrets validation) - Bot 토큰 검증
 ✅ Weather data collection - 데이터 수집
 ✅ Telegram notify - 알림 전송
 ✅ Email notify - 이메일 전송
diff --git a/github_secrets_guide.md b/github_secrets_guide.md
index 027d407ca83f6de3fe5e14eba845b08f6c2f2071..54012a4711aae8ace0aeedb78f6ff0160e622ace 100644
--- a/github_secrets_guide.md
+++ b/github_secrets_guide.md
@@ -1,66 +1,66 @@
 # GitHub Secrets 설정 가이드
 
 ## 🎯 현재 완료된 설정
 
 ### ✅ Telegram 설정 (완료)
-- **Bot Token**: `8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk`
-- **Chat ID**: `470962761`
-- **테스트 메시지**: 성공적으로 발송됨
+- **Bot Token**: `<YOUR_TELEGRAM_BOT_TOKEN>`
+- **Chat ID**: `<YOUR_TELEGRAM_CHAT_ID>`
+- **테스트 메시지**: 성공적으로 발송됨 (실제 값은 GitHub Secrets에만 저장)
 
 ### ❌ Gmail 설정 (문제 있음)
 - **App Password**: 인증 실패 (535 오류)
 - **해결 필요**: 새로운 App Password 생성
 
 ## 📋 GitHub Secrets 설정 방법
 
 ### 1단계: GitHub 리포지토리 설정
 1. GitHub 리포지토리 → **Settings**
 2. **Secrets and variables** → **Actions**
 3. **"New repository secret"** 클릭
 
 ### 2단계: 필수 Secrets 설정
 
 #### A) Telegram Secrets (즉시 설정 가능)
 ```
 Name: TELEGRAM_BOT_TOKEN
-Value: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk
+Value: <YOUR_TELEGRAM_BOT_TOKEN>
 
 Name: TELEGRAM_CHAT_ID
-Value: 470962761
+Value: <YOUR_TELEGRAM_CHAT_ID>
 ```
 
 #### B) Gmail Secrets (App Password 재생성 후)
 ```
 Name: MAIL_USERNAME
-Value: mscho715@gmail.com
+Value: <YOUR_GMAIL_ADDRESS>
 
 Name: MAIL_PASSWORD
-Value: [새로운 16자리 App Password]
+Value: <YOUR_16_CHAR_APP_PASSWORD>
 
 Name: MAIL_TO
-Value: mscho715@gmail.com
+Value: <RECIPIENT_EMAIL>
 ```
 
 ## 🚀 테스트 순서
 
 ### 1단계: Telegram만 설정해서 테스트
 1. 위의 2개 Telegram Secrets만 설정
 2. GitHub Actions 워크플로우 실행
 3. Telegram 알림 수신 확인
 
 ### 2단계: Gmail App Password 재생성
 1. Google 계정 → 보안 → 2단계 인증 확인
 2. 새로운 App Password 생성
 3. Gmail Secrets 설정
 4. 전체 알림 시스템 테스트
 
 ## 🔧 Gmail App Password 문제 해결
 
 ### 현재 문제:
 - 535 오류: "Username and Password not accepted"
 - App Password 인증 실패
 
 ### 해결 방법:
 1. **2단계 인증 재확인**
    - Google 계정 → 보안 → 2단계 인증 활성화
 
diff --git a/scripts/demo_operability_integration.py b/scripts/demo_operability_integration.py
index 3ee64af0a0cdfbeebfc5ccdc1f327b8c7a8c2937..d25f0d562c12f54ba2fb1b05be3da8e5e6923117 100644
--- a/scripts/demo_operability_integration.py
+++ b/scripts/demo_operability_integration.py
@@ -1,287 +1,264 @@
 #!/usr/bin/env python3
-"""
-KR: 통합된 운항 가능성 예측 데모
-EN: Integrated operability prediction demo
-
-이 스크립트는 HVDC 해양 데이터 수집 시스템과 operability_package를 통합하여
-실제 기상 데이터를 기반으로 운항 가능성 예측을 수행합니다.
-"""
+"""KR: 운항 가능성 예측 데모 / EN: Operability prediction demo."""
 
+import argparse
+import os
 import sys
 import json
 import pandas as pd
 from pathlib import Path
-from datetime import datetime, timedelta
-from typing import List, Dict, Any
+from datetime import datetime, timedelta, timezone
+from typing import Any, Dict, List, Tuple
 
 # 프로젝트 루트를 Python 경로에 추가
 project_root = Path(__file__).parent.parent
 sys.path.insert(0, str(project_root))
 
-from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
-from src.marine_ops.operability.api import OperabilityPredictor, create_operability_report
+from src.marine_ops.core.schema import MarineTimeseries
+from src.marine_ops.operability.api import create_operability_report
 from src.marine_ops.connectors.stormglass import StormglassConnector
 from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
-from src.marine_ops.connectors.worldtides import fetch_worldtides_heights, create_marine_timeseries_from_worldtides
-from src.marine_ops.eri.compute import ERICalculator
+from src.marine_ops.connectors.worldtides import create_marine_timeseries_from_worldtides
+from scripts.offline_support import decide_execution_mode, generate_offline_dataset
+
+def collect_weather_data(mode: str = "auto") -> Tuple[List[MarineTimeseries], str, List[str]]:
+    """KR: 기상 데이터 수집 / EN: Collect marine weather data."""
 
-def collect_weather_data() -> List[MarineTimeseries]:
-    """실제 기상 데이터 수집"""
     print("🌊 기상 데이터 수집 중...")
-    
-    weather_data = []
-    
-    # UAE 해역 좌표 (Dubai 근처)
+
     lat, lon = 25.2048, 55.2708
-    
-    try:
-        # Stormglass 데이터 수집
-        print("  📡 Stormglass API에서 데이터 수집...")
-        sg_connector = StormglassConnector()
-        sg_data = sg_connector.get_marine_weather(lat, lon, days=7)
-        if sg_data and sg_data.data_points:
-            weather_data.append(sg_data)
-            print(f"    ✅ {len(sg_data.data_points)}개 데이터 포인트 수집")
-        else:
-            print("    ⚠️ Stormglass 데이터 없음")
-    except Exception as e:
-        print(f"    ❌ Stormglass 오류: {e}")
-    
+    forecast_hours = 24 * 7
+    start_time = datetime.now(timezone.utc)
+    end_time = start_time + timedelta(hours=forecast_hours)
+    required_secrets = ["STORMGLASS_API_KEY", "WORLDTIDES_API_KEY"]
+    missing_secrets = [key for key in required_secrets if not os.getenv(key)]
+    resolved_mode, offline_reasons = decide_execution_mode(mode, missing_secrets, ncm_available=True)
+
+    if resolved_mode == "offline":
+        synthetic_series, _ = generate_offline_dataset("UAE_Waters", forecast_hours)
+        if offline_reasons:
+            print(f"⚠️ 오프라인 모드 전환: {', '.join(offline_reasons)}")
+        return synthetic_series, resolved_mode, offline_reasons
+
+    weather_data: List[MarineTimeseries] = []
+
+    stormglass_key = os.getenv("STORMGLASS_API_KEY", "")
+    if stormglass_key:
+        try:
+            print("  📡 Stormglass API에서 데이터 수집...")
+            sg_connector = StormglassConnector(api_key=stormglass_key)
+            sg_data = sg_connector.get_marine_weather(
+                lat,
+                lon,
+                start_time,
+                end_time,
+                location="UAE_Waters",
+            )
+            if sg_data and sg_data.data_points:
+                weather_data.append(sg_data)
+                print(f"    ✅ {len(sg_data.data_points)}개 데이터 포인트 수집")
+            else:
+                print("    ⚠️ Stormglass 데이터 없음")
+        except Exception as error:
+            print(f"    ❌ Stormglass 오류: {error}")
+    else:
+        print("  ⚠️ Stormglass API 키 없음으로 건너뜀")
+
     try:
-        # Open-Meteo 데이터 수집
         print("  📡 Open-Meteo API에서 데이터 수집...")
         om_connector = OpenMeteoConnector()
-        om_data = om_connector.get_marine_weather(lat, lon, days=7)
+        om_data = om_connector.get_marine_weather(
+            lat,
+            lon,
+            start_time,
+            end_time,
+            location="UAE_Waters",
+        )
         if om_data and om_data.data_points:
             weather_data.append(om_data)
             print(f"    ✅ {len(om_data.data_points)}개 데이터 포인트 수집")
         else:
             print("    ⚠️ Open-Meteo 데이터 없음")
-    except Exception as e:
-        print(f"    ❌ Open-Meteo 오류: {e}")
-    
-    try:
-        # WorldTides 데이터 수집
-        print("  📡 WorldTides API에서 데이터 수집...")
-        wt_key = "a7b5bd88-041e-4316-8f8e-02670eb44bc7"  # API 키
-        wt_raw = fetch_worldtides_heights(lat, lon, wt_key, hours=168)  # 7일
-        if wt_raw and 'heights' in wt_raw:
-            wt_data = create_marine_timeseries_from_worldtides(wt_raw, lat, lon)
+    except Exception as error:
+        print(f"    ❌ Open-Meteo 오류: {error}")
+
+    worldtides_key = os.getenv("WORLDTIDES_API_KEY", "")
+    if worldtides_key:
+        try:
+            print("  📡 WorldTides API에서 데이터 수집...")
+            wt_data = create_marine_timeseries_from_worldtides(
+                lat,
+                lon,
+                worldtides_key,
+                forecast_hours,
+                "UAE_Waters",
+            )
             if wt_data and wt_data.data_points:
                 weather_data.append(wt_data)
                 print(f"    ✅ {len(wt_data.data_points)}개 데이터 포인트 수집")
             else:
-                print("    ⚠️ WorldTides 데이터 변환 실패")
-        else:
-            print("    ⚠️ WorldTides 데이터 없음")
-    except Exception as e:
-        print(f"    ❌ WorldTides 오류: {e}")
-    
-    print(f"📊 총 {len(weather_data)}개 소스에서 데이터 수집 완료")
-    return weather_data
+                print("    ⚠️ WorldTides 데이터 없음")
+        except Exception as error:
+            print(f"    ❌ WorldTides 오류: {error}")
+    else:
+        print("  ⚠️ WorldTides API 키 없음으로 건너뜀")
 
-def create_synthetic_ensemble_data() -> List[MarineTimeseries]:
-    """합성 앙상블 데이터 생성 (실제 데이터가 부족할 경우)"""
-    print("🎲 합성 앙상블 데이터 생성...")
-    
-    import random
-    import numpy as np
-    from datetime import datetime, timedelta
-    
-    random.seed(42)
-    np.random.seed(42)
-    
-    # 7일간의 시간별 데이터 생성
-    data_points = []
-    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
-    
-    for day in range(7):
-        for hour in range(0, 24, 3):  # 3시간 간격
-            timestamp = base_time + timedelta(days=day, hours=hour)
-            
-            # 시간과 날짜에 따른 파라미터 변화
-            day_factor = 1 + (day * 0.05)  # 날이 지날수록 조건 악화
-            hour_factor = 1 + 0.1 * np.sin(hour / 4.0)  # 시간에 따른 변화
-            
-            # 파고 (Hs) 생성
-            hs_base = 0.8 + (day * 0.1) * hour_factor
-            hs = max(0.1, np.random.normal(hs_base, 0.2))
-            
-            # 풍속 생성
-            wind_base = 15.0 + (day * 0.5) * hour_factor
-            wind = max(0.5, np.random.normal(wind_base, 3.0))
-            
-            # 풍향 생성
-            wind_dir = np.random.uniform(0, 360)
-            
-            data_point = MarineDataPoint(
-                timestamp=timestamp.isoformat(),
-                wind_speed=wind,
-                wind_direction=wind_dir,
-                wave_height=hs,
-                wave_period=np.random.uniform(6, 12),
-                wave_direction=wind_dir + np.random.uniform(-30, 30),
-                sea_state="Moderate" if hs < 1.5 else "Rough",
-                visibility=np.random.uniform(8, 15),
-                temperature=np.random.uniform(22, 28),
-                confidence=0.7  # 합성 데이터 신뢰도
-            )
-            data_points.append(data_point)
-    
-    # MarineTimeseries 객체 생성
-    synthetic_timeseries = MarineTimeseries(
-        source="synthetic_ensemble",
-        location="UAE_Waters",
-        data_points=data_points,
-        ingested_at=datetime.now().isoformat()
-    )
-    
-    print(f"    ✅ {len(data_points)}개 합성 데이터 포인트 생성")
-    return [synthetic_timeseries]
+    if not weather_data:
+        print("⚠️ 외부 데이터가 없어 합성 데이터로 대체합니다.")
+        synthetic_series, _ = generate_offline_dataset("UAE_Waters", forecast_hours)
+        weather_data = synthetic_series
+        offline_reasons.append("외부 데이터 수집 실패")
+        resolved_mode = "offline"
+
+    print(f"📊 총 {len(weather_data)}개 소스에서 데이터 수집 완료")
+    return weather_data, resolved_mode, offline_reasons
 
 def run_operability_prediction(weather_data: List[MarineTimeseries]) -> Dict[str, Any]:
-    """운항 가능성 예측 실행"""
+    """KR: 운항 가능성 예측 실행 / EN: Run operability prediction."""
     print("🚢 운항 가능성 예측 실행 중...")
     
     # 항로 정보 정의
     routes = [
         {
             "name": "Abu Dhabi to AGI or DAS",
             "distance_nm": 65.0,
             "planned_speed_kt": 12.0,
             "hs_forecast": 1.2
         }
     ]
     
     # 운항 가능성 보고서 생성
     report = create_operability_report(
         weather_data=weather_data,
         routes=routes,
         forecast_days=7
     )
     
     print(f"    ✅ {len(report['operability_forecasts'])}개 운항 가능성 예측 완료")
     print(f"    ✅ {len(report['eta_predictions'])}개 ETA 예측 완료")
     
     return report
 
 def save_results(report: Dict[str, Any], output_dir: Path):
-    """결과 저장"""
+    """KR: 결과 저장 / EN: Persist results."""
     print("💾 결과 저장 중...")
     
     # JSON 보고서 저장
     json_file = output_dir / "operability_report.json"
     with open(json_file, 'w', encoding='utf-8') as f:
         json.dump(report, f, indent=2, ensure_ascii=False, default=str)
     print(f"  ✅ JSON 보고서: {json_file}")
     
     # CSV 형식으로 운항 가능성 예측 저장
     if report['operability_forecasts']:
         csv_data = []
         for forecast in report['operability_forecasts']:
             csv_data.append({
                 'day': forecast.day,
                 'daypart': forecast.daypart,
                 'P_go': forecast.probabilities.P_go,
                 'P_cond': forecast.probabilities.P_cond,
                 'P_nogo': forecast.probabilities.P_nogo,
                 'decision': forecast.decision,
                 'confidence': forecast.confidence,
                 'gate_hs_go': forecast.gate_used.hs_go,
                 'gate_wind_go': forecast.gate_used.wind_go
             })
         
         df_forecasts = pd.DataFrame(csv_data)
         csv_file = output_dir / "operability_forecasts.csv"
         df_forecasts.to_csv(csv_file, index=False)
         print(f"  ✅ 운항 가능성 예측 CSV: {csv_file}")
     
     # ETA 예측 CSV 저장
     if report['eta_predictions']:
         eta_data = []
         for eta in report['eta_predictions']:
             eta_data.append({
                 'route': eta.route,
                 'distance_nm': eta.distance_nm,
                 'planned_speed_kt': eta.planned_speed_kt,
                 'effective_speed_kt': eta.effective_speed_kt,
                 'eta_hours': eta.eta_hours,
                 'buffer_minutes': eta.buffer_minutes,
                 'hs_impact': eta.hs_impact
             })
         
         df_eta = pd.DataFrame(eta_data)
         eta_csv_file = output_dir / "eta_predictions.csv"
         df_eta.to_csv(eta_csv_file, index=False)
         print(f"  ✅ ETA 예측 CSV: {eta_csv_file}")
 
 def print_summary(report: Dict[str, Any]):
-    """결과 요약 출력"""
+    """KR: 결과 요약 출력 / EN: Print result summary."""
     print("\n" + "="*60)
     print("📊 운항 가능성 예측 결과 요약")
     print("="*60)
     
     summary = report['summary']
     print(f"📅 예측 기간: {report['forecast_days']}일")
     print(f"📈 총 예측 수: {summary['total_forecasts']}")
     print(f"✅ GO: {summary['go_count']}개")
     print(f"⚠️  CONDITIONAL: {summary['conditional_count']}개")
     print(f"❌ NO-GO: {summary['nogo_count']}개")
     print(f"🎯 평균 신뢰도: {summary['average_confidence']:.2f}")
     
     print("\n🚢 ETA 예측:")
     for eta in report['eta_predictions']:
         print(f"  • {eta.route}: {eta.eta_hours:.1f}시간 "
               f"(계획: {eta.planned_speed_kt}kt → 실제: {eta.effective_speed_kt:.1f}kt)")
     
     print("\n📋 일별 운항 가능성 (최소 P_go):")
     day_summary = {}
     for forecast in report['operability_forecasts']:
         day = forecast.day
         if day not in day_summary:
             day_summary[day] = []
         day_summary[day].append(forecast.probabilities.P_go)
     
     for day in sorted(day_summary.keys()):
         min_p_go = min(day_summary[day])
         status = "🟢" if min_p_go > 0.5 else "🟡" if min_p_go > 0.3 else "🔴"
         print(f"  {status} {day}: P(Go) = {min_p_go:.2f}")
 
-def main():
-    """메인 함수"""
+def parse_args() -> argparse.Namespace:
+    """KR: CLI 인자 파싱 / EN: Parse CLI arguments."""
+
+    parser = argparse.ArgumentParser(description="HVDC Marine operability demo")
+    parser.add_argument("--mode", choices=["auto", "online", "offline"], default="auto", help="실행 모드 (auto/online/offline)")
+    parser.add_argument("--output", default="out", help="결과 출력 디렉터리")
+    return parser.parse_args()
+
+
+def main() -> None:
+    """KR: 데모 실행 / EN: Run demo."""
+
+    args = parse_args()
+
     print("🚢 HVDC 해양 운항 가능성 예측 시스템")
-    print("="*50)
-    
-    # 출력 디렉토리 생성
-    output_dir = Path("out")
-    output_dir.mkdir(exist_ok=True)
-    
+    print("=" * 50)
+
+    output_dir = Path(args.output)
+    output_dir.mkdir(exist_ok=True, parents=True)
+
     try:
-        # 1. 기상 데이터 수집
-        weather_data = collect_weather_data()
-        
-        # 실제 데이터가 부족하면 합성 데이터 추가
-        if len(weather_data) == 0 or sum(len(ts.data_points) for ts in weather_data) < 50:
-            print("⚠️ 실제 데이터가 부족하여 합성 데이터를 추가합니다...")
-            synthetic_data = create_synthetic_ensemble_data()
-            weather_data.extend(synthetic_data)
-        
-        # 2. 운항 가능성 예측 실행
+        weather_data, resolved_mode, offline_reasons = collect_weather_data(args.mode)
+        print(f"⚙️ 실행 모드: {resolved_mode}")
+        if offline_reasons:
+            print("  ↳ 사유: " + ", ".join(offline_reasons))
+
         report = run_operability_prediction(weather_data)
-        
-        # 3. 결과 저장
         save_results(report, output_dir)
-        
-        # 4. 요약 출력
         print_summary(report)
-        
+
         print(f"\n✅ 운항 가능성 예측 완료! 결과는 {output_dir} 디렉토리에 저장되었습니다.")
-        
-    except Exception as e:
-        print(f"\n❌ 오류 발생: {e}")
+
+    except Exception as error:
+        print(f"\n❌ 오류 발생: {error}")
         import traceback
         traceback.print_exc()
         sys.exit(1)
 
+
 if __name__ == "__main__":
     main()
diff --git a/scripts/offline_support.py b/scripts/offline_support.py
new file mode 100644
index 0000000000000000000000000000000000000000..83f8a7804ff0191f37da949aa1f402cd31b8b7a0
--- /dev/null
+++ b/scripts/offline_support.py
@@ -0,0 +1,90 @@
+"""KR: GitHub Actions용 오프라인 지원 유틸 / EN: Offline support utilities for GitHub Actions."""
+from __future__ import annotations
+
+import os
+import math
+from datetime import datetime, timedelta, timezone
+from typing import Dict, List, Sequence, Tuple
+
+from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries
+
+
+def decide_execution_mode(requested_mode: str, missing_secrets: Sequence[str], ncm_available: bool) -> Tuple[str, List[str]]:
+    """KR: 실행 모드 결정 / EN: Decide execution mode."""
+
+    normalized = requested_mode.lower()
+    if normalized not in {"auto", "online", "offline"}:
+        raise ValueError(f"지원하지 않는 실행 모드입니다: {requested_mode}")
+
+    reasons: List[str] = []
+
+    if normalized == "offline":
+        reasons.append("사용자 지정 오프라인 모드")
+        return "offline", reasons
+
+    if normalized == "online":
+        return "online", reasons
+
+    if os.getenv("CI", "").lower() == "true":
+        reasons.append("CI 환경 자동 전환")
+
+    if missing_secrets:
+        reasons.append(f"필수 시크릿 누락: {', '.join(missing_secrets)}")
+
+    if not ncm_available:
+        reasons.append("NCM Selenium 모듈 미로드")
+
+    resolved_mode = "offline" if reasons else "online"
+    return resolved_mode, reasons
+
+
+def generate_offline_dataset(location: str, forecast_hours: int) -> Tuple[List[MarineTimeseries], Dict[str, Dict[str, float]]]:
+    """KR: 합성 해양 시계열 생성 / EN: Generate synthetic marine timeseries."""
+    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
+    data_points: List[MarineDataPoint] = []
+
+    for hour in range(max(forecast_hours, 6)):
+        timestamp = now + timedelta(hours=hour)
+        phase = hour / 6.0
+        wind_speed = 8.5 + 1.8 * math.sin(phase)
+        wind_direction = (120 + 20 * math.cos(phase * 0.8)) % 360
+        wind_gust = wind_speed * 1.15
+        wave_height = 0.6 + 0.25 * math.sin(phase + 0.6)
+        wave_period = 7.5 + 0.4 * math.cos(phase)
+        visibility = 11.0 - 0.8 * math.sin(phase * 0.5)
+        temperature = 27.0 - 0.6 * math.cos(phase * 0.9)
+        sea_state = "Slight" if wave_height < 1.0 else "Moderate"
+
+        data_points.append(
+            MarineDataPoint(
+                timestamp=timestamp.isoformat(),
+                wind_speed=round(wind_speed, 2),
+                wind_direction=round(wind_direction, 2),
+                wave_height=round(wave_height, 2),
+                wind_gust=round(wind_gust, 2),
+                wave_period=round(wave_period, 2),
+                wave_direction=round((wind_direction + 5) % 360, 2),
+                sea_state=sea_state,
+                visibility=round(max(4.0, visibility), 2),
+                temperature=round(temperature, 2),
+                confidence=0.7,
+            )
+        )
+
+    synthetic_series = MarineTimeseries(
+        source="synthetic_offline",
+        location=location,
+        data_points=data_points,
+        ingested_at=datetime.now(timezone.utc).isoformat(),
+        confidence=0.7,
+    )
+
+    statuses: Dict[str, Dict[str, float]] = {
+        "STORMGLASS": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
+        "OPEN_METEO": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
+        "NCM_SELENIUM": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
+        "WORLDTIDES": {"status": "⚠️ 오프라인 모드", "confidence": 0.0},
+        "SYNTHETIC": {"status": "✅ 오프라인 합성 데이터", "confidence": synthetic_series.confidence or 0.7},
+    }
+
+    return [synthetic_series], statuses
diff --git a/scripts/secret_helpers.py b/scripts/secret_helpers.py
new file mode 100644
index 0000000000000000000000000000000000000000..3539251cb503d35e9b368077b86d480e880343cd
--- /dev/null
+++ b/scripts/secret_helpers.py
@@ -0,0 +1,29 @@
+"""KR: 시크릿 로드/마스킹 유틸 / EN: Helpers to load and mask secrets."""
+from __future__ import annotations
+
+import os
+from typing import Final
+
+MISSING_MARK: Final[str] = "[missing]"
+
+
+def load_secret(name: str, allow_empty: bool = False) -> str:
+    """KR: 환경 시크릿 로드 / EN: Load secret from environment."""
+    value = os.getenv(name, "").strip()
+    if value:
+        return value
+    if allow_empty:
+        return ""
+    raise RuntimeError(
+        f"환경 변수 {name}이(가) 설정되지 않았습니다. "
+        "GitHub Secrets 또는 .env 파일을 확인하세요."
+    )
+
+
+def mask_secret(value: str) -> str:
+    """KR: 시크릿 마스킹 / EN: Mask secret for logs."""
+    if not value:
+        return MISSING_MARK
+    if len(value) <= 8:
+        return "*" * len(value)
+    return f"{value[:4]}…{value[-4:]}"
diff --git a/scripts/weather_job.py b/scripts/weather_job.py
index 27b12faf118ed05277a848f71abc0a1268f8afde..b8e127372794d0c70f6e74973a883d67f04577fe 100644
--- a/scripts/weather_job.py
+++ b/scripts/weather_job.py
@@ -1,147 +1,189 @@
 #!/usr/bin/env python3
 """
 GitHub Actions용 해양 날씨 작업 스크립트
 매시간 실행되어 해양 날씨 데이터를 수집하고 요약 보고서를 생성합니다.
 """
 
 import os
 import sys
 import json
 import argparse
 from pathlib import Path
 from datetime import datetime, timedelta
+from typing import List
+
 import pandas as pd
 
 # 프로젝트 루트를 Python 경로에 추가
 project_root = Path(__file__).parent.parent
 sys.path.insert(0, str(project_root))
 
 from src.marine_ops.connectors.stormglass import StormglassConnector, LOCATIONS as SG_LOCATIONS
 from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
 from src.marine_ops.connectors.worldtides import create_marine_timeseries_from_worldtides
-from ncm_web.ncm_selenium_ingestor import NCMSeleniumIngestor
 from src.marine_ops.eri.compute import ERICalculator
 from src.marine_ops.decision.fusion import ForecastFusion, OperationalDecisionMaker
-from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint, OperationalDecision, ERIPoint
+from src.marine_ops.core.schema import MarineTimeseries, ERIPoint
+from scripts.offline_support import decide_execution_mode, generate_offline_dataset
+
+try:
+    from ncm_web.ncm_selenium_ingestor import NCMSeleniumIngestor
 
+    NCM_IMPORT_ERROR: Exception | None = None
+except Exception as import_error:  # pragma: no cover - import guard
+    NCMSeleniumIngestor = None  # type: ignore[assignment]
+    NCM_IMPORT_ERROR = import_error
 def load_config(config_path: str) -> dict:
     """설정 파일 로드"""
     try:
         with open(config_path, 'r', encoding='utf-8') as f:
             if config_path.endswith('.yml') or config_path.endswith('.yaml'):
                 import yaml
                 return yaml.safe_load(f)
             else:
                 return json.load(f)
     except FileNotFoundError:
         print(f"설정 파일을 찾을 수 없습니다: {config_path}")
         return {}
 
-def collect_weather_data(location_name: str = "AGI", forecast_hours: int = 24) -> dict:
+def collect_weather_data(location_name: str = "AGI", forecast_hours: int = 24, mode: str = "auto") -> dict:
     """해양 날씨 데이터 수집"""
     print(f"🌊 {location_name} 해역 날씨 데이터 수집 시작...")
-    
+
     lat, lon = SG_LOCATIONS[location_name]['lat'], SG_LOCATIONS[location_name]['lon']
     now = datetime.now()
     end_date = now + timedelta(hours=forecast_hours)
-    
-    all_timeseries = []
-    api_status = {}
-    
+
+    required_secrets = ["STORMGLASS_API_KEY", "WORLDTIDES_API_KEY"]
+    missing_secrets = [key for key in required_secrets if not os.getenv(key)]
+    resolved_mode, offline_reasons = decide_execution_mode(mode, missing_secrets, NCMSeleniumIngestor is not None)
+
+    if resolved_mode == "offline":
+        synthetic_series, statuses = generate_offline_dataset(location_name, forecast_hours)
+        if offline_reasons:
+            print(f"⚠️ 오프라인 모드 전환: {', '.join(offline_reasons)}")
+        return {
+            'timeseries': synthetic_series,
+            'api_status': statuses,
+            'location': location_name,
+            'forecast_hours': forecast_hours,
+            'collected_at': now.isoformat(),
+            'mode': resolved_mode,
+            'offline_reasons': offline_reasons,
+        }
+
+    all_timeseries: List[MarineTimeseries] = []
+    api_status: dict[str, dict[str, float]] = {}
+
     # API 키 로드
     stormglass_key = os.getenv('STORMGLASS_API_KEY', '')
     worldtides_key = os.getenv('WORLDTIDES_API_KEY', '')
-    
+
     # 1. Stormglass 데이터 수집
     try:
         if stormglass_key:
             sg_connector = StormglassConnector(api_key=stormglass_key)
             sg_timeseries = sg_connector.get_marine_weather(lat, lon, now, end_date, location=location_name)
             all_timeseries.append(sg_timeseries)
             api_status['STORMGLASS'] = {
                 'status': '✅ 실제 데이터',
                 'confidence': getattr(sg_timeseries, 'confidence', 0.5)
             }
             print(f"✅ Stormglass: {len(sg_timeseries.data_points)}개 데이터 포인트")
         else:
             api_status['STORMGLASS'] = {'status': '❌ API 키 없음', 'confidence': 0.0}
             print("❌ Stormglass API 키 없음")
     except Exception as e:
         print(f"❌ Stormglass 수집 실패: {e}")
         api_status['STORMGLASS'] = {'status': '❌ 실패', 'confidence': 0.0}
-    
+
     # 2. Open-Meteo 데이터 수집
     try:
         om_connector = OpenMeteoConnector()
         om_timeseries = om_connector.get_marine_weather(lat, lon, now, end_date, location=location_name)
         all_timeseries.append(om_timeseries)
         api_status['OPEN_METEO'] = {
             'status': '✅ 실제 데이터',
             'confidence': getattr(om_timeseries, 'confidence', 0.5)
         }
         print(f"✅ Open-Meteo: {len(om_timeseries.data_points)}개 데이터 포인트")
     except Exception as e:
         print(f"❌ Open-Meteo 수집 실패: {e}")
         api_status['OPEN_METEO'] = {'status': '❌ 실패', 'confidence': 0.0}
-    
+
     # 3. NCM Selenium 데이터 수집
-    try:
-        ncm_ingestor = NCMSeleniumIngestor(headless=True)
-        ncm_timeseries = ncm_ingestor.create_marine_timeseries(location=location_name, forecast_hours=forecast_hours)
-        all_timeseries.append(ncm_timeseries)
-        api_status['NCM_SELENIUM'] = {
-            'status': '✅ 실제 데이터' if "fallback" not in ncm_timeseries.source else '⚠️ 폴백 데이터', 
-            'confidence': getattr(ncm_timeseries, 'confidence', 0.5)
-        }
-        print(f"✅ NCM Selenium: {len(ncm_timeseries.data_points)}개 데이터 포인트")
-    except Exception as e:
-        print(f"❌ NCM Selenium 수집 실패: {e}")
-        api_status['NCM_SELENIUM'] = {'status': '❌ 실패', 'confidence': 0.0}
-    
+    if NCMSeleniumIngestor is None:
+        api_status['NCM_SELENIUM'] = {'status': '❌ 모듈 누락', 'confidence': 0.0}
+        if NCM_IMPORT_ERROR is not None:
+            print(f"❌ NCM Selenium 로드 실패: {NCM_IMPORT_ERROR}")
+    else:
+        try:
+            ncm_ingestor = NCMSeleniumIngestor(headless=True)
+            ncm_timeseries = ncm_ingestor.create_marine_timeseries(location=location_name, forecast_hours=forecast_hours)
+            all_timeseries.append(ncm_timeseries)
+            api_status['NCM_SELENIUM'] = {
+                'status': '✅ 실제 데이터' if "fallback" not in ncm_timeseries.source else '⚠️ 폴백 데이터',
+                'confidence': getattr(ncm_timeseries, 'confidence', 0.5)
+            }
+            print(f"✅ NCM Selenium: {len(ncm_timeseries.data_points)}개 데이터 포인트")
+        except Exception as e:
+            print(f"❌ NCM Selenium 수집 실패: {e}")
+            api_status['NCM_SELENIUM'] = {'status': '❌ 실패', 'confidence': 0.0}
+
     # 4. WorldTides 데이터 수집 (선택사항)
     if worldtides_key:
         try:
             wt_timeseries = create_marine_timeseries_from_worldtides(lat, lon, worldtides_key, forecast_hours, location_name)
             all_timeseries.append(wt_timeseries)
             api_status['WORLDTIDES'] = {
                 'status': '✅ 실제 데이터',
                 'confidence': getattr(wt_timeseries, 'confidence', 0.5)
             }
             print(f"✅ WorldTides: {len(wt_timeseries.data_points)}개 데이터 포인트")
         except Exception as e:
             print(f"⚠️ WorldTides 수집 실패: {e}")
             api_status['WORLDTIDES'] = {'status': '⚠️ 크레딧 부족', 'confidence': 0.3}
     else:
         api_status['WORLDTIDES'] = {'status': '❌ API 키 없음', 'confidence': 0.0}
-    
+
+    if not all_timeseries:
+        print("⚠️ 외부 데이터가 없어 합성 데이터로 대체합니다.")
+        synthetic_series, synthetic_status = generate_offline_dataset(location_name, forecast_hours)
+        all_timeseries.extend(synthetic_series)
+        api_status.update(synthetic_status)
+        offline_reasons.append("외부 데이터 수집 실패")
+        resolved_mode = "offline"
+
     return {
         'timeseries': all_timeseries,
         'api_status': api_status,
         'location': location_name,
         'forecast_hours': forecast_hours,
-        'collected_at': now.isoformat()
+        'collected_at': now.isoformat(),
+        'mode': resolved_mode,
+        'offline_reasons': offline_reasons,
     }
 
 def analyze_weather_data(data: dict) -> dict:
     """수집된 날씨 데이터 분석"""
     print("📊 날씨 데이터 분석 중...")
     
     all_timeseries = data['timeseries']
     if not all_timeseries:
         return {'error': '수집된 데이터가 없습니다'}
     
     # ERI 계산
     eri_calculator = ERICalculator()
     all_eri_points = []
     
     for timeseries in all_timeseries:
         eri_points = eri_calculator.compute_eri_timeseries(timeseries)
         all_eri_points.extend(eri_points)
     
     # 예보 융합
     fusion_settings = {
         'ncm_weight': 0.60,
         'system_weight': 0.40,
         'alpha': 0.7,
         'beta': 0.3
     }
@@ -179,151 +221,164 @@ def analyze_weather_data(data: dict) -> dict:
         'decisions': {
             'total': len(decisions),
             'GO': go_count,
             'CONDITIONAL': conditional_count,
             'NO-GO': no_go_count
         },
         'averages': {
             'eri': avg_eri,
             'wind_speed_ms': avg_wind_speed,
             'wave_height_m': avg_wave_height
         },
         'eri_points': len(all_eri_points),
         'confidence_scores': [getattr(ts, 'confidence', 0.5) for ts in all_timeseries]
     }
 
 def generate_summary_report(data: dict, analysis: dict, output_dir: str) -> dict:
     """요약 보고서 생성"""
     print("📝 요약 보고서 생성 중...")
     
     output_path = Path(output_dir)
     output_path.mkdir(exist_ok=True)
     
     timestamp = datetime.now().strftime("%Y%m%d_%H%M")
     
     # JSON 요약
+    execution_mode = data.get('mode', 'online')
+    success_sources = sum(1 for status in data['api_status'].values() if '✅' in status['status'])
+    total_sources = max(len(data['api_status']), 1)
+    collection_rate = success_sources / total_sources * 100
     summary_json = {
         'metadata': {
             'generated_at': datetime.now().isoformat(),
             'location': data['location'],
             'forecast_hours': data['forecast_hours'],
-            'system_version': 'v2.1'
+            'system_version': 'v2.1',
+            'execution_mode': execution_mode,
         },
         'api_status': data['api_status'],
         'analysis': analysis,
         'collection_stats': {
             'total_timeseries': len(data['timeseries']),
             'total_data_points': analysis.get('total_data_points', 0),
-            'data_collection_rate': len([s for s in data['api_status'].values() if '✅' in s['status']]) / len(data['api_status']) * 100
+            'data_collection_rate': collection_rate,
         }
     }
+
+    if data.get('offline_reasons'):
+        summary_json['metadata']['offline_reasons'] = data['offline_reasons']
     
     json_path = output_path / f"summary_{timestamp}.json"
     with open(json_path, 'w', encoding='utf-8') as f:
         json.dump(summary_json, f, ensure_ascii=False, indent=2)
     
     # CSV 요약
     csv_data = []
     for api_name, status in data['api_status'].items():
         csv_data.append({
             'API': api_name,
             'Status': status['status'],
             'Confidence': status['confidence'],
             'Timestamp': datetime.now().isoformat()
         })
     
     csv_path = output_path / f"api_status_{timestamp}.csv"
     df = pd.DataFrame(csv_data)
     df.to_csv(csv_path, index=False, encoding='utf-8')
     
     # 텍스트 요약
     txt_content = f"""🌊 UAE 해역 해양 날씨 보고서
 ========================================
 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
 위치: {data['location']} (Al Ghallan Island)
 예보 기간: {data['forecast_hours']}시간
-
-📊 데이터 수집 현황:
+실행 모드: {execution_mode.upper()}
 """
-    
+
+    if data.get('offline_reasons'):
+        txt_content += "오프라인 사유: " + "; ".join(data['offline_reasons']) + "\n"
+
+    txt_content += "\n📊 데이터 수집 현황:\n"
+
     for api_name, status in data['api_status'].items():
         conf = status.get('confidence', None)
         conf_txt = f"{conf:.2f}" if isinstance(conf, (int, float)) else "N/A"
         txt_content += f"  {api_name}: {status['status']} (신뢰도: {conf_txt})\n"
     
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
     
     txt_path = output_path / "summary.txt"
     with open(txt_path, 'w', encoding='utf-8') as f:
         f.write(txt_content)
     
     print(f"✅ 요약 보고서 생성 완료:")
     print(f"  - JSON: {json_path}")
     print(f"  - CSV: {csv_path}")
     print(f"  - TXT: {txt_path}")
     
     return {
         'json_path': str(json_path),
         'csv_path': str(csv_path),
         'txt_path': str(txt_path),
         'summary_json': summary_json
     }
 
 def main():
     """메인 함수"""
     parser = argparse.ArgumentParser(description='GitHub Actions 해양 날씨 작업')
     parser.add_argument('--config', default='config/locations.yml', help='설정 파일 경로')
     parser.add_argument('--out', default='out', help='출력 디렉터리')
     parser.add_argument('--location', default='AGI', help='위치 코드')
     parser.add_argument('--hours', type=int, default=24, help='예보 시간')
+    parser.add_argument('--mode', choices=['auto', 'online', 'offline'], default='auto', help='실행 모드 (auto/online/offline)')
     
     args = parser.parse_args()
     
     print("🤖 GitHub Actions 해양 날씨 작업 시작")
     print("=" * 50)
     
     try:
         # 설정 로드
         config = load_config(args.config)
         print(f"✅ 설정 로드: {args.config}")
         
         # 날씨 데이터 수집
-        data = collect_weather_data(args.location, args.hours)
+        data = collect_weather_data(args.location, args.hours, args.mode)
         
         # 데이터 분석
         analysis = analyze_weather_data(data)
         
         # 요약 보고서 생성
         report = generate_summary_report(data, analysis, args.out)
         
         # 운항 가능성 예측 실행
         try:
             print("\n🚢 운항 가능성 예측 실행 중...")
             from src.marine_ops.operability.api import create_operability_report
             
             # 항로 정보 정의
             routes = [
                 {
                     "name": "Abu Dhabi to AGI or DAS",
                     "distance_nm": 65.0,
                     "planned_speed_kt": 12.0,
                     "hs_forecast": 1.2
                 }
             ]
             
             # 운항 가능성 보고서 생성
             # data는 딕셔너리이므로 MarineTimeseries 리스트 추출
             weather_timeseries = data.get('timeseries', [])
diff --git a/test_gmail_correct.py b/test_gmail_correct.py
index bd7dfcb9149e0957cd66256c745b4c12a65ca45e..2d3b869d4d123347e08a91d2128cf82f8a86b543 100644
--- a/test_gmail_correct.py
+++ b/test_gmail_correct.py
@@ -1,82 +1,86 @@
 #!/usr/bin/env python3
+"""KR: Gmail 알림 텍스트 검증 / EN: Gmail notification plain-text test."""
+
+from __future__ import annotations
+
+import os
 import smtplib
-from email.mime.text import MIMEText
-from email.mime.multipart import MIMEMultipart
 from datetime import datetime
+from email.mime.multipart import MIMEMultipart
+from email.mime.text import MIMEText
+
+from scripts.secret_helpers import load_secret, mask_secret
+
+
+def main() -> None:
+    """KR: Gmail 발송 확인 / EN: Validate Gmail delivery."""
+
+    try:
+        username = load_secret("MAIL_USERNAME")
+        password = load_secret("MAIL_PASSWORD")
+        to_email = load_secret("MAIL_TO")
+    except RuntimeError as error:
+        print(f"❌ 환경 변수 누락: {error}")
+        print("ℹ️ .env 파일 또는 GitHub Secrets에서 값을 설정하세요.")
+        return
+
+    print("📧 Gmail 설정 테스트 (공백 제거)...")
+    print(f"✅ Gmail 사용자명: {username}")
+    print(f"✅ 수신자: {to_email}")
+    print(f"✅ App Password: {mask_secret(password)}")
+
+    try:
+        print("\n📡 Gmail SMTP 연결 중...")
+        server = smtplib.SMTP("smtp.gmail.com", 587)
+        server.starttls()
+
+        print("🔐 Gmail 로그인 시도 중...")
+        server.login(username, password)
+        print("✅ Gmail SMTP 로그인 성공!")
+
+        msg = MIMEMultipart("alternative")
+        msg["Subject"] = "🔍 HVDC Marine Weather System - Gmail 설정 성공"
+        msg["From"] = f"HVDC Weather Bot <{username}>"
+        msg["To"] = to_email
+
+        text_content = (
+            "🌊 HVDC Marine Weather System - Gmail 설정 성공\n\n"
+            f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
+            f"Gmail 사용자명: {username}\n"
+            f"수신자: {to_email}\n\n"
+            "✅ Gmail 설정이 완료되었습니다!\n"
+            "✅ GitHub Actions에서 이메일 알림이 정상 작동할 것입니다!\n\n"
+            "---\nHVDC Project - Samsung C&T Logistics"
+        )
+
+        text_part = MIMEText(text_content, "plain", "utf-8")
+        msg.attach(text_part)
+
+        print("📤 테스트 이메일 발송 중...")
+        server.sendmail(username, to_email, msg.as_string())
+        server.quit()
+
+        print("✅ Gmail 테스트 이메일 발송 성공!")
+
+        print("\n🎉 모든 알림 시스템 설정 완료!")
+        print("\n📋 GitHub Secrets 설정 상태:")
+        print("=" * 60)
+        print(f"TELEGRAM_BOT_TOKEN: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
+        print(f"TELEGRAM_CHAT_ID: {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}")
+        print(f"MAIL_USERNAME: {username}")
+        print(f"MAIL_PASSWORD: {mask_secret(password)}")
+        print(f"MAIL_TO: {to_email}")
+        print("\n🔧 GitHub Settings에서 위의 5개 시크릿을 설정하세요!")
+
+    except smtplib.SMTPAuthenticationError as error:
+        print(f"❌ Gmail 인증 실패: {error}")
+        print("\n⚠️ Gmail App Password 문제:")
+        print("1. Google 계정 → 보안 → 2단계 인증 활성화 여부 확인")
+        print("2. 새로운 App Password를 생성")
+        print("3. App Password는 16자리여야 합니다")
+    except Exception as error:  # pragma: no cover - diagnostic helper
+        print(f"❌ Gmail 연결 실패: {error}")
+
 
-# Gmail 설정 - 공백 제거된 App Password
-username = "mscho715@gmail.com"
-password = "svomdxwnvdzep"  # 공백 제거
-to_email = "mscho715@gmail.com"
-
-print("📧 Gmail 설정 테스트 (공백 제거)...")
-print(f"✅ Gmail 사용자명: {username}")
-print(f"✅ 수신자: {to_email}")
-print(f"✅ App Password: {password}")
-
-try:
-    # SMTP 연결 테스트
-    print("\n📡 Gmail SMTP 연결 중...")
-    server = smtplib.SMTP('smtp.gmail.com', 587)
-    server.starttls()
-    
-    print("🔐 Gmail 로그인 시도 중...")
-    server.login(username, password)
-    print("✅ Gmail SMTP 로그인 성공!")
-    
-    # 테스트 이메일 작성
-    msg = MIMEMultipart('alternative')
-    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 성공"
-    msg['From'] = f"HVDC Weather Bot <{username}>"
-    msg['To'] = to_email
-    
-    text_content = f"""🌊 HVDC Marine Weather System - Gmail 설정 성공
-
-테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-Gmail 사용자명: {username}
-수신자: {to_email}
-
-✅ Gmail 설정이 완료되었습니다!
-✅ GitHub Actions에서 이메일 알림이 정상 작동할 것입니다!
-
----
-HVDC Project - Samsung C&T Logistics"""
-    
-    text_part = MIMEText(text_content, 'plain', 'utf-8')
-    msg.attach(text_part)
-    
-    # 이메일 발송
-    print("📤 테스트 이메일 발송 중...")
-    server.sendmail(username, to_email, msg.as_string())
-    server.quit()
-    
-    print("✅ Gmail 테스트 이메일 발송 성공!")
-    
-    print("\n🎉 모든 알림 시스템 설정 완료!")
-    print("\n📋 GitHub Secrets 설정 정보:")
-    print("=" * 60)
-    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
-    print("TELEGRAM_CHAT_ID: 470962761")
-    print(f"MAIL_USERNAME: {username}")
-    print(f"MAIL_PASSWORD: {password}")
-    print(f"MAIL_TO: {to_email}")
-    print("\n🔧 이제 GitHub Settings에서 위의 5개 시크릿을 설정하세요!")
-    
-except smtplib.SMTPAuthenticationError as e:
-    print(f"❌ Gmail 인증 실패: {e}")
-    print("\n⚠️ Gmail App Password 문제:")
-    print("1. Google 계정 → 보안 → 2단계 인증이 활성화되어 있는지 확인")
-    print("2. 새로운 App Password를 생성해보세요")
-    print("3. App Password는 16자리여야 합니다")
-    
-    # 임시로 GitHub Secrets 설정 정보만 제공
-    print("\n📋 GitHub Secrets 설정 정보 (Telegram은 정상):")
-    print("=" * 60)
-    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
-    print("TELEGRAM_CHAT_ID: 470962761")
-    print("MAIL_USERNAME: [Gmail 주소]")
-    print("MAIL_PASSWORD: [16자리 앱 비밀번호]")
-    print("MAIL_TO: [수신자 이메일]")
-    
-except Exception as e:
-    print(f"❌ Gmail 연결 실패: {e}")
+if __name__ == "__main__":
+    main()
diff --git a/test_gmail_final.py b/test_gmail_final.py
index 20d30b392ed771e710ebb4e3c133e59589dc634e..1553d1d9bb5ed104bf360f6f08b7906796236c21 100644
--- a/test_gmail_final.py
+++ b/test_gmail_final.py
@@ -1,76 +1,87 @@
 #!/usr/bin/env python3
+"""KR: Gmail 알림 최종 점검 / EN: Final Gmail notification check."""
+
+from __future__ import annotations
+
+import os
 import smtplib
-from email.mime.text import MIMEText
-from email.mime.multipart import MIMEMultipart
 from datetime import datetime
+from email.mime.multipart import MIMEMultipart
+from email.mime.text import MIMEText
+
+from scripts.secret_helpers import load_secret, mask_secret
+
+
+def main() -> None:
+    """KR: 최종 Gmail 검증 / EN: Perform final Gmail verification."""
+
+    try:
+        username = load_secret("MAIL_USERNAME")
+        password = load_secret("MAIL_PASSWORD")
+        to_email = load_secret("MAIL_TO")
+    except RuntimeError as error:
+        print(f"❌ 환경 변수 누락: {error}")
+        print("ℹ️ .env 파일 또는 GitHub Secrets에서 값을 설정하세요.")
+        return
+
+    print("📧 Gmail 설정 테스트 (최종)...")
+    print(f"✅ Gmail 사용자명: {username}")
+    print(f"✅ 수신자: {to_email}")
+    print(f"✅ App Password: {mask_secret(password)}")
+
+    try:
+        print("\n📡 Gmail SMTP 연결 중...")
+        server = smtplib.SMTP("smtp.gmail.com", 587)
+        server.starttls()
+
+        print("🔐 Gmail 로그인 시도 중...")
+        server.login(username, password)
+        print("✅ Gmail SMTP 로그인 성공!")
+
+        print("📝 테스트 이메일 작성 중...")
+        msg = MIMEMultipart("alternative")
+        msg["Subject"] = "🔍 HVDC Marine Weather System - Gmail 설정 검증 성공"
+        msg["From"] = f"HVDC Weather Bot <{username}>"
+        msg["To"] = to_email
+
+        text_content = (
+            "🌊 HVDC Marine Weather System - Gmail 설정 검증 성공\n\n"
+            f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
+            f"Gmail 사용자명: {username}\n"
+            f"수신자: {to_email}\n\n"
+            "✅ 이 이메일이 수신되면 Gmail 설정이 완료되었습니다!\n"
+            "✅ App Password가 올바르게 작동합니다!\n\n"
+            "---\nHVDC Project - Samsung C&T Logistics\n"
+            "Marine Weather Notification System"
+        )
+
+        text_part = MIMEText(text_content, "plain", "utf-8")
+        msg.attach(text_part)
+
+        print("📤 테스트 이메일 발송 중...")
+        server.sendmail(username, to_email, msg.as_string())
+        server.quit()
+
+        print("✅ Gmail 테스트 이메일 발송 성공!")
+
+        print("\n🎉 모든 설정이 완료되었습니다!")
+        print("\n📋 GitHub Secrets 설정 상태:")
+        print("=" * 50)
+        print(f"TELEGRAM_BOT_TOKEN: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
+        print(f"TELEGRAM_CHAT_ID: {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}")
+        print(f"MAIL_USERNAME: {username}")
+        print(f"MAIL_PASSWORD: {mask_secret(password)}")
+        print(f"MAIL_TO: {to_email}")
+
+    except smtplib.SMTPAuthenticationError as error:
+        print(f"❌ Gmail 인증 실패: {error}")
+        print("\n🔧 문제 해결:")
+        print("1. App Password가 올바른지 확인")
+        print("2. 2단계 인증이 활성화되어 있는지 확인")
+        print("3. App Password 생성 시 공백 제거 확인")
+    except Exception as error:  # pragma: no cover - diagnostic helper
+        print(f"❌ Gmail 연결 실패: {error}")
+
 
-# Gmail 설정
-username = "mscho715@gmail.com"
-password = "svomdxwnvdzep"  # App Password (공백 제거)
-to_email = "mscho715@gmail.com"
-
-print("📧 Gmail 설정 테스트 (최종)...")
-print(f"✅ Gmail 사용자명: {username}")
-print(f"✅ 수신자: {to_email}")
-print(f"✅ App Password: {password}")
-
-try:
-    # SMTP 연결 테스트
-    print("\n📡 Gmail SMTP 연결 중...")
-    server = smtplib.SMTP('smtp.gmail.com', 587)
-    server.starttls()
-    
-    print("🔐 Gmail 로그인 시도 중...")
-    server.login(username, password)
-    print("✅ Gmail SMTP 로그인 성공!")
-    
-    # 테스트 이메일 작성
-    print("📝 테스트 이메일 작성 중...")
-    msg = MIMEMultipart('alternative')
-    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 검증 성공"
-    msg['From'] = f"HVDC Weather Bot <{username}>"
-    msg['To'] = to_email
-    
-    # 간단한 텍스트 메시지
-    text_content = f"""
-🌊 HVDC Marine Weather System - Gmail 설정 검증 성공
-
-테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-Gmail 사용자명: {username}
-수신자: {to_email}
-
-✅ 이 이메일이 수신되면 Gmail 설정이 완료되었습니다!
-✅ App Password가 올바르게 작동합니다!
-
----
-HVDC Project - Samsung C&T Logistics
-Marine Weather Notification System
-    """
-    
-    text_part = MIMEText(text_content, 'plain', 'utf-8')
-    msg.attach(text_part)
-    
-    # 이메일 발송
-    print("📤 테스트 이메일 발송 중...")
-    server.sendmail(username, to_email, msg.as_string())
-    server.quit()
-    
-    print("✅ Gmail 테스트 이메일 발송 성공!")
-    
-    print("\n🎉 모든 설정이 완료되었습니다!")
-    print("\n📋 GitHub Secrets 설정 정보:")
-    print("=" * 50)
-    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
-    print("TELEGRAM_CHAT_ID: 470962761")
-    print(f"MAIL_USERNAME: {username}")
-    print(f"MAIL_PASSWORD: {password}")
-    print(f"MAIL_TO: {to_email}")
-    
-except smtplib.SMTPAuthenticationError as e:
-    print(f"❌ Gmail 인증 실패: {e}")
-    print("\n🔧 문제 해결:")
-    print("1. App Password가 올바른지 확인")
-    print("2. 2단계 인증이 활성화되어 있는지 확인")
-    print("3. App Password 생성 시 공백 제거 확인")
-except Exception as e:
-    print(f"❌ Gmail 연결 실패: {e}")
+if __name__ == "__main__":
+    main()
diff --git a/test_gmail_new_password.py b/test_gmail_new_password.py
index dcbfaa6c6b25410dbe7b5529a6271af74fb59a4c..75031b81a824a811a5f99c044d78b6632b89e3bc 100644
--- a/test_gmail_new_password.py
+++ b/test_gmail_new_password.py
@@ -1,110 +1,125 @@
 #!/usr/bin/env python3
+"""KR: 새로운 Gmail 앱 비밀번호 검증 / EN: Verify refreshed Gmail app password."""
+
+from __future__ import annotations
+
+import os
 import smtplib
-from email.mime.text import MIMEText
-from email.mime.multipart import MIMEMultipart
 from datetime import datetime
+from email.mime.multipart import MIMEMultipart
+from email.mime.text import MIMEText
 
-# Gmail 설정 - 새로운 App Password
-username = "mscho715@gmail.com"
-password = "svomdxwnvdzedfle"  # 새로운 App Password
-to_email = "mscho715@gmail.com"
-
-print("📧 Gmail 설정 테스트 (새로운 App Password)...")
-print(f"✅ Gmail 사용자명: {username}")
-print(f"✅ 수신자: {to_email}")
-print(f"✅ App Password: {password}")
-
-try:
-    # SMTP 연결 테스트
-    print("\n📡 Gmail SMTP 연결 중...")
-    server = smtplib.SMTP('smtp.gmail.com', 587)
-    server.starttls()
-    
-    print("🔐 Gmail 로그인 시도 중...")
-    server.login(username, password)
-    print("✅ Gmail SMTP 로그인 성공!")
-    
-    # 테스트 이메일 작성
-    print("📝 테스트 이메일 작성 중...")
-    msg = MIMEMultipart('alternative')
-    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 성공!"
-    msg['From'] = f"HVDC Weather Bot <{username}>"
-    msg['To'] = to_email
-    
-    # HTML 내용
-    html_content = f"""
-    <html>
-    <body style="font-family: Arial, sans-serif;">
-        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
-            <h1>🌊 HVDC Marine Weather System</h1>
-            <h2>Gmail 설정 성공!</h2>
-            
-            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
-                <h3>📊 설정 완료 정보</h3>
-                <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
-                <p><strong>Gmail 사용자명:</strong> {username}</p>
-                <p><strong>수신자:</strong> {to_email}</p>
-                <p><strong>App Password:</strong> {password[:4]}...{password[-4:]}</p>
-                <p><strong>상태:</strong> ✅ Gmail 설정 완료</p>
-            </div>
-            
-            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
-                <h3>🎉 알림 시스템 완성!</h3>
-                <p>✅ Telegram 알림: 정상 작동</p>
-                <p>✅ Gmail 알림: 정상 작동</p>
-                <p>✅ GitHub Actions: 정상 작동</p>
-                <p>✅ 해양 날씨 보고서: 매시간 자동 발송</p>
-            </div>
-            
-            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
-                <h3>📋 GitHub Secrets 설정 정보</h3>
-                <p><strong>TELEGRAM_BOT_TOKEN:</strong> 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk</p>
-                <p><strong>TELEGRAM_CHAT_ID:</strong> 470962761</p>
-                <p><strong>MAIL_USERNAME:</strong> {username}</p>
-                <p><strong>MAIL_PASSWORD:</strong> {password}</p>
-                <p><strong>MAIL_TO:</strong> {to_email}</p>
+from scripts.secret_helpers import load_secret, mask_secret
+
+
+def main() -> None:
+    """KR: 새 비밀번호로 발송 테스트 / EN: Send email with new password."""
+
+    try:
+        username = load_secret("MAIL_USERNAME")
+        password = load_secret("MAIL_PASSWORD")
+        to_email = load_secret("MAIL_TO")
+    except RuntimeError as error:
+        print(f"❌ 환경 변수 누락: {error}")
+        print("ℹ️ .env 파일 또는 GitHub Secrets에서 값을 설정하세요.")
+        return
+
+    print("📧 Gmail 설정 테스트 (새로운 App Password)...")
+    print(f"✅ Gmail 사용자명: {username}")
+    print(f"✅ 수신자: {to_email}")
+    print(f"✅ App Password: {mask_secret(password)}")
+
+    try:
+        print("\n📡 Gmail SMTP 연결 중...")
+        server = smtplib.SMTP("smtp.gmail.com", 587)
+        server.starttls()
+
+        print("🔐 Gmail 로그인 시도 중...")
+        server.login(username, password)
+        print("✅ Gmail SMTP 로그인 성공!")
+
+        print("📝 테스트 이메일 작성 중...")
+        msg = MIMEMultipart("alternative")
+        msg["Subject"] = "🔍 HVDC Marine Weather System - Gmail 설정 성공!"
+        msg["From"] = f"HVDC Weather Bot <{username}>"
+        msg["To"] = to_email
+
+        html_content = f"""
+        <html>
+        <body style="font-family: Arial, sans-serif;">
+            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
+                <h1>🌊 HVDC Marine Weather System</h1>
+                <h2>Gmail 설정 성공!</h2>
+
+                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
+                    <h3>📊 설정 완료 정보</h3>
+                    <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
+                    <p><strong>Gmail 사용자명:</strong> {username}</p>
+                    <p><strong>수신자:</strong> {to_email}</p>
+                    <p><strong>App Password:</strong> {mask_secret(password)}</p>
+                    <p><strong>상태:</strong> ✅ Gmail 설정 완료</p>
+                </div>
+
+                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
+                    <h3>🎉 알림 시스템 완성!</h3>
+                    <p>✅ Telegram 알림: 정상 작동</p>
+                    <p>✅ Gmail 알림: 정상 작동</p>
+                    <p>✅ GitHub Actions: 정상 작동</p>
+                    <p>✅ 해양 날씨 보고서: 매시간 자동 발송</p>
+                </div>
+
+                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
+                    <h3>📋 GitHub Secrets 설정 상태</h3>
+                    <p><strong>TELEGRAM_BOT_TOKEN:</strong> {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}</p>
+                    <p><strong>TELEGRAM_CHAT_ID:</strong> {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}</p>
+                    <p><strong>MAIL_USERNAME:</strong> {username}</p>
+                    <p><strong>MAIL_PASSWORD:</strong> {mask_secret(password)}</p>
+                    <p><strong>MAIL_TO:</strong> {to_email}</p>
+                </div>
+
+                <hr style="margin: 30px 0;">
+                <p style="color: #666; font-size: 12px;">
+                    HVDC Project - Samsung C&T Logistics<br>
+                    Marine Weather Notification System
+                </p>
             </div>
-            
-            <hr style="margin: 30px 0;">
-            <p style="color: #666; font-size: 12px;">
-                HVDC Project - Samsung C&T Logistics<br>
-                Marine Weather Notification System
-            </p>
-        </div>
-    </body>
-    </html>
-    """
-    
-    html_part = MIMEText(html_content, 'html', 'utf-8')
-    msg.attach(html_part)
-    
-    # 이메일 발송
-    print("📤 테스트 이메일 발송 중...")
-    server.sendmail(username, to_email, msg.as_string())
-    server.quit()
-    
-    print("✅ Gmail 테스트 이메일 발송 성공!")
-    
-    print("\n🎉 모든 알림 시스템 설정 완료!")
-    print("\n📋 GitHub Secrets 설정 정보:")
-    print("=" * 60)
-    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
-    print("TELEGRAM_CHAT_ID: 470962761")
-    print(f"MAIL_USERNAME: {username}")
-    print(f"MAIL_PASSWORD: {password}")
-    print(f"MAIL_TO: {to_email}")
-    
-    print("\n🚀 다음 단계:")
-    print("1. GitHub 리포지토리 → Settings → Secrets and variables → Actions")
-    print("2. 위의 5개 시크릿을 모두 설정")
-    print("3. GitHub Actions → 'Run workflow' 클릭")
-    print("4. Telegram과 Gmail로 해양 날씨 보고서 수신 확인!")
-    
-except smtplib.SMTPAuthenticationError as e:
-    print(f"❌ Gmail 인증 실패: {e}")
-    print("\n🔧 문제 해결:")
-    print("1. App Password가 올바른지 확인")
-    print("2. 2단계 인증이 활성화되어 있는지 확인")
-    print("3. App Password 생성 시 공백 제거 확인")
-except Exception as e:
-    print(f"❌ Gmail 연결 실패: {e}")
+        </body>
+        </html>
+        """
+
+        html_part = MIMEText(html_content, "html", "utf-8")
+        msg.attach(html_part)
+
+        print("📤 테스트 이메일 발송 중...")
+        server.sendmail(username, to_email, msg.as_string())
+        server.quit()
+
+        print("✅ Gmail 테스트 이메일 발송 성공!")
+
+        print("\n🎉 모든 알림 시스템 설정 완료!")
+        print("\n📋 GitHub Secrets 설정 상태:")
+        print("=" * 60)
+        print(f"TELEGRAM_BOT_TOKEN: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
+        print(f"TELEGRAM_CHAT_ID: {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}")
+        print(f"MAIL_USERNAME: {username}")
+        print(f"MAIL_PASSWORD: {mask_secret(password)}")
+        print(f"MAIL_TO: {to_email}")
+
+        print("\n🚀 다음 단계:")
+        print("1. GitHub 리포지토리 → Settings → Secrets and variables → Actions")
+        print("2. 위의 5개 시크릿을 모두 설정")
+        print("3. GitHub Actions → 'Run workflow' 클릭")
+        print("4. Telegram과 Gmail로 해양 날씨 보고서 수신 확인!")
+
+    except smtplib.SMTPAuthenticationError as error:
+        print(f"❌ Gmail 인증 실패: {error}")
+        print("\n🔧 문제 해결:")
+        print("1. App Password가 올바른지 확인")
+        print("2. 2단계 인증이 활성화되어 있는지 확인")
+        print("3. App Password 생성 시 공백 제거 확인")
+    except Exception as error:  # pragma: no cover - diagnostic helper
+        print(f"❌ Gmail 연결 실패: {error}")
+
+
+if __name__ == "__main__":
+    main()
diff --git a/test_gmail_quick.py b/test_gmail_quick.py
index 68dd241696d53c1523c3fa3a5dc85c0b144f90fa..bb3f9f3c5714bf67364c8d2de2941cc231849c8f 100644
--- a/test_gmail_quick.py
+++ b/test_gmail_quick.py
@@ -1,93 +1,108 @@
 #!/usr/bin/env python3
+"""KR: Gmail 알림 연동 점검 / EN: Gmail notification smoke test."""
+
+from __future__ import annotations
+
+import os
 import smtplib
-from email.mime.text import MIMEText
-from email.mime.multipart import MIMEMultipart
 from datetime import datetime
+from email.mime.multipart import MIMEMultipart
+from email.mime.text import MIMEText
 
-# Gmail 설정 (실제 값으로 교체 필요)
-username = "mscho715@gmail.com"  # Gmail 주소
-password = "svom dxwn vdze dfle"  # App Password (공백 제거)
-to_email = "mscho715@gmail.com"   # 수신자
-
-# 공백 제거
-password = password.replace(" ", "")
-
-print("📧 Gmail 설정 테스트 시작...")
-print(f"✅ Gmail 사용자명: {username}")
-print(f"✅ 수신자: {to_email}")
-print(f"✅ App Password: {password[:4]}...{password[-4:]}")
-
-try:
-    # SMTP 연결 테스트
-    print("\n📡 Gmail SMTP 연결 중...")
-    server = smtplib.SMTP('smtp.gmail.com', 587)
-    server.starttls()
-    
-    print("🔐 Gmail 로그인 시도 중...")
-    server.login(username, password)
-    print("✅ Gmail SMTP 로그인 성공!")
-    
-    # 테스트 이메일 작성
-    print("📝 테스트 이메일 작성 중...")
-    msg = MIMEMultipart('alternative')
-    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 검증 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
-    msg['From'] = f"HVDC Weather Bot <{username}>"
-    msg['To'] = to_email
-    
-    # HTML 내용
-    html_content = f"""
-    <html>
-    <body style="font-family: Arial, sans-serif;">
-        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
-            <h1>🌊 HVDC Marine Weather System</h1>
-            <h2>Gmail 설정 검증 성공</h2>
-            
-            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
-                <h3>📊 테스트 정보</h3>
-                <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
-                <p><strong>Gmail 사용자명:</strong> {username}</p>
-                <p><strong>수신자:</strong> {to_email}</p>
-                <p><strong>상태:</strong> Gmail 설정 검증 성공</p>
-            </div>
-            
-            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
-                <p>✅ 이 이메일이 수신되면 Gmail 설정이 완료되었습니다!</p>
-                <p>✅ App Password가 올바르게 작동합니다!</p>
+from scripts.secret_helpers import load_secret, mask_secret
+
+
+def main() -> None:
+    """KR: 시크릿을 노출 없이 검증 / EN: Verify secrets without leaking."""
+
+    try:
+        username = load_secret("MAIL_USERNAME")
+        password = load_secret("MAIL_PASSWORD").replace(" ", "")
+        to_email = load_secret("MAIL_TO")
+    except RuntimeError as error:
+        print(f"❌ 환경 변수 누락: {error}")
+        print("ℹ️ .env 파일 또는 GitHub Secrets에서 값을 설정하세요.")
+        return
+
+    print("📧 Gmail 설정 테스트 시작...")
+    print(f"✅ Gmail 사용자명: {username}")
+    print(f"✅ 수신자: {to_email}")
+    print(f"✅ App Password: {mask_secret(password)}")
+
+    try:
+        print("\n📡 Gmail SMTP 연결 중...")
+        server = smtplib.SMTP("smtp.gmail.com", 587)
+        server.starttls()
+
+        print("🔐 Gmail 로그인 시도 중...")
+        server.login(username, password)
+        print("✅ Gmail SMTP 로그인 성공!")
+
+        print("📝 테스트 이메일 작성 중...")
+        msg = MIMEMultipart("alternative")
+        msg["Subject"] = (
+            "🔍 HVDC Marine Weather System - Gmail 설정 검증 "
+            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
+        )
+        msg["From"] = f"HVDC Weather Bot <{username}>"
+        msg["To"] = to_email
+
+        html_content = f"""
+        <html>
+        <body style="font-family: Arial, sans-serif;">
+            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
+                <h1>🌊 HVDC Marine Weather System</h1>
+                <h2>Gmail 설정 검증 성공</h2>
+
+                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
+                    <h3>📊 테스트 정보</h3>
+                    <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
+                    <p><strong>Gmail 사용자명:</strong> {username}</p>
+                    <p><strong>수신자:</strong> {to_email}</p>
+                    <p><strong>상태:</strong> Gmail 설정 검증 성공</p>
+                </div>
+
+                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
+                    <p>✅ 이 이메일이 수신되면 Gmail 설정이 완료되었습니다!</p>
+                    <p>✅ App Password가 올바르게 작동합니다!</p>
+                </div>
+
+                <hr style="margin: 30px 0;">
+                <p style="color: #666; font-size: 12px;">
+                    HVDC Project - Samsung C&T Logistics<br>
+                    Marine Weather Notification System
+                </p>
             </div>
-            
-            <hr style="margin: 30px 0;">
-            <p style="color: #666; font-size: 12px;">
-                HVDC Project - Samsung C&T Logistics<br>
-                Marine Weather Notification System
-            </p>
-        </div>
-    </body>
-    </html>
-    """
-    
-    html_part = MIMEText(html_content, 'html', 'utf-8')
-    msg.attach(html_part)
-    
-    # 이메일 발송
-    print("📤 테스트 이메일 발송 중...")
-    server.sendmail(username, to_email, msg.as_string())
-    server.quit()
-    
-    print("✅ Gmail 테스트 이메일 발송 성공!")
-    
-    print("\n📋 GitHub Secrets 설정 정보:")
-    print("=" * 50)
-    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
-    print("TELEGRAM_CHAT_ID: 470962761")
-    print(f"MAIL_USERNAME: {username}")
-    print(f"MAIL_PASSWORD: {password}")
-    print(f"MAIL_TO: {to_email}")
-    
-except smtplib.SMTPAuthenticationError as e:
-    print(f"❌ Gmail 인증 실패: {e}")
-    print("\n🔧 해결 방법:")
-    print("1. Google 계정 → 보안 → 2단계 인증 활성화")
-    print("2. 앱 비밀번호 생성 (16자리)")
-    print("3. 일반 비밀번호가 아닌 앱 비밀번호 사용")
-except Exception as e:
-    print(f"❌ Gmail 연결 실패: {e}")
+        </body>
+        </html>
+        """
+
+        html_part = MIMEText(html_content, "html", "utf-8")
+        msg.attach(html_part)
+
+        print("📤 테스트 이메일 발송 중...")
+        server.sendmail(username, to_email, msg.as_string())
+        server.quit()
+
+        print("✅ Gmail 테스트 이메일 발송 성공!")
+
+        print("\n📋 GitHub Secrets 설정 상태:")
+        print("=" * 50)
+        print(f"TELEGRAM_BOT_TOKEN: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
+        print(f"TELEGRAM_CHAT_ID: {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}")
+        print(f"MAIL_USERNAME: {username}")
+        print(f"MAIL_PASSWORD: {mask_secret(password)}")
+        print(f"MAIL_TO: {to_email}")
+
+    except smtplib.SMTPAuthenticationError as error:
+        print(f"❌ Gmail 인증 실패: {error}")
+        print("\n🔧 해결 방법:")
+        print("1. Google 계정 → 보안 → 2단계 인증 활성화")
+        print("2. 앱 비밀번호를 새로 생성하고 16자리 값을 사용")
+        print("3. 일반 비밀번호가 아닌 앱 비밀번호를 사용")
+    except Exception as error:  # pragma: no cover - diagnostic helper
+        print(f"❌ Gmail 연결 실패: {error}")
+
+
+if __name__ == "__main__":
+    main()
