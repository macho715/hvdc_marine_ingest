#!/usr/bin/env python3
"""
안전한 Telegram Bot 테스트 스크립트
환경 변수나 사용자 입력을 통해서만 토큰을 받습니다.
"""

import os
import requests
import sys

def test_bot_token_safely():
    print("🤖 안전한 Telegram Bot 테스트")
    print("=" * 50)
    
    # 방법 1: 환경 변수에서 토큰 읽기
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        # 방법 2: 사용자 입력으로 토큰 받기
        print("⚠️ 환경 변수 TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        print("새로 생성한 Bot Token을 입력하세요:")
        bot_token = input("Bot Token: ").strip()
        
        if not bot_token:
            print("❌ Bot Token이 입력되지 않았습니다.")
            return False
    
    # 토큰 마스킹 출력
    masked_token = f"{bot_token[:10]}...{bot_token[-10:]}" if len(bot_token) > 20 else "***"
    print(f"🔍 테스트 중: {masked_token}")
    
    try:
        # Bot 정보 확인
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                print(f"✅ Bot 활성화 확인:")
                print(f"   이름: {bot_info['result']['first_name']}")
                print(f"   사용자명: @{bot_info['result']['username']}")
                print(f"   Bot ID: {bot_info['result']['id']}")
                
                # Chat ID 확인
                print(f"\n📱 Chat ID 확인:")
                chat_id = input("새 봇과 대화를 시작한 후 Chat ID를 입력하세요: ").strip()
                
                if chat_id:
                    # 테스트 메시지 전송
                    test_msg = "🔍 HVDC Marine Weather - 새 Bot Token 테스트 성공!"
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    
                    payload = {
                        'chat_id': chat_id,
                        'text': test_msg,
                        'parse_mode': 'HTML'
                    }
                    
                    response = requests.post(send_url, json=payload, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result['ok']:
                            print(f"✅ 테스트 메시지 전송 성공!")
                            print(f"   메시지 ID: {result['result']['message_id']}")
                            print(f"\n🎯 새로운 설정 정보:")
                            print(f"   TELEGRAM_BOT_TOKEN: {masked_token}")
                            print(f"   TELEGRAM_CHAT_ID: {chat_id}")
                            return True
                        else:
                            print(f"❌ 메시지 전송 실패: {result}")
                    else:
                        print(f"❌ API 오류: {response.status_code}")
                else:
                    print("❌ Chat ID가 입력되지 않았습니다.")
            else:
                print(f"❌ Bot 정보 오류: {bot_info}")
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
    
    return False

def main():
    print("🔒 보안 강화된 Telegram Bot 테스트")
    print("이 스크립트는 토큰을 코드에 하드코딩하지 않습니다.")
    print("환경 변수나 사용자 입력을 통해서만 토큰을 받습니다.\n")
    
    success = test_bot_token_safely()
    
    if success:
        print("\n🎉 새 Bot Token 테스트 성공!")
        print("이제 GitHub Secrets를 업데이트하세요.")
    else:
        print("\n❌ Bot Token 테스트 실패")
        print("새로운 Bot Token을 다시 확인하세요.")

if __name__ == "__main__":
    main()
