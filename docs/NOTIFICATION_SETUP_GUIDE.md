# GitHub Secrets 설정 가이드

## 1. Telegram Bot 설정

### 1.1 Bot 생성
1. Telegram에서 @BotFather와 대화 시작
2. `/newbot` 명령어 입력
3. 봇 이름과 사용자명 설정
4. Bot Token 복사

### 1.2 Chat ID 확인
1. 봇과 대화 시작
2. 브라우저에서 `https://api.telegram.org/bot[BOT_TOKEN]/getUpdates` 접속
3. `chat.id` 값 복사

### 1.3 GitHub Secrets 설정
- `TELEGRAM_BOT_TOKEN`: Bot Token
- `TELEGRAM_CHAT_ID`: Chat ID (숫자)

## 2. Gmail 설정

### 2.1 앱 비밀번호 생성
1. Google 계정 → 보안 → 2단계 인증 활성화
2. 앱 비밀번호 생성 (16자리)
3. Gmail 사용자명과 앱 비밀번호 기록

### 2.2 GitHub Secrets 설정
- `MAIL_USERNAME`: Gmail 주소 (예: user@gmail.com)
- `MAIL_PASSWORD`: 앱 비밀번호 (16자리)
- `MAIL_TO`: 수신자 이메일 주소

## 3. API 키 설정
- `STORMGLASS_API_KEY`: Stormglass API 키
- `WORLDTIDES_API_KEY`: WorldTides API 키

## 4. 설정 확인
1. GitHub Actions 탭에서 워크플로우 실행
2. 로그에서 알림 상태 확인
3. Telegram과 Email 수신 확인
