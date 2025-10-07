# 🔍 GitHub Secrets "사라짐" 문제 완전 해결 가이드

## 🚨 **핵심 원인 4가지**

### **1. 포크·외부 트리거 (Fork/External Trigger)**
- **증상**: 포크에서 올라온 PR, Dependabot에서 시크릿 접근 불가
- **원인**: 공개 레포는 보안상 외부 이벤트에 시크릿 전달 안 함
- **해결**: 
  - `pull_request_target` 사용 (보안 주의)
  - Maintainer가 수동 승인
  - 또는 포크 금지 정책
- **참조**: [GitHub Docs - Using secrets in GitHub Actions](https://docs.github.com/actions/security-guides/using-secrets-in-github-actions)

### **2. 스케줄 60일 규칙 / 포크 기본 비활성**
- **증상**: `schedule` 트리거가 작동하지 않음
- **원인**: 
  - 공개 레포는 60일 활동 없으면 스케줄 자동 비활성
  - 포크의 스케줄은 기본적으로 비활성화
- **해결**:
  - Actions → Workflows → "Enable" 클릭
  - 주기적 활동으로 keep-alive (예: 배지 갱신)
- **참조**: [GitHub Docs - Disabling and enabling a workflow](https://docs.github.com/actions/using-workflows/disabling-and-enabling-a-workflow)

### **3. Environment 시크릿 스코프**
- **증상**: 시크릿이 설정되어 있는데도 접근 불가
- **원인**: Environment 시크릿은 해당 environment를 명시해야만 접근 가능
- **해결**:
  ```yaml
  jobs:
    marine-weather:
      runs-on: ubuntu-latest
      environment: production  # ✅ 명시 필요
  ```
- **참조**: [GitHub Docs - Managing environments for deployment](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)

### **4. 조건식/길이 제한 이슈**
- **증상**: 조건문에서 시크릿 비교 시 예상대로 작동하지 않음
- **원인**:
  - `if:`에서 시크릿 직접 비교 시 표현식 평가 오류
  - Telegram 4096자 제한 초과 시 조용히 실패
- **해결**:
  - **게이트 스텝** 사용 (outputs로 불린 값 전달)
  - 텔레그램 메시지 길이 체크 + `sendDocument` 폴백
- **참조**: [GitHub Docs - Evaluate expressions in workflows and actions](https://docs.github.com/actions/reference/evaluate-expressions-in-workflows-and-actions)

## ✅ **적용된 패치 (3가지 핵심 개선)**

### **1. 게이트 스텝으로 시크릿 존재 검증**
```yaml
- name: Compute gates
  id: gates
  run: |
    echo "has_tg=${{ secrets.TELEGRAM_BOT_TOKEN != '' && secrets.TELEGRAM_CHAT_ID != '' }}" >> "$GITHUB_OUTPUT"
    echo "has_mail=${{ secrets.MAIL_USERNAME != '' && secrets.MAIL_PASSWORD != '' && secrets.MAIL_TO != '' }}" >> "$GITHUB_OUTPUT"
    
    # 진단 출력
    echo "🔍 시크릿 상태 진단:"
    echo "  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN != '' && '설정됨' || '없음' }}"
    echo "  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID != '' && '설정됨' || '없음' }}"
```

**핵심**: 이후 스텝에서 `if: ${{ steps.gates.outputs.has_tg == 'true' }}`로 판단 (시크릿 직접 비교 안 함)

### **2. Telegram 4096자 제한 대응**
```yaml
- name: Telegram notify (text or document)
  if: ${{ steps.gates.outputs.has_tg == 'true' }}
  env:
    TG_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TG_CHAT:  ${{ secrets.TELEGRAM_CHAT_ID }}
  run: |
    set -eo pipefail
    BYTES=$(wc -c < out/summary.txt)
    
    if [ "$BYTES" -gt 4000 ] && [ -f out/summary.html ]; then
      # 길이 초과 → sendDocument
      curl -fsS -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendDocument" \
        -F chat_id="${TG_CHAT}" \
        -F caption="Marine Weather (HTML attached)" \
        -F document=@out/summary.html
    else
      # 일반 메시지
      curl -fsS -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        --data-urlencode "chat_id=${TG_CHAT}" \
        --data-urlencode "text@out/summary.txt"
    fi
```

**핵심**: 
- `-f` 플래그로 HTTP 오류 시 즉시 실패
- 4000바이트 기준으로 자동 폴백

### **3. Gmail App Password 명시 + 환경 변수 전달**
```yaml
- name: Email notify (Gmail SMTP via action)
  if: ${{ steps.gates.outputs.has_mail == 'true' }}
  uses: dawidd6/action-send-mail@v6
  with:
    server_address: smtp.gmail.com
    server_port: 587
    username: ${{ secrets.MAIL_USERNAME }}     # Gmail 주소
    password: ${{ secrets.MAIL_PASSWORD }}     # ✅ Google App Password 필요
    subject: "🌊 Marine Weather Report - AGI"
    to: ${{ secrets.MAIL_TO }}
    from: "HVDC Weather Bot <${{ secrets.MAIL_USERNAME }}>"
    html_body: file://out/summary.html
```

**핵심**: Gmail은 2단계 인증 + App Password(16자리) 필수

## 🔍 **진단 체크리스트**

### **스케줄 활성화 확인**
1. GitHub 리포지토리 → **Actions** 탭
2. 왼쪽 사이드바 → **"Marine Weather Hourly Collection"**
3. **"..."** 메뉴 → **"Enable workflow"** (비활성화 상태인 경우)

### **시크릿 설정 확인**
1. GitHub 리포지토리 → **Settings** → **Secrets and variables** → **Actions**
2. 필수 시크릿 7개 확인:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `MAIL_USERNAME`
   - `MAIL_PASSWORD`
   - `MAIL_TO`
   - `STORMGLASS_API_KEY`
   - `WORLDTIDES_API_KEY`

### **포크 여부 확인**
- 포크인 경우: 원본 레포에서 워크플로우 실행
- 포크에서 실행 필요 시: Settings → Actions → "Allow all actions and reusable workflows"

### **Environment 시크릿 사용 시**
```yaml
jobs:
  marine-weather:
    runs-on: ubuntu-latest
    environment: production  # ✅ Environment 명시
```

## 📊 **로그 확인 포인트**

### **1. Compute gates 단계**
```
🔍 시크릿 상태 진단:
  TELEGRAM_BOT_TOKEN: 설정됨
  TELEGRAM_CHAT_ID: 설정됨
  MAIL_USERNAME: 설정됨
  MAIL_PASSWORD: 설정됨

📊 게이트 출력값:
  has_tg: true
  has_mail: true
```

### **2. Telegram ping 단계**
```
✅ Bot Token 유효
✅ Telegram 시크릿 검증 완료
Response: {"ok":true,"result":{"message_id":123}}
```

### **3. Telegram notify 단계**
```
Telegram response: 
{"ok":true,"result":{"message_id":124,"chat":{"id":470962761}}}
```

## ⚠️ **자주 발생하는 오류**

### **오류 1: `has_tg=false` (시크릿 없음)**
```
📊 게이트 출력값:
  has_tg: false
```
**해결**: GitHub Secrets 설정 확인

### **오류 2: `{"ok":false,"error_code":401}` (토큰 무효)**
```
❌ Bot Token 무효 - 새로운 토큰 필요
```
**해결**: @BotFather에서 새 Bot Token 생성

### **오류 3: `{"ok":false,"error_code":400}` (메시지 너무 김)**
```
Telegram API 오류: 400
```
**해결**: 이미 패치됨 (자동 `sendDocument` 폴백)

### **오류 4: Gmail `535 Authentication failed`**
```
❌ Email notify 실패
```
**해결**: 
- 2단계 인증 활성화
- App Password(16자리) 생성
- `MAIL_PASSWORD`에 App Password 설정

## 🚀 **수동 테스트 방법**

### **워크플로우 수동 실행**
1. Actions → "Marine Weather Hourly Collection"
2. "Run workflow" 클릭
3. 로그에서 위의 **로그 확인 포인트** 검증

### **로컬 테스트**
```bash
# Telegram 테스트
python test_new_bot_safely.py

# Gmail 테스트
python test_gmail_new_password.py
```

## 📋 **최종 확인 사항**

- [ ] 스케줄 활성화 확인 (Actions → Enable workflow)
- [ ] 7개 Secrets 모두 설정 (Settings → Secrets)
- [ ] 포크가 아닌 원본 레포에서 실행
- [ ] Bot Token 유효성 확인 (@BotFather → /mybots)
- [ ] Gmail App Password 확인 (16자리)
- [ ] 워크플로우 수동 실행 테스트
- [ ] 로그에서 `has_tg=true`, `has_mail=true` 확인
- [ ] Telegram/Gmail 수신 확인

---
**작성 시간**: 2025-10-07
**적용 워크플로우**: `.github/workflows/marine-hourly.yml`
**상태**: ✅ 완전 패치 적용됨
