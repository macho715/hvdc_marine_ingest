#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail 설정
username = "mscho715@gmail.com"
password = "svomdxwnvdzep"  # App Password (공백 제거)
to_email = "mscho715@gmail.com"

print("📧 Gmail 설정 테스트 (최종)...")
print(f"✅ Gmail 사용자명: {username}")
print(f"✅ 수신자: {to_email}")
print(f"✅ App Password: {password}")

try:
    # SMTP 연결 테스트
    print("\n📡 Gmail SMTP 연결 중...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    
    print("🔐 Gmail 로그인 시도 중...")
    server.login(username, password)
    print("✅ Gmail SMTP 로그인 성공!")
    
    # 테스트 이메일 작성
    print("📝 테스트 이메일 작성 중...")
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 검증 성공"
    msg['From'] = f"HVDC Weather Bot <{username}>"
    msg['To'] = to_email
    
    # 간단한 텍스트 메시지
    text_content = f"""
🌊 HVDC Marine Weather System - Gmail 설정 검증 성공

테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Gmail 사용자명: {username}
수신자: {to_email}

✅ 이 이메일이 수신되면 Gmail 설정이 완료되었습니다!
✅ App Password가 올바르게 작동합니다!

---
HVDC Project - Samsung C&T Logistics
Marine Weather Notification System
    """
    
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    msg.attach(text_part)
    
    # 이메일 발송
    print("📤 테스트 이메일 발송 중...")
    server.sendmail(username, to_email, msg.as_string())
    server.quit()
    
    print("✅ Gmail 테스트 이메일 발송 성공!")
    
    print("\n🎉 모든 설정이 완료되었습니다!")
    print("\n📋 GitHub Secrets 설정 정보:")
    print("=" * 50)
    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
    print("TELEGRAM_CHAT_ID: 470962761")
    print(f"MAIL_USERNAME: {username}")
    print(f"MAIL_PASSWORD: {password}")
    print(f"MAIL_TO: {to_email}")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Gmail 인증 실패: {e}")
    print("\n🔧 문제 해결:")
    print("1. App Password가 올바른지 확인")
    print("2. 2단계 인증이 활성화되어 있는지 확인")
    print("3. App Password 생성 시 공백 제거 확인")
except Exception as e:
    print(f"❌ Gmail 연결 실패: {e}")
