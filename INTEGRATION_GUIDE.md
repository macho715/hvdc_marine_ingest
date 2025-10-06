# 🚢 해양 날씨 통합 파이프라인 완성 가이드

## 🎯 완성된 기능들

### ✅ 1. 핵심 아키텍처
- **다중 소스 수집**: Stormglass, Open-Meteo, WorldTides, NCM 웹
- **벡터 DB 저장**: SQLite + sentence-transformers 임베딩
- **ERI 계산**: 환경 위험 지수 (0-100)
- **융합 판정**: GO/CONDITIONAL/NO-GO 운항 결정
- **자동화**: 크론 스케줄링 + 알림 시스템

### ✅ 2. Cursor 1.7 Browser Controls 연동
- **`agent_hooks.py`**: NCM 웹 페이지 자동 수집
- **HTML 파싱**: BeautifulSoup으로 테이블 데이터 추출
- **실시간 저장**: CSV + 벡터 DB 자동 저장

### ✅ 3. 벡터 검색 시스템
- **의미 검색**: "AGI high tide RORO window" 같은 자연어 질의
- **운항 윈도우 분석**: 시간대별 운항 가능성 평가
- **조건별 분류**: GO/CONDITIONAL/NO-GO 자동 분류

## 🚀 즉시 실행 가능한 명령어들

### 기본 테스트
```bash
# 1. 벡터 파이프라인 테스트
python scripts/test_vector_pipeline.py --vector-only

# 2. Cursor 훅 테스트
python scripts/test_vector_pipeline.py --hook-only

# 3. 벡터 검색 테스트
python query_vec.py --query "AGI high tide RORO window" --top-k 5
```

### 데모 모드 (API 키 없이)
```bash
# 통합 해양 날씨 보고서 생성
python scripts/demo_integrated.py

# 전체 파이프라인 실행
python run_once.ps1
```

### 실제 운영 (API 키 설정 후)
```bash
# 1. 환경 변수 설정
copy config\env_template config\.env
# .env 파일에서 API 키 설정

# 2. 실제 API 연동
python scripts/generate_weather_report.py --locations AGI,DAS

# 3. 자동화 실행
python scripts/cron_automation.py --once  # 한 번만
python scripts/cron_automation.py        # 스케줄러 시작
```

## 📊 출력 결과 예시

### 검색 결과
```json
{
  "status": "success",
  "query": "AGI high tide RORO window",
  "total_results": 3,
  "analysis": {
    "wind_summary": {
      "min": 12.0, "max": 18.0, "avg": 15.0
    },
    "wave_summary": {
      "min": 1.0, "max": 1.5, "avg": 1.23
    },
    "conditions": {
      "good_count": 2,
      "moderate_count": 1,
      "poor_count": 0
    }
  }
}
```

### 운항 판정
```
AGI 운항 윈도우:
- GO: 1개
- CONDITIONAL: 0개  
- NO-GO: 0개
- 운항 가능률: 100.0%
- 권고사항: 운항 조건 양호 - 정상 운영 가능
```

## 🔧 Cursor 1.7 Browser Controls 설정

### 1. 훅 등록
```javascript
// Cursor 프로젝트의 .cursor/hooks.js
module.exports = {
  onPageLoaded: async (url, content) => {
    const { execSync } = require('child_process');
    const result = execSync(`python agent_hooks.py "${url}"`, { 
      encoding: 'utf-8',
      cwd: 'C:/Users/jichu/Downloads/hvdc_marine_ingest'
    });
    return JSON.parse(result);
  }
};
```

### 2. 브라우저 컨트롤 활성화
- Cursor 1.7에서 Browser Controls ON
- `https://www.ncm.ae/marine-forecast` 접속
- 자동으로 데이터 수집 및 벡터 DB 저장

## 📁 생성된 파일 구조

```
C:\Users\jichu\Downloads\hvdc_marine_ingest\
├── marine_vec.db                    # 벡터 데이터베이스
├── data/marine_ncm_*.csv           # 수집된 CSV 데이터
├── reports/DEMO_*.json             # 생성된 보고서
├── config/
│   ├── env_template               # 환경 변수 템플릿
│   ├── settings.yaml              # 시스템 설정
│   └── eri_rules.yaml             # ERI 계산 규칙
├── src/marine_ops/
│   ├── core/                      # 핵심 모듈
│   ├── connectors/                # API 커넥터
│   ├── eri/                       # ERI 계산
│   └── decision/                  # 융합 및 판정
├── scripts/
│   ├── demo_integrated.py         # 데모 통합 파이프라인
│   ├── generate_weather_report.py # 실제 API 연동
│   ├── cron_automation.py         # 자동화 스케줄러
│   └── test_vector_pipeline.py    # 테스트 스크립트
└── agent_hooks.py                 # Cursor 브라우저 훅
```

## 🎯 다음 단계 (실운영)

### 1. API 키 설정
```bash
# config/.env 파일 수정
STORMGLASS_API_KEY=your_actual_key
WORLDTIDES_API_KEY=your_actual_key
```

### 2. Task Scheduler 설정 (Windows)
```powershell
# AM 06:00, PM 18:00 자동 실행
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\path\to\scripts\cron_automation.py"
$trigger = New-ScheduledTaskTrigger -Daily -At 06:00AM
Register-ScheduledTask -TaskName "MarineWeather" -Action $action -Trigger $trigger
```

### 3. 알림 설정
```bash
# Telegram 봇 설정
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 이메일 설정
SMTP_SERVER=smtp.gmail.com
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

## 🔍 질의 예시

### 자연어 질의
```bash
python query_vec.py --query "AGI 22:00 ~ 02:00 파고 ≥ 1.5 m"
python query_vec.py --query "high wind speed rough seas"
python query_vec.py --query "RORO operations pilotage window"
```

### 운항 윈도우 분석
```bash
python query_vec.py --operational --location AGI
python query_vec.py --recent 24 --location DAS
```

### 지역별 검색
```bash
python query_vec.py --query "marine conditions" --location AGI --top-k 10
python query_vec.py --query "weather forecast" --location DAS --top-k 5
```

## 🎉 성과 요약

✅ **완전 자동화**: 웹 수집 → 벡터 저장 → LLM 질의 → 운항 판정  
✅ **실시간 검색**: "AGI high tide RORO window" 자연어 질의 지원  
✅ **다중 소스**: Stormglass + Open-Meteo + WorldTides + NCM 통합  
✅ **운영 판정**: GO/CONDITIONAL/NO-GO 자동 분류  
✅ **자동화**: 3시간마다 수집 + 알림 시스템  
✅ **확장성**: 새로운 데이터 소스 쉽게 추가 가능  

이제 **`python scripts/demo_integrated.py`** 하나의 명령어로 완전한 해양 날씨 파이프라인을 실행할 수 있습니다! 🚢⚓
