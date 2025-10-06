#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail 설정 (실제 값으로 교체 필요)
username = "mscho715@gmail.com"  # Gmail 주소
password = "svom dxwn vdze dfle"  # App Password (공백 제거)
to_email = "mscho715@gmail.com"   # 수신자

# 공백 제거
password = password.replace(" ", "")

print("📧 Gmail 설정 테스트 시작...")
print(f"✅ Gmail 사용자명: {username}")
print(f"✅ 수신자: {to_email}")
print(f"✅ App Password: {password[:4]}...{password[-4:]}")

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
    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 검증 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    msg['From'] = f"HVDC Weather Bot <{username}>"
    msg['To'] = to_email
    
    # HTML 내용
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
    
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
    # 이메일 발송
    print("📤 테스트 이메일 발송 중...")
    server.sendmail(username, to_email, msg.as_string())
    server.quit()
    
    print("✅ Gmail 테스트 이메일 발송 성공!")
    
    print("\n📋 GitHub Secrets 설정 정보:")
    print("=" * 50)
    print("TELEGRAM_BOT_TOKEN: 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk")
    print("TELEGRAM_CHAT_ID: 470962761")
    print(f"MAIL_USERNAME: {username}")
    print(f"MAIL_PASSWORD: {password}")
    print(f"MAIL_TO: {to_email}")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Gmail 인증 실패: {e}")
    print("\n🔧 해결 방법:")
    print("1. Google 계정 → 보안 → 2단계 인증 활성화")
    print("2. 앱 비밀번호 생성 (16자리)")
    print("3. 일반 비밀번호가 아닌 앱 비밀번호 사용")
except Exception as e:
    print(f"❌ Gmail 연결 실패: {e}")
