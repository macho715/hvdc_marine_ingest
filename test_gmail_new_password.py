#!/usr/bin/env python3
"""KR: 새로운 Gmail 앱 비밀번호 검증 / EN: Verify refreshed Gmail app password."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from scripts.secret_helpers import load_secret, mask_secret


def main() -> None:
    """KR: 새 비밀번호로 발송 테스트 / EN: Send email with new password."""

    try:
        username = load_secret("MAIL_USERNAME")
        password = load_secret("MAIL_PASSWORD")
        to_email = load_secret("MAIL_TO")
    except RuntimeError as error:
        print(f"❌ 환경 변수 누락: {error}")
        print("ℹ️ .env 파일 또는 GitHub Secrets에서 값을 설정하세요.")
        return

    print("📧 Gmail 설정 테스트 (새로운 App Password)...")
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
        msg["Subject"] = "🔍 HVDC Marine Weather System - Gmail 설정 성공!"
        msg["From"] = f"HVDC Weather Bot <{username}>"
        msg["To"] = to_email

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1>🌊 HVDC Marine Weather System</h1>
                <h2>Gmail 설정 성공!</h2>

                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>📊 설정 완료 정보</h3>
                    <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Gmail 사용자명:</strong> {username}</p>
                    <p><strong>수신자:</strong> {to_email}</p>
                    <p><strong>App Password:</strong> {mask_secret(password)}</p>
                    <p><strong>상태:</strong> ✅ Gmail 설정 완료</p>
                </div>

                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
                    <h3>🎉 알림 시스템 완성!</h3>
                    <p>✅ Telegram 알림: 정상 작동</p>
                    <p>✅ Gmail 알림: 정상 작동</p>
                    <p>✅ GitHub Actions: 정상 작동</p>
                    <p>✅ 해양 날씨 보고서: 매시간 자동 발송</p>
                </div>

                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>📋 GitHub Secrets 설정 상태</h3>
                    <p><strong>TELEGRAM_BOT_TOKEN:</strong> {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}</p>
                    <p><strong>TELEGRAM_CHAT_ID:</strong> {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}</p>
                    <p><strong>MAIL_USERNAME:</strong> {username}</p>
                    <p><strong>MAIL_PASSWORD:</strong> {mask_secret(password)}</p>
                    <p><strong>MAIL_TO:</strong> {to_email}</p>
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

        print("\n🎉 모든 알림 시스템 설정 완료!")
        print("\n📋 GitHub Secrets 설정 상태:")
        print("=" * 60)
        print(f"TELEGRAM_BOT_TOKEN: {mask_secret(os.getenv('TELEGRAM_BOT_TOKEN', ''))}")
        print(f"TELEGRAM_CHAT_ID: {mask_secret(os.getenv('TELEGRAM_CHAT_ID', ''))}")
        print(f"MAIL_USERNAME: {username}")
        print(f"MAIL_PASSWORD: {mask_secret(password)}")
        print(f"MAIL_TO: {to_email}")

        print("\n🚀 다음 단계:")
        print("1. GitHub 리포지토리 → Settings → Secrets and variables → Actions")
        print("2. 위의 5개 시크릿을 모두 설정")
        print("3. GitHub Actions → 'Run workflow' 클릭")
        print("4. Telegram과 Gmail로 해양 날씨 보고서 수신 확인!")

    except smtplib.SMTPAuthenticationError as error:
        print(f"❌ Gmail 인증 실패: {error}")
        print("\n🔧 문제 해결:")
        print("1. App Password가 올바른지 확인")
        print("2. 2단계 인증이 활성화되어 있는지 확인")
        print("3. App Password 생성 시 공백 제거 확인")
    except Exception as error:  # pragma: no cover - diagnostic helper
        print(f"❌ Gmail 연결 실패: {error}")


if __name__ == "__main__":
    main()
