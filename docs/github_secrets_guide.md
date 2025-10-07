# GitHub Secrets 설정 가이드

## 🎯 현재 완료된 설정

### ✅ Telegram 설정 (완료)
- **Bot Token**: `<YOUR_TELEGRAM_BOT_TOKEN>`
- **Chat ID**: `<YOUR_TELEGRAM_CHAT_ID>`
- **테스트 메시지**: 성공적으로 발송됨 (실제 값은 GitHub Secrets에만 저장)

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
Value: <YOUR_TELEGRAM_BOT_TOKEN>

Name: TELEGRAM_CHAT_ID
Value: <YOUR_TELEGRAM_CHAT_ID>
```

#### B) Gmail Secrets (App Password 재생성 후)
```
Name: MAIL_USERNAME
Value: <YOUR_GMAIL_ADDRESS>

Name: MAIL_PASSWORD
Value: <YOUR_16_CHAR_APP_PASSWORD>

Name: MAIL_TO
Value: <RECIPIENT_EMAIL>
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

2. **새로운 App Password 생성**
   - 앱 비밀번호 → 새 앱 비밀번호 생성
   - 이름: "hvdc_marine_ingest"
   - 16자리 비밀번호 복사

3. **공백 제거 확인**
   - App Password에서 공백 제거
   - 예: "svom dxwn vdze dfle" → "svomdxwnvdzep"

## 📊 예상 결과

### Telegram 설정 후:
- ✅ GitHub Actions 실행 성공
- ✅ Telegram에 해양 날씨 보고서 수신
- ✅ 시크릿 진단 로그에서 "설정됨" 표시

### Gmail 설정 후:
- ✅ Email에 HTML 보고서 수신
- ✅ 완전한 알림 시스템 작동

## 🎯 우선순위

1. **즉시**: Telegram Secrets 설정 → GitHub Actions 테스트
2. **다음**: Gmail App Password 재생성 → Email 알림 완성
