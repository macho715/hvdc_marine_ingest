#!/usr/bin/env python3
"""
Gmail 설정 검증 스크립트
Gmail App Password의 유효성을 확인합니다.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_gmail_connection():
    """Gmail SMTP 연결 테스트"""
    print("📧 Gmail 설정 검증 시작...")
    
    # Gmail 계정 정보 (실제 값으로 교체 필요)
    username = input("Gmail 주소를 입력하세요 (예: your_email@gmail.com): ").strip()
    password = input("Gmail App Password를 입력하세요 (16자리): ").strip()
    to_email = input("수신자 이메일을 입력하세요: ").strip()
    
    if not all([username, password, to_email]):
        print("❌ 모든 정보를 입력해주세요.")
        return False
    
    print(f"✅ Gmail 사용자명: {username}")
    print(f"✅ 수신자: {to_email}")
    print(f"✅ App Password: {'*' * len(password)}")
    
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
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Gmail 인증 실패: {e}")
        print("\n🔧 해결 방법:")
        print("1. Google 계정 → 보안 → 2단계 인증 활성화")
        print("2. 앱 비밀번호 생성 (16자리)")
        print("3. 일반 비밀번호가 아닌 앱 비밀번호 사용")
        return False
    except Exception as e:
        print(f"❌ Gmail 연결 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚢 HVDC Marine Weather - Gmail 설정 검증")
    print("=" * 60)
    
    print("📋 Gmail App Password 생성 방법:")
    print("1. Google 계정 → 보안 → 2단계 인증 활성화")
    print("2. 앱 비밀번호 생성 (16자리)")
    print("3. 일반 비밀번호가 아닌 앱 비밀번호 사용")
    print()
    
    success = test_gmail_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Gmail 설정이 완료되었습니다!")
        print("\n📋 GitHub Secrets에 설정할 값들:")
        print("   MAIL_USERNAME: [Gmail 주소]")
        print("   MAIL_PASSWORD: [16자리 앱 비밀번호]")
        print("   MAIL_TO: [수신자 이메일]")
    else:
        print("⚠️ Gmail 설정에 문제가 있습니다.")
        print("   → 위의 해결 방법을 따라 설정을 완료하세요.")

if __name__ == "__main__":
    main()
