# Quick Start (Windows)

## 1) Create folder & venv
```powershell
mkdir C:\hvdc\marine-ingest
cd C:\hvdc\marine-ingest
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2) Install packages
```powershell
pip install --upgrade pip
pip install pandas beautifulsoup4 lxml numpy sentence-transformers sqlite-utils
```

## 3) UTF-8 console
```powershell
chcp 65001
setx PYTHONUTF8 1
$env:PYTHONUTF8="1"
```

## 4) NCM 웹 수집 (업데이트됨!)
```powershell
# NCM Al Bahar 해양 관측 페이지에서 Selenium으로 데이터 수집
python test_ncm_selenium.py

# 업데이트된 NCM 수집기 테스트
python test_ncm_real.py

# 출력: data/ncm_selenium_*.csv, data/ncm_real_*.csv
# 벡터 DB: marine_vec.db에 실시간 저장
```

## 5) First run
```powershell
# If you have an HTML snapshot (e.g., NCM page) saved as snapshot.html
python ingest_standalone.py
python embed_index.py
python query_knn.py
```

## 6) Scheduled embeddings (every 3h)
```powershell
powershell -ExecutionPolicy Bypass -File .\schedule_embed.ps1
```

## 7) 통합 해양 날씨 파이프라인 (NEW!)
```powershell
# 데모 모드 (API 키 없이 실행 가능)
python .\scripts\demo_integrated.py

# 전체 파이프라인 실행
python .\run_once.ps1
```

## 8) 실제 API 연동 (옵션)
```powershell
# 환경 변수 설정
copy config\env_template config\.env
# .env 파일에서 API 키 설정 후:
python .\scripts\generate_weather_report.py --locations AGI,DAS
```

## 9) 벡터 검색 및 질의
```powershell
# 자연어 질의
python query_vec.py --query "AGI high tide RORO window"

# 운항 윈도우 분석
python query_vec.py --operational --location AGI

# 벡터 파이프라인 테스트
python scripts\test_vector_pipeline.py
```

## 10) 자동화 스케줄러
```powershell
# 한 번 실행 (테스트)
python scripts\cron_automation.py --once

# 스케줄러 시작 (3시간마다 수집, 06:00/18:00 보고서)
python scripts\cron_automation.py
```

## Notes
- For dynamic pages, prefer `agent_hooks.py` with Cursor 1.7 Browser Controls.
- Model: `all-MiniLM-L6-v2` (CPU OK).
- **NEW**: 통합 해양 날씨 파이프라인 (Stormglass/Open-Meteo/WorldTides/NCM → ERI → 융합판정 → 보고서)
- **NEW**: SQLite 벡터 DB + 자연어 질의 시스템
- **NEW**: 자동화 스케줄러 + 알림 시스템 (Telegram/Email)
- **NEW**: NCM Al Bahar 페이지 Selenium 자동 수집 (https://albahar.ncm.gov.ae/marine-observations?lang=en)
- 보고서 출력: `reports/DEMO_YYYYMMDD_HHMM.json/csv`
- 벡터 DB: `marine_vec.db` (SQLite + sentence-transformers)

## 🎯 완성된 기능들
✅ **다중 소스 수집**: Stormglass/Open-Meteo/WorldTides/NCM 웹  
✅ **벡터 DB 저장**: SQLite + 임베딩 검색  
✅ **자연어 질의**: "AGI high tide RORO window" 검색  
✅ **운항 판정**: GO/CONDITIONAL/NO-GO 자동 분류  
✅ **자동화**: 3시간마다 수집 + 알림  
✅ **Cursor 연동**: Browser Controls 훅으로 실시간 수집
✅ **NCM Selenium**: Al Bahar 해양 관측 페이지 자동 수집
✅ **WorldTides**: 조석 높이 데이터 통합 (30분 해상도)
✅ **확장된 해양 변수**: 스웰/바람파/해류/SST/해수면 높이
✅ **향상된 ERI**: 10개 해양 변수 기반 환경 위험 지수
✅ **HTTP 안정화**: 429/503 자동 재시도 + robots.txt 준수
✅ **실제 데이터 검증**: 83.3% 성공률 달성 (NCM + Open-Meteo 연동)
✅ **API 키 통합**: Stormglass ✅ + WorldTides ⚠️ (75% 실제 데이터 수집률)  

자세한 내용은 `INTEGRATION_GUIDE.md` 참조

## 📊 시스템 아키텍처 문서

- **전체 아키텍처**: `SYSTEM_ARCHITECTURE.md` - 시스템 전체 구조 및 데이터 플로우
- **시각화 다이어그램**: `system_architecture_diagram.html` - 인터랙티브 아키텍처 다이어그램
- **컴포넌트 구조**: `component_architecture.html` - 모듈별 상세 구조 및 관계도
- **NCM 업데이트**: `NCM_UPDATE_GUIDE.md` - NCM Al Bahar 페이지 자동 수집 업데이트
- **PR 적용 결과**: `PR_APPLICATION_RESULTS.md` - 스크래핑 안정화 + 해양 확장 적용 결과
- **데이터 검증 보고서**: `DATA_VALIDATION_REPORT.md` - 실제 데이터 수집 및 처리 검증 결과
- **API 키 통합 보고서**: `API_KEYS_INTEGRATION_REPORT.md` - Stormglass + WorldTides API 키 통합 결과
