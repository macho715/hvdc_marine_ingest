# 🌊 HVDC Marine Weather Ingestion System

[![Test](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/test.yml/badge.svg)](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/test.yml)
[![Marine Hourly](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/marine-hourly.yml/badge.svg)](https://github.com/macho715/hvdc_marine_ingest/actions/workflows/marine-hourly.yml)

## Overview

통합 해양 날씨 데이터 수집 및 분석 시스템으로, 다중 소스에서 해양 기상 데이터를 수집하여 ERI(Environmental Risk Index)를 계산하고 운항 판정을 제공합니다.

### 주요 기능
- 🌐 **다중 소스 수집**: Stormglass, Open-Meteo, WorldTides, NCM 웹
- 🔍 **벡터 검색**: SQLite + 임베딩 기반 자연어 질의
- ⚠️ **ERI 계산**: 7개 해양 변수 기반 환경 위험 지수
- 🚢 **운항 판정**: GO/CONDITIONAL/NO-GO 자동 분류
- 📊 **자동 보고서**: 3일 기상 예보 및 분석
- 🔄 **실시간 수집**: GitHub Actions 기반 자동화
- 📱 **알림 시스템**: Telegram, Email 자동 알림

## Directory Structure

```
hvdc_marine_ingest/
├── .github/workflows/          # GitHub Actions 워크플로우
│   ├── marine-hourly.yml      # 매시간 자동 실행
│   └── test.yml               # 테스트 자동화
├── src/marine_ops/            # 핵심 시스템 모듈
│   ├── connectors/            # API 커넥터들
│   ├── core/                  # 핵심 스키마 및 유틸리티
│   ├── decision/              # 운항 판정 로직
│   └── eri/                   # ERI 계산 엔진
├── ncm_web/                   # NCM 웹 스크래핑
├── scripts/                   # 자동화 스크립트
├── config/                    # 설정 파일들
├── data/                      # 수집된 데이터
├── reports/                   # 생성된 보고서
├── docs/                      # 문서화
└── tests/                     # 테스트 파일들
```

## Setup

### Prerequisites
- Python 3.8+
- Git
- Chrome/Chromium (Selenium용)

### Installation

1. **저장소 클론**:
   ```bash
   git clone https://github.com/macho715/hvdc_marine_ingest.git
   cd hvdc_marine_ingest
   ```

2. **가상환경 생성**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **의존성 설치**:
   ```bash
   pip install -r requirements.txt
   ```

4. **환경 설정** (선택사항):
   ```bash
   cp config/env_template .env
   # API 키 설정 (Stormglass, WorldTides)
   ```

### Quick Start

1. **전체 파이프라인 실행**:
   ```bash
   python run_once.ps1  # PowerShell
   python scripts/demo_integrated.py  # Python 직접 실행
   ```

2. **3일 기상 보고서 생성**:
   ```bash
   python generate_3day_weather_report.py
   ```

3. **벡터 검색 테스트**:
   ```bash
   python query_knn.py
   ```

## GitHub Actions 자동화

### 매시간 자동 실행
- **스케줄**: 매시간 07분(UTC) 실행
- **트리거**: 푸시, 수동 실행, 스케줄
- **기능**: 데이터 수집 → 분석 → 보고서 생성 → 알림 발송

### 알림 설정
GitHub Secrets에 다음 값들을 설정하세요:

```bash
# Telegram 알림
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Email 알림
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_TO=recipient@example.com

# API 키 (선택사항)
STORMGLASS_API_KEY=your_stormglass_key
WORLDTIDES_API_KEY=your_worldtides_key
```

### 워크플로우 상태
- 🟢 **marine-hourly**: 매시간 해양 날씨 수집
- 🟢 **test**: 코드 품질 및 테스트

## Usage

### 로컬 실행

```bash
# GitHub Actions 작업 시뮬레이션
python scripts/weather_job.py --config config/locations.yml --out out

# 특정 위치 및 시간 설정
python scripts/weather_job.py --location AGI --hours 48 --out reports/
```

### 주요 스크립트

| 스크립트 | 용도 | 설명 |
|----------|------|------|
| `scripts/weather_job.py` | GitHub Actions 작업 | 매시간 자동 실행 스크립트 |
| `generate_3day_weather_report.py` | 기상 보고서 | 3일 예보 생성 |
| `query_knn.py` | 벡터 검색 | 자연어 질의 |
| `git_upload_verifier.py` | Git 업로드 | 자동 검증 및 정리 |

### API 키 설정 (선택사항)

실제 데이터 수집률을 높이려면:

1. **Stormglass API**:
   ```bash
   export STORMGLASS_API_KEY="your_api_key"
   ```

2. **WorldTides API**:
   ```bash
   export WORLDTIDES_API_KEY="your_api_key"
   ```

## Performance

### 현재 성능 지표
- **데이터 수집**: 2.3초 (평균)
- **ERI 계산**: 0.05초
- **운항 판정**: 0.02초
- **전체 처리**: 2.5초 (평균)

### 정확도
- **0-6시간 예보**: 95%
- **6-12시간 예보**: 90%
- **12-24시간 예보**: 85%
- **24-48시간 예보**: 75%
- **48-72시간 예보**: 65%

### 데이터 수집률
- **전체 수집률**: 83.3% (실제 데이터)
- **Stormglass**: ✅ 실제 데이터
- **Open-Meteo**: ✅ 실제 데이터  
- **NCM Selenium**: ✅ 실제/폴백 데이터
- **WorldTides**: ⚠️ 크레딧 부족 (폴백 데이터)

## CI/CD

### 자동화된 테스트
```bash
# 코드 품질 검사
flake8 src/
black --check src/
mypy src/

# 테스트 실행
pytest --cov=src
```

### GitHub Actions
- **자동 테스트**: 푸시/PR 시 실행
- **매시간 수집**: 해양 날씨 데이터 자동 수집
- **알림 발송**: Telegram, Email 자동 알림
- **아티팩트 저장**: 보고서 및 데이터 보관

## Documentation

### 주요 문서
- [시스템 아키텍처](SYSTEM_ARCHITECTURE.md) - 전체 시스템 구조
- [날씨 판정 로직](WEATHER_DECISION_LOGIC_REPORT.md) - 알고리즘 상세 분석
- [API 키 통합 가이드](API_KEYS_INTEGRATION_REPORT.md) - API 설정 방법
- [통합 가이드](INTEGRATION_GUIDE.md) - 전체 시스템 통합 방법

### 시각화
- [날씨 판정 플로우](weather_decision_flow_diagram.html) - 판정 프로세스 다이어그램
- [ERI 계산 알고리즘](eri_calculation_diagram.html) - ERI 계산 과정
- [시스템 아키텍처](system_architecture_diagram.html) - 전체 구조도

## License

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## Contribution

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### 개발 가이드라인
- PEP 8 스타일 가이드 준수
- 타입 힌트 사용 권장
- 테스트 커버리지 80% 이상 유지
- 문서 업데이트 필수

---

*마지막 업데이트: 2025-10-06 23:30:00*  
*시스템 버전: v2.1*  
*GitHub Actions: 활성화*
