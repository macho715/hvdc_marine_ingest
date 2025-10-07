#!/usr/bin/env python3
"""KR: 로컬 알림 전송 테스트 / EN: Local notification test."""

from __future__ import annotations

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from secret_helpers import load_secret, mask_secret


def send_telegram_notification(summary_file: Path) -> bool:
    """KR: Telegram 알림 전송 / EN: Send Telegram notification."""
    
    try:
        bot_token = load_secret("TELEGRAM_BOT_TOKEN", allow_empty=True)
        chat_id = load_secret("TELEGRAM_CHAT_ID", allow_empty=True)
        
        if not bot_token or not chat_id:
            print("⚠️ Telegram 시크릿 없음 - 건너뜀")
            return False
        
        print(f"\n📱 Telegram 알림 전송 중...")
        print(f"  Bot Token: {mask_secret(bot_token)}")
        print(f"  Chat ID: {mask_secret(chat_id)}")
        
        # 요약 파일 읽기
        with open(summary_file, 'r', encoding='utf-8') as f:
            message = f.read()
        
        # Telegram API 호출
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            print("  ✅ Telegram 알림 전송 성공!")
            return True
        else:
            print(f"  ❌ Telegram 전송 실패: {result}")
            return False
            
    except Exception as e:
        print(f"  ❌ Telegram 오류: {e}")
        return False


def send_email_notification(summary_file: Path) -> bool:
    """KR: 이메일 알림 전송 / EN: Send email notification."""
    
    try:
        username = load_secret("MAIL_USERNAME", allow_empty=True)
        password = load_secret("MAIL_PASSWORD", allow_empty=True)
        to_email = load_secret("MAIL_TO", allow_empty=True)
        
        if not username or not password or not to_email:
            print("⚠️ Email 시크릿 없음 - 건너뜀")
            return False
        
        print(f"\n📧 Email 알림 전송 중...")
        print(f"  From: {username}")
        print(f"  To: {to_email}")
        print(f"  Password: {mask_secret(password)}")
        
        # 요약 파일 읽기
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 이메일 작성
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌊 HVDC Marine Weather Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg["From"] = f"HVDC Weather Bot <{username}>"
        msg["To"] = to_email
        
        text_part = MIMEText(content, "plain", "utf-8")
        msg.attach(text_part)
        
        # SMTP 전송
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(username, password)
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        
        print("  ✅ Email 알림 전송 성공!")
        return True
        
    except Exception as e:
        print(f"  ❌ Email 오류: {e}")
        return False


def main():
    """KR: 알림 전송 메인 / EN: Main notification sender."""
    
    print("=" * 60)
    print("📨 HVDC Marine 알림 시스템 테스트")
    print("=" * 60)
    
    # 요약 파일 찾기
    summary_file = Path("out/summary.txt")
    if not summary_file.exists():
        print(f"❌ 요약 파일 없음: {summary_file}")
        print("먼저 weather_job.py를 실행하세요:")
        print("  python scripts/weather_job.py --mode auto")
        return False
    
    print(f"✅ 요약 파일: {summary_file}")
    print(f"  크기: {summary_file.stat().st_size} bytes")
    
    # 알림 전송
    tg_success = send_telegram_notification(summary_file)
    email_success = send_email_notification(summary_file)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 알림 전송 결과")
    print("=" * 60)
    print(f"📱 Telegram: {'✅ 성공' if tg_success else '❌ 실패'}")
    print(f"📧 Email: {'✅ 성공' if email_success else '❌ 실패'}")
    
    if tg_success or email_success:
        print("\n🎉 알림 전송 완료!")
        return True
    else:
        print("\n⚠️ 알림 전송 실패")
        print("환경변수를 설정하세요:")
        print("  $env:TELEGRAM_BOT_TOKEN='your_token'")
        print("  $env:TELEGRAM_CHAT_ID='your_chat_id'")
        print("  $env:MAIL_USERNAME='your_email@gmail.com'")
        print("  $env:MAIL_PASSWORD='your_app_password'")
        print("  $env:MAIL_TO='recipient@example.com'")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

