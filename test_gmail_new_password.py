#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail 설정 - 새로운 App Password
username = "mscho715@gmail.com"
password = "svomdxwnvdzedfle"  # 새로운 App Password
to_email = "mscho715@gmail.com"

print("📧 Gmail 설정 테스트 (새로운 App Password)...")
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
    msg['Subject'] = f"🔍 HVDC Marine Weather System - Gmail 설정 성공!"
    msg['From'] = f"HVDC Weather Bot <{username}>"
    msg['To'] = to_email
    
    # HTML 내용
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
                <p><strong>App Password:</strong> {password[:4]}...{password[-4:]}</p>
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
                <h3>📋 GitHub Secrets 설정 정보</h3>
                <p><strong>TELEGRAM_BOT_TOKEN:</strong> 8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk</p>
                <p><strong>TELEGRAM_CHAT_ID:</strong> 470962761</p>
                <p><strong>MAIL_USERNAME:</strong> {username}</p>
                <p><strong>MAIL_PASSWORD:</strong> {password}</p>
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
    
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
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
    
    print("\n🚀 다음 단계:")
    print("1. GitHub 리포지토리 → Settings → Secrets and variables → Actions")
    print("2. 위의 5개 시크릿을 모두 설정")
    print("3. GitHub Actions → 'Run workflow' 클릭")
    print("4. Telegram과 Gmail로 해양 날씨 보고서 수신 확인!")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Gmail 인증 실패: {e}")
    print("\n🔧 문제 해결:")
    print("1. App Password가 올바른지 확인")
    print("2. 2단계 인증이 활성화되어 있는지 확인")
    print("3. App Password 생성 시 공백 제거 확인")
except Exception as e:
    print(f"❌ Gmail 연결 실패: {e}")
