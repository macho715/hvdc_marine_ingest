#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail 설정 - 공백 제거된 App Password
username = "mscho715@gmail.com"
password = "svomdxwnvdzep"  # 공백 제거
to_email = "mscho715@gmail.com"

print("📧 Gmail 설정 테스트 (공백 제거)...")
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
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 성공"
    msg['From'] = f"HVDC Weather Bot <{username}>"
    msg['To'] = to_email
    
    text_content = f"""🌊 HVDC Marine Weather System - Gmail 설정 성공

테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Gmail 사용자명: {username}
수신자: {to_email}

✅ Gmail 설정이 완료되었습니다!
✅ GitHub Actions에서 이메일 알림이 정상 작동할 것입니다!

---
HVDC Project - Samsung C&T Logistics"""
    
    text_part = MIMEText(text_content, 'plain', 'utf-8')
    msg.attach(text_part)
    
    # 이메일 발송
    print("📤 테스트 이메일 발송 중...")
    server.sendmail(username, to_email, msg.as_string())
    server.quit()
    
    print("✅ Gmail 테스트 이메일 발송 성공!")
    
    print("\n🎉 모든 알림 시스템 설정 완료!")
    print("\n📋 GitHub Secrets 설정 정보:")
    print("=" * 60)
    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
    print("TELEGRAM_CHAT_ID: 470962761")
    print(f"MAIL_USERNAME: {username}")
    print(f"MAIL_PASSWORD: {password}")
    print(f"MAIL_TO: {to_email}")
    print("\n🔧 이제 GitHub Settings에서 위의 5개 시크릿을 설정하세요!")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Gmail 인증 실패: {e}")
    print("\n⚠️ Gmail App Password 문제:")
    print("1. Google 계정 → 보안 → 2단계 인증이 활성화되어 있는지 확인")
    print("2. 새로운 App Password를 생성해보세요")
    print("3. App Password는 16자리여야 합니다")
    
    # 임시로 GitHub Secrets 설정 정보만 제공
    print("\n📋 GitHub Secrets 설정 정보 (Telegram은 정상):")
    print("=" * 60)
    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
    print("TELEGRAM_CHAT_ID: 470962761")
    print("MAIL_USERNAME: [Gmail 주소]")
    print("MAIL_PASSWORD: [16자리 앱 비밀번호]")
    print("MAIL_TO: [수신자 이메일]")
    
except Exception as e:
    print(f"❌ Gmail 연결 실패: {e}")
