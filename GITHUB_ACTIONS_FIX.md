# GitHub Actions 문제 해결 / GitHub Actions Fixes

## ✅ 해결된 문제 / Fixed Issues

### 1. Git Push 실패 (403 Permission Denied)
**문제**: `contents: read` 권한으로는 Git push 불가
```yaml
# 이전 (Before)
permissions:
  contents: read

# 수정 (After)
permissions:
  contents: write  # Git push를 위한 쓰기 권한
```

**파일**: `.github/workflows/marine-hourly.yml:18`

---

### 2. pandas.read_html 폴백 경고
**문제**: lxml이 없어서 NCM Selenium이 폴백 데이터 사용

**해결**:
```txt
# requirements.txt에 추가
lxml>=4.9.0
```

---

## ⚠️ 사용자 설정 필요 / User Configuration Required

### 3. Telegram "chat not found" 오류

**원인**:
- Chat ID가 잘못되었거나
- Bot이 채팅방에 초대되지 않음

**해결 방법**:

#### A. Chat ID 확인
1. Bot에게 메시지 전송
2. 브라우저에서 확인:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. `"chat":{"id":1234567890}` 확인
4. GitHub Secrets 업데이트:
   - Settings → Secrets and variables → Actions
   - `TELEGRAM_CHAT_ID` 값 확인/수정

#### B. Bot 초대 확인
- **개인 채팅**: Bot에게 먼저 `/start` 메시지 전송
- **그룹 채팅**: Bot을 그룹에 초대

#### C. 로컬 테스트
```bash
# .env 파일 설정
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# 테스트 실행
python scripts/send_notifications.py
```

---

### 4. WorldTides 크레딧 부족

**현상**: `Out of credits` 오류로 폴백 데이터 사용

**옵션**:

#### A. 크레딧 충전 (권장)
1. https://www.worldtides.info/ 로그인
2. Dashboard → Credits
3. 크레딧 구매

#### B. WorldTides 비활성화
시스템은 자동으로 폴백하므로 계속 사용 가능합니다.

**현재 데이터 소스 상태**:
```
✅ Stormglass API - 정상 (API 키 필요)
✅ Open-Meteo API - 정상 (무료, API 키 불필요)
⚠️ WorldTides API - 크레딧 부족 (폴백 사용)
⚠️ NCM Selenium - lxml 없음 (폴백 사용)
```

**수정 후 예상 상태**:
```
✅ Stormglass API - 정상
✅ Open-Meteo API - 정상
⚠️ WorldTides API - 크레딧 부족 (폴백 사용)
✅ NCM Selenium - 정상 (lxml 추가)
```

---

## 🚀 재실행 방법 / How to Rerun

### GitHub Actions에서 워크플로우 수동 실행

1. **워크플로우 페이지 접속**:
   ```
   https://github.com/macho715/hvdc_marine_ingest/actions/workflows/marine-hourly.yml
   ```

2. **"Run workflow" 클릭**:
   - Branch: `main` 선택
   - "Run workflow" 버튼 클릭

3. **실행 로그 확인**:
   - Actions 메인 페이지에서 최근 실행 확인
   - 각 스텝의 상태 확인

---

## 📊 예상 결과 / Expected Results

### 성공적인 실행 (All Secrets Configured)
```
✅ Compute gates
✅ Telegram ping - Bot 검증 성공
✅ Run marine weather collection
  ✅ Stormglass: 48 타임스텝
  ✅ Open-Meteo: 25 타임스텝
  ⚠️ WorldTides: 폴백 (크레딧 부족)
  ✅ NCM Selenium: 실제 데이터 (lxml 사용)
  📊 데이터 수집률: 75.0%
✅ Telegram notify - 알림 발송 성공
✅ Email notify - 이메일 발송 성공
```

### 일부 Secrets 누락 (Partial Configuration)
```
✅ Compute gates
⚠️ Telegram ping - 건너뜀 (시크릿 없음)
✅ Run marine weather collection
  ⚠️ 오프라인 모드 (API 키 없음)
  📊 데이터 수집률: 100% (합성 데이터)
⚠️ Telegram notify - 건너뜀
⚠️ Email notify - 건너뜀
```

---

## 🔧 추가 확인 사항 / Additional Checks

### Secrets 검증
GitHub → Settings → Secrets and variables → Actions

**필수**:
- ✅ `TELEGRAM_BOT_TOKEN`
- ✅ `TELEGRAM_CHAT_ID`
- ✅ `MAIL_USERNAME`
- ✅ `MAIL_PASSWORD`
- ✅ `MAIL_TO`

**선택**:
- ✅ `STORMGLASS_API_KEY`
- ✅ `WORLDTIDES_API_KEY`

---

## 📞 문제 해결 체크리스트 / Troubleshooting Checklist

- [x] ✅ Git push 권한 수정 (`contents: write`)
- [x] ✅ lxml 의존성 추가
- [ ] ⚠️ Telegram Chat ID 확인 필요
- [ ] ⚠️ Telegram Bot 초대 확인 필요
- [ ] ⚠️ WorldTides 크레딧 충전 (선택)

---

**🎯 다음 단계**: Git push 후 워크플로우를 재실행하여 수정사항을 확인하세요!

