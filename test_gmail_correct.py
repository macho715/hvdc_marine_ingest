#!/usr/bin/env python3
"""KR: Gmail 알림 텍스트 검증 / EN: Gmail notification plain-text test."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from scripts.secret_helpers import load_secret, mask_secret


def main() -> None:
    """KR: Gmail 발송 확인 / EN: Validate Gmail delivery."""

    try:
        username = load_secret("MAIL_USERNAME")
        password = load_secret("MAIL_PASSWORD")
        to_email = load_secret("MAIL_TO")
    except RuntimeError as error:
        print(f"❌ 환경 변수 누락: {error}")
        print("ℹ️ .env 파일 또는 GitHub Secrets에서 값을 설정하세요.")
        return

    print("📧 Gmail 설정 테스트 (공백 제거)...")
    print(f"✅ Gmail 사용자명: {username}")
    print(f"✅ 수신자: {to_email}")
    print(f"✅ App Password: {mask_secret(password)}")

    try:
        print("\n📡 Gmail SMTP 연결 중...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        print("🔐 Gmail 로그인 시도 중...")
        server.login(username, password)
        print("✅ Gmail SMTP 로그인 성공!")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔍 HVDC Marine Weather System - Gmail 설정 성공"
        msg["From"] = f"HVDC Weather Bot <{username}>"
        msg["To"] = to_email

        text_content = (
            "🌊 HVDC Marine Weather System - Gmail 설정 성공\n\n"
            f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Gmail 사용자명: {username}\n"
            f"수신자: {to_email}\n\n"
            "✅ Gmail 설정이 완료되었습니다!\n"
            "✅ GitHub Actions에서 이메일 알림이 정상 작동할 것입니다!\n\n"
            "---\nHVDC Project - Samsung C&T Logistics"
        )

        text_part = MIMEText(text_content, "plain", "utf-8")
        msg.attach(text_part)

        print("📤 테스트 이메일 발송 중...")
        server.sendmail(username, to_email, msg.as_string())
        server.quit()

        print("✅ Gmail 테스트 이메일 발송 성공!")

        print("\n🎉 모든 알림 시스템 설정 완료!")
        print("\n📋 GitHub Secrets 설정 상태:")
        print("=" * 60)
        print(f"TELEGRAM_BOT_TOKEN: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
        print(f"TELEGRAM_CHAT_ID: {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}")
        print(f"MAIL_USERNAME: {username}")
        print(f"MAIL_PASSWORD: {mask_secret(password)}")
        print(f"MAIL_TO: {to_email}")
        print("\n🔧 GitHub Settings에서 위의 5개 시크릿을 설정하세요!")

    except smtplib.SMTPAuthenticationError as error:
        print(f"❌ Gmail 인증 실패: {error}")
        print("\n⚠️ Gmail App Password 문제:")
        print("1. Google 계정 → 보안 → 2단계 인증 활성화 여부 확인")
        print("2. 새로운 App Password를 생성")
        print("3. App Password는 16자리여야 합니다")
    except Exception as error:  # pragma: no cover - diagnostic helper
        print(f"❌ Gmail 연결 실패: {error}")


if __name__ == "__main__":
    main()
