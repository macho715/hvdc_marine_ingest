#!/usr/bin/env python3
"""
로컬 알림 시스템 테스트 스크립트
GitHub Actions 없이 Telegram과 Email 발송 테스트
"""

import os
import sys
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def test_telegram_notification():
    """Telegram 알림 테스트"""
    print("🤖 Telegram 알림 테스트 시작...")
    
    # 환경변수에서 시크릿 가져오기
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다")
        print("   설정 방법: export TELEGRAM_BOT_TOKEN='your_bot_token'")
        return False
        
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID 환경변수가 설정되지 않았습니다")
        print("   설정 방법: export TELEGRAM_CHAT_ID='your_chat_id'")
        return False
    
    print(f"✅ Bot Token: {bot_token[:10]}...{bot_token[-10:]}")
    print(f"✅ Chat ID: {chat_id}")
    
    # 1. Bot 정보 확인
    print("📡 Bot Token 유효성 확인 중...")
    try:
        bot_info_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(bot_info_url, timeout=10)
        
        if response.status_code == 200:
            bot_data = response.json()
            if bot_data.get('ok'):
                print(f"✅ Bot 정보: {bot_data['result']['first_name']} (@{bot_data['result'].get('username', 'N/A')})")
            else:
                print(f"❌ Bot API 오류: {bot_data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Bot 정보 확인 실패: {e}")
        return False
    
    # 2. 테스트 메시지 발송
    print("📱 테스트 메시지 발송 중...")
    try:
        test_message = f"""🔍 HVDC Marine Weather System - 로컬 테스트

⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌊 시스템: 해양 날씨 알림 시스템
📊 상태: 로컬 테스트 성공

이 메시지가 수신되면 Telegram 알림이 정상 작동합니다!"""
        
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(send_url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Telegram 테스트 메시지 발송 성공!")
                print(f"   Message ID: {result['result']['message_id']}")
                return True
            else:
                print(f"❌ Telegram API 오류: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메시지 발송 실패: {e}")
        return False

def test_email_notification():
    """Email 알림 테스트"""
    print("\n📧 Email 알림 테스트 시작...")
    
    # 환경변수에서 시크릿 가져오기
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    to_email = os.getenv('MAIL_TO')
    
    if not username:
        print("❌ MAIL_USERNAME 환경변수가 설정되지 않았습니다")
        print("   설정 방법: export MAIL_USERNAME='your_email@gmail.com'")
        return False
        
    if not password:
        print("❌ MAIL_PASSWORD 환경변수가 설정되지 않았습니다")
        print("   설정 방법: export MAIL_PASSWORD='your_app_password'")
        return False
        
    if not to_email:
        print("❌ MAIL_TO 환경변수가 설정되지 않았습니다")
        print("   설정 방법: export MAIL_TO='recipient@gmail.com'")
        return False
    
    print(f"✅ Gmail 사용자명: {username}")
    print(f"✅ 수신자: {to_email}")
    print(f"✅ App Password: {'*' * len(password)}")
    
    try:
        # SMTP 연결 테스트
        print("📡 Gmail SMTP 연결 중...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(username, password)
        print("✅ Gmail SMTP 로그인 성공!")
        
        # 테스트 이메일 작성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🔍 HVDC Marine Weather System - 로컬 테스트 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg['From'] = f"HVDC Weather Bot <{username}>"
        msg['To'] = to_email
        
        # HTML 내용
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1>🌊 HVDC Marine Weather System</h1>
                <h2>로컬 테스트 성공</h2>
                
                <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>📊 테스트 정보</h3>
                    <p><strong>테스트 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>시스템:</strong> 해양 날씨 알림 시스템</p>
                    <p><strong>상태:</strong> 로컬 테스트 성공</p>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px;">
                    <p>✅ 이 이메일이 수신되면 Email 알림이 정상 작동합니다!</p>
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
        print("📧 테스트 이메일 발송 중...")
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        
        print("✅ Email 테스트 발송 성공!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Gmail 인증 실패: {e}")
        print("   → Gmail App Password를 확인하세요 (16자리)")
        print("   → 2단계 인증이 활성화되어 있는지 확인하세요")
        return False
    except Exception as e:
        print(f"❌ Email 발송 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚢 HVDC Marine Weather - 로컬 알림 테스트")
    print("=" * 60)
    
    # 환경변수 설정 안내
    print("📋 환경변수 설정 안내:")
    print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
    print("   export TELEGRAM_CHAT_ID='your_chat_id'")
    print("   export MAIL_USERNAME='your_email@gmail.com'")
    print("   export MAIL_PASSWORD='your_app_password'")
    print("   export MAIL_TO='recipient@gmail.com'")
    print()
    
    telegram_success = test_telegram_notification()
    email_success = test_email_notification()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약:")
    print(f"   Telegram: {'✅ 성공' if telegram_success else '❌ 실패'}")
    print(f"   Email: {'✅ 성공' if email_success else '❌ 실패'}")
    
    if telegram_success and email_success:
        print("\n🎉 모든 알림 시스템이 정상 작동합니다!")
    else:
        print("\n⚠️ 일부 알림 시스템에 문제가 있습니다.")
        print("   GitHub Actions 로그를 확인하고 환경변수를 재설정하세요.")

if __name__ == "__main__":
    main()
