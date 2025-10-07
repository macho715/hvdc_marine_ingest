#!/usr/bin/env python3
"""KR: 로컬 전체 테스트 (날씨+알림) / EN: Local full test (weather+notifications)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

print("=" * 70)
print("🚀 HVDC Marine - 로컬 전체 시스템 테스트")
print("=" * 70)

# 환경변수 확인
print("\n🔍 환경변수 확인:")
secrets_to_check = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "MAIL_USERNAME",
    "MAIL_PASSWORD",
    "MAIL_TO",
    "STORMGLASS_API_KEY",
    "WORLDTIDES_API_KEY"
]

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from secret_helpers import mask_secret

for secret_name in secrets_to_check:
    value = os.getenv(secret_name, "")
    status = "✅ 설정됨" if value else "❌ 없음"
    masked = mask_secret(value) if value else "[missing]"
    print(f"  {secret_name}: {status} ({masked})")

# 1. 날씨 데이터 수집
print("\n" + "=" * 70)
print("1️⃣ 해양 날씨 데이터 수집")
print("=" * 70)

import subprocess

result = subprocess.run(
    ["python", "scripts/weather_job.py", "--location", "AGI", "--hours", "24", "--mode", "auto", "--out", "out"],
    capture_output=False,
    text=True
)

if result.returncode != 0:
    print("❌ 날씨 데이터 수집 실패")
    sys.exit(1)

# 2. 알림 전송
print("\n" + "=" * 70)
print("2️⃣ 알림 전송 테스트")
print("=" * 70)

result = subprocess.run(
    ["python", "scripts/send_notifications.py"],
    capture_output=False,
    text=True
)

# 3. 최종 결과
print("\n" + "=" * 70)
print("🎉 로컬 테스트 완료")
print("=" * 70)

if result.returncode == 0:
    print("✅ 모든 테스트 성공!")
    print("\n📱 Telegram을 확인하세요 (알림이 설정된 경우)")
    print("📧 Email을 확인하세요 (알림이 설정된 경우)")
else:
    print("⚠️ 알림 전송 실패 (시크릿 미설정)")
    print("\n.env 파일을 설정하세요:")
    print("  1. cp config/.env.example .env")
    print("  2. .env 파일 편집")
    print("  3. python run_local_test.py 재실행")

sys.exit(result.returncode)

