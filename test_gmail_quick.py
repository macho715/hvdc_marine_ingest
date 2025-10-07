#!/usr/bin/env python3
"""KR: Gmail 알림 연동 점검 / EN: Gmail notification smoke test."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from scripts.secret_helpers import load_secret, mask_secret


def main() -> None:
    """KR: 시크릿을 노출 없이 검증 / EN: Verify secrets without leaking."""

    try:
        username = load_secret("MAIL_USERNAME")
        password = load_secret("MAIL_PASSWORD").replace(" ", "")
        to_email = load_secret("MAIL_TO")
    except RuntimeError as error:
        print(f"❌ 환경 변수 누락: {error}")
        print("ℹ️ .env 파일 또는 GitHub Secrets에서 값을 설정하세요.")
        return

    print("📧 Gmail 설정 테스트 시작...")
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

        print("📝 테스트 이메일 작성 중...")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            "🔍 HVDC Marine Weather System - Gmail 설정 검증 "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        msg["From"] = f"HVDC Weather Bot <{username}>"
        msg["To"] = to_email

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1>🌊 HVDC Marine Weather System</h1>
                <h2>Gmail 설정 검증 성공</h2>

                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>📊 테스트 정보</h3>
                    <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Gmail 사용자명:</strong> {username}</p>
                    <p><strong>수신자:</strong> {to_email}</p>
                    <p><strong>상태:</strong> Gmail 설정 검증 성공</p>
                </div>

                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
                    <p>✅ 이 이메일이 수신되면 Gmail 설정이 완료되었습니다!</p>
                    <p>✅ App Password가 올바르게 작동합니다!</p>
                </div>

                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    HVDC Project - Samsung C&T Logistics<br>
                    Marine Weather Notification System
                </p>
            </div>
        </body>
        </html>
        """

        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        print("📤 테스트 이메일 발송 중...")
        server.sendmail(username, to_email, msg.as_string())
        server.quit()

        print("✅ Gmail 테스트 이메일 발송 성공!")

        print("\n📋 GitHub Secrets 설정 상태:")
        print("=" * 50)
        print(f"TELEGRAM_BOT_TOKEN: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
        print(f"TELEGRAM_CHAT_ID: {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}")
        print(f"MAIL_USERNAME: {username}")
        print(f"MAIL_PASSWORD: {mask_secret(password)}")
        print(f"MAIL_TO: {to_email}")

    except smtplib.SMTPAuthenticationError as error:
        print(f"❌ Gmail 인증 실패: {error}")
        print("\n🔧 해결 방법:")
        print("1. Google 계정 → 보안 → 2단계 인증 활성화")
        print("2. 앱 비밀번호를 새로 생성하고 16자리 값을 사용")
        print("3. 일반 비밀번호가 아닌 앱 비밀번호를 사용")
    except Exception as error:  # pragma: no cover - diagnostic helper
        print(f"❌ Gmail 연결 실패: {error}")


if __name__ == "__main__":
    main()
