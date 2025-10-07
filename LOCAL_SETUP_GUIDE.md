# 🏠 로컬 실행 가이드 / Local Setup Guide

## 빠른 시작 / Quick Start

### 1. 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (실제 값 입력)
notepad .env
```

### 2. 전체 시스템 실행
```bash
python run_local_test.py
```

---

## 📋 상세 설정 / Detailed Setup

### Telegram 알림 설정

1. **BotFather로 봇 생성**
   - Telegram에서 [@BotFather](https://t.me/botfather) 검색
   - `/newbot` 명령어 실행
   - 봇 이름 설정
   - **Bot Token 복사** (예: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Chat ID 확인**
   - 생성한 봇에게 아무 메시지 전송
   - 브라우저에서 접속: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - `"chat":{"id":1234567890}` 부분에서 **Chat ID 복사**

3. **.env 파일에 입력**
   ```
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=1234567890
   ```

---

### Gmail 알림 설정

1. **Google 계정 2단계 인증 활성화**
   - https://myaccount.google.com/security
   - "2단계 인증" 활성화

2. **앱 비밀번호 생성**
   - https://myaccount.google.com/apppasswords
   - "메일" 선택 → "기타" 선택
   - 이름 입력 (예: "HVDC Marine")
   - **16자리 앱 비밀번호 복사** (예: `abcd efgh ijkl mnop`)

3. **.env 파일에 입력**
   ```
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=abcdefghijklmnop
   MAIL_TO=recipient@example.com
   ```

---

### API 키 설정 (선택사항)

#### Stormglass API
1. https://stormglass.io/ 회원가입
2. Dashboard → API Key 복사
3. `.env`에 추가:
   ```
   STORMGLASS_API_KEY=your_api_key_here
   ```

#### WorldTides API
1. https://www.worldtides.info/ 회원가입
2. Dashboard → API Key 복사
3. `.env`에 추가:
   ```
   WORLDTIDES_API_KEY=your_api_key_here
   ```

**참고**: API 키 없이도 오프라인 모드로 테스트 가능합니다.

---

## 🚀 실행 방법 / How to Run

### 방법 1: 전체 테스트 (권장)
```bash
python run_local_test.py
```

**결과**:
- ✅ 해양 날씨 데이터 수집
- ✅ ERI 계산
- ✅ 운항 가능성 예측
- ✅ Telegram 알림 전송
- ✅ Email 알림 전송

---

### 방법 2: 개별 실행

#### 날씨 데이터만 수집
```bash
python scripts/weather_job.py --location AGI --hours 24 --mode auto --out out
```

#### 알림만 전송
```bash
python scripts/send_notifications.py
```

---

## 📊 출력 결과 / Output

### 콘솔 출력 예시
```
======================================================================
🚀 HVDC Marine - 로컬 전체 시스템 테스트
======================================================================

🔍 환경변수 확인:
  TELEGRAM_BOT_TOKEN: ✅ 설정됨 (1234...wxyz)
  TELEGRAM_CHAT_ID: ✅ 설정됨 (1234...7890)
  MAIL_USERNAME: ✅ 설정됨 (your_email@gmail.com)
  MAIL_PASSWORD: ✅ 설정됨 (abcd...mnop)
  MAIL_TO: ✅ 설정됨 (recipient@example.com)

======================================================================
1️⃣ 해양 날씨 데이터 수집
======================================================================
🌊 AGI 해역 날씨 데이터 수집
✅ Stormglass: 48 타임스텝
✅ Open-Meteo: 25 타임스텝
✅ WorldTides: 96 타임스텝
⚠️ NCM Selenium: 폴백 데이터
📊 데이터 수집률: 75.0% (3/4 소스)

======================================================================
2️⃣ 알림 전송 테스트
======================================================================
📱 Telegram 알림 전송 중...
  ✅ Telegram 알림 전송 성공!

📧 Email 알림 전송 중...
  ✅ Email 알림 전송 성공!

======================================================================
🎉 로컬 테스트 완료
======================================================================
✅ 모든 테스트 성공!

📱 Telegram을 확인하세요
📧 Email을 확인하세요
```

### 생성 파일
```
out/
├── summary.txt                      # 텍스트 요약
├── summary_20251007_2029.json      # JSON 보고서
├── api_status_20251007_2029.csv    # API 상태
├── operability_forecasts.csv       # 운항 가능성 예측
└── eta_predictions.csv             # ETA 예측
```

---

## ❌ 문제 해결 / Troubleshooting

### 오류: "Telegram 시크릿 없음"
**원인**: `.env` 파일이 없거나 TELEGRAM_BOT_TOKEN이 비어있음

**해결**:
```bash
# .env 파일 확인
cat .env

# 값이 비어있다면 다시 설정
notepad .env
```

---

### 오류: "Email 오류: Authentication failed"
**원인**: Gmail 앱 비밀번호가 잘못되었거나 2단계 인증이 비활성화됨

**해결**:
1. https://myaccount.google.com/security 에서 2단계 인증 확인
2. https://myaccount.google.com/apppasswords 에서 새 앱 비밀번호 생성
3. `.env` 파일에 16자리 비밀번호 입력 (공백 제거)

---

### 오류: "ModuleNotFoundError: No module named 'dotenv'"
**원인**: python-dotenv 패키지가 설치되지 않음

**해결**:
```bash
pip install python-dotenv
```

---

## 🔒 보안 / Security

### ⚠️ 중요: .env 파일 관리

```bash
# .env 파일은 절대 Git에 커밋하지 마세요!
# .env file should NEVER be committed to Git!

# .gitignore에 추가되어 있는지 확인
cat .gitignore | grep .env
```

**.gitignore**에 다음이 포함되어야 합니다:
```
.env
.env.local
```

---

## 📞 지원 / Support

문제가 발생하면:
1. `python run_local_test.py` 출력 로그 확인
2. `.env` 파일 내용 재확인 (실제 값이 입력되었는지)
3. API 키 만료 여부 확인

---

**🎉 준비 완료! `python run_local_test.py`를 실행하세요!**

