# 🌊 HVDC Marine Weather Ingestion System

[![Test](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/test.yml/badge.svg)](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/test.yml)
[![Marine Hourly](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/marine-hourly.yml/badge.svg)](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/marine-hourly.yml)

## Overview

통합 해양 날씨 데이터 수집 및 분석 시스템으로, 다중 소스에서 해양 기상 데이터를 수집하여 ERI(Environmental Risk Index)를 계산하고 3일치 운항 판정을 제공합니다.

### 주요 기능 (v2.6 Production Ready)

#### 🆕 v2.6 신규 기능
- 🌊 **3-Day GO/NO-GO Format**: Impact-Based Forecast (IBFWS) 원칙 적용 ⭐
- 📅 **일별 운항 윈도우**: D0/D+1/D+2 연속 윈도우 자동 탐지 ⭐
- 📊 **WMO/NOAA 표준**: Sea State Code 3700 + Small Craft Advisory ⭐
- 📱 **Telegram 최적화**: 한눈에 보는 3일 운항 가능성 ⭐
- 📧 **Email HTML**: 깔끔한 포맷 + 참조 문헌 ⭐
- 🤖 **ML 장기 예측**: RandomForest 기반 7일 ERI 추정 + 이상 탐지 ⭐

#### v2.5 기능
- 🌊 **72시간 예보 파이프라인**: 3일치 해양 예보 자동 생성
- 🚢 **운영 영향 모델링**: ETA/ETD 지연 정량 계산 (95% 정확도)
- 📊 **Daypart 분석**: dawn/morning/afternoon/evening 4구간 요약
- 🌊 **WMO Sea State**: 국제 표준 해상 상태 분류
- 🗺️ **Route Window**: AGI↔DAS 운용 윈도우 교집합 분석
- 🎭 **Playwright 통합**: NCM AlBahar 고성능 스크래핑
- 🔒 **보안 강화**: 시크릿 마스킹 및 환경변수 관리

#### 핵심 기능
- 🌐 **다중 소스 수집**: Stormglass, Open-Meteo, WorldTides, NCM AlBahar
- 🔄 **CI 환경 온라인 모드**: GitHub Actions에서도 API 키 있으면 실제 데이터
- 📄 **다중 형식 보고서**: HTML/TXT/JSON/CSV 자동 생성
- 🛡️ **오프라인 모드**: API 키 누락 시 자동 합성 데이터 생성
- 🔄 **Resilience**: 각 데이터 소스별 독립적 fallback 처리
- 🔍 **벡터 검색**: SQLite + 임베딩 기반 자연어 질의
- ⚠️ **ERI 계산**: 10개 해양 변수 기반 환경 위험 지수
- 🚢 **운항 판정**: GO/CONDITIONAL/NO-GO 자동 분류

## Quick Start

### Prerequisites
- Python 3.8+
- Git

### Installation

```bash
git clone https://github.com/macho715/hvdc_marine_ingest.git
cd hvdc_marine_ingest

python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 로컬 실행

```bash
# 오프라인 모드 (API 키 불필요)
python scripts/weather_job.py --location AGI --hours 24 --mode offline --out out

# 온라인 모드 (API 키 필요)
python scripts/weather_job.py --location AGI --hours 24 --mode online --out out

# 72시간 예보
python scripts/weather_job_3d.py --mode offline --out out
```

### 출력 예시 (v2.6 3-Day Format)

```
🌊 AGI Marine Ops — 3-Day GO/NO-GO

🗓 Build: 2025-10-07 19:49 UTC  |  2025-10-07 23:49 (UTC+4)
📍 Spot: AGI (Al Ghallan Island)

🔎 3-Day Overview (UTC+4)
D0 오늘:     🔴  창 없음 (대체 일정 탐색)
D+1 내일:    🟢  운항 권장, 06:00–18:00
D+2 모레:    🟢  운항 권장, 04:00–20:00 ← Best Window

🪟 Windows (UTC+4)
• D0: —
• D+1: 🟢 06:00–18:00
• D+2: 🟢 04:00–20:00 | 🟡 21:00–23:00

Why (요약)
• Hs/Wind (avg): 0.67 m / 18 kt
• ERI(mean): 0.17  | Bias: GO>NO-GO (66/47)
• Notes: 정상

Confidence: MED (0.73)
Data: OPEN-METEO ✅  NCM ✅  STORMGLASS ✅  TIDES ⚠️

/actions  ➜  /plan D+2 04:00-20:00   /brief crew   /share mws
```

## GitHub Actions 자동화

### 매시간 자동 실행
- **스케줄**: 매시간 07분(UTC) 실행
- **트리거**: push (main), 수동 실행, 스케줄
- **알림**: Telegram + Email (3-Day GO/NO-GO 포맷)

### 주간 ML 재학습
- **스케줄**: 매주 일요일 03:00 UTC (`ml-retrain.yml`)
- **내용**: `scripts/train_ml_model.py` 실행 → RandomForest 모델 학습 및 아티팩트 업로드
- **산출물**: `cache/ml_forecast/` 폴더의 모델과 `metadata.json`

### GitHub Secrets 설정

**필수 (알림용)**:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_TO=recipient@example.com
```

**선택사항 (실제 데이터용)**:
```bash
STORMGLASS_API_KEY=your_key  # 선택
WORLDTIDES_API_KEY=your_key  # 선택
```

## Performance

### v2.6 실측 성능
- **데이터 포인트**: 121개(24h) + 228개(72h)
- **응답 시간**: <3초(오프라인), <30초(온라인)
- **ETA 계산 정확도**: 95%
- **윈도우 탐지**: 최소 2시간 연속
- **시스템 가용성**: 100%

## Documentation

### 📚 전체 문서 (docs/ 폴더)

#### 시작 가이드
- [상세 README](docs/README.md) - 전체 기능 설명
- [빠른 시작](docs/README_quickstart.md) - 5분 설정
- [로컬 실행 가이드](docs/LOCAL_SETUP_GUIDE.md)
- [ML 장기 예측 가이드 (EN)](docs/en/ml_forecast.md)
- [ML 장기 예측 가이드 (KR)](docs/kr/ml_forecast.md)

#### 시스템 아키텍처
- [시스템 아키텍처](docs/SYSTEM_ARCHITECTURE.md)
- [날씨 판정 로직](docs/WEATHER_DECISION_LOGIC_REPORT.md)
- [통합 가이드](docs/INTEGRATION_GUIDE.md)

#### 패치 및 검증
- [3-Day 포맷 통합](docs/PATCH_MESSAGE_INTEGRATION.md) ⭐ v2.6
- [72시간 파이프라인](docs/PATCH_v4_VERIFICATION.md)
- [운영 영향 모델링](docs/PATCH5_VERIFICATION_REPORT.md)
- [보안 강화](docs/PATCH_v3_VERIFICATION_REPORT.md)

#### 시각화
- [날씨 판정 플로우](docs/weather_decision_flow_diagram.html)
- [시스템 아키텍처](docs/system_architecture_diagram.html)
- [ERI 계산](docs/eri_calculation_diagram.html)

#### 문제 해결
- [GitHub Actions 문제 해결](docs/GITHUB_ACTIONS_FIX.md)
- [시크릿 관리](docs/SECRETS_TROUBLESHOOTING_GUIDE.md)
- [알림 설정](docs/NOTIFICATION_SETUP_GUIDE.md)

## License

MIT License

---

**시스템 버전**: v2.6 Production Ready ⭐  
**최신 업데이트**: 2025-10-07  
**상태**: 🟢 All Systems Operational  
**GitHub Actions**: ✅ 자동 실행 중

*3-Day GO/NO-GO 포맷으로 매시간 해양 운항 조건을 자동으로 분석하여 Telegram 및 Email로 전송합니다.*

