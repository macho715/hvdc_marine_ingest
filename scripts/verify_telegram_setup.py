#!/usr/bin/env python3
"""
Telegram Bot 설정 검증 스크립트
Bot Token과 Chat ID의 유효성을 확인합니다.
"""

import requests
import json

def verify_bot_token(token):
    """Bot Token 유효성 확인"""
    print(f"🤖 Bot Token 검증 중: {token[:10]}...{token[-10:]}")
    
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print("✅ Bot Token 유효!")
                print(f"   Bot 이름: {bot_info['first_name']}")
                print(f"   Bot 사용자명: @{bot_info.get('username', 'N/A')}")
                print(f"   Bot ID: {bot_info['id']}")
                return True, bot_info
            else:
                print(f"❌ Bot API 오류: {data.get('description', 'Unknown error')}")
                return False, None
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Bot Token 검증 실패: {e}")
        return False, None

def get_chat_id(token):
    """Chat ID 확인 (최근 메시지에서)"""
    print("📱 Chat ID 확인 중...")
    
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data['result']
                if updates:
                    # 가장 최근 메시지의 chat_id 찾기
                    latest_update = updates[-1]
                    chat_id = latest_update['message']['chat']['id']
                    chat_info = latest_update['message']['chat']
                    
                    print("✅ Chat ID 확인!")
                    print(f"   Chat ID: {chat_id}")
                    print(f"   Chat 타입: {chat_info.get('type', 'N/A')}")
                    if 'first_name' in chat_info:
                        print(f"   사용자명: {chat_info['first_name']}")
                    if 'username' in chat_info:
                        print(f"   사용자명: @{chat_info['username']}")
                    
                    return chat_id
                else:
                    print("⚠️ 메시지가 없습니다.")
                    print("   → 봇과 대화를 시작하고 메시지를 보내세요")
                    return None
            else:
                print(f"❌ getUpdates API 오류: {data.get('description', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Chat ID 확인 실패: {e}")
        return None

def test_message_sending(token, chat_id):
    """테스트 메시지 발송"""
    print(f"📤 테스트 메시지 발송 중... (Chat ID: {chat_id})")
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        message = """🔍 HVDC Marine Weather System - 설정 검증

✅ Bot Token: 유효
✅ Chat ID: 유효
✅ 메시지 발송: 성공

이 메시지가 수신되면 Telegram 설정이 완료되었습니다!"""
        
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ 테스트 메시지 발송 성공!")
                print(f"   Message ID: {result['result']['message_id']}")
                return True
            else:
                print(f"❌ 메시지 발송 실패: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 메시지 발송 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚢 HVDC Marine Weather - Telegram 설정 검증")
    print("=" * 60)
    
    # Bot Token 입력
    print("📋 Bot Token을 입력하세요:")
    print("   (예: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)")
    bot_token = input("Bot Token: ").strip()
    
    if not bot_token:
        print("❌ Bot Token이 입력되지 않았습니다.")
        return
    
    # Bot Token 검증
    is_valid, bot_info = verify_bot_token(bot_token)
    if not is_valid:
        print("\n❌ Bot Token이 유효하지 않습니다.")
        print("   → @BotFather에서 새로운 토큰을 생성하세요")
        return
    
    print("\n" + "-" * 40)
    
    # Chat ID 확인
    chat_id = get_chat_id(bot_token)
    if not chat_id:
        print("\n❌ Chat ID를 확인할 수 없습니다.")
        print("   → 봇과 대화를 시작하고 메시지를 보내세요")
        return
    
    print("\n" + "-" * 40)
    
    # 테스트 메시지 발송
    success = test_message_sending(bot_token, chat_id)
    
    print("\n" + "=" * 60)
    print("📊 Telegram 설정 검증 결과:")
    print(f"   Bot Token: {'✅ 유효' if is_valid else '❌ 무효'}")
    print(f"   Chat ID: {'✅ 확인됨' if chat_id else '❌ 확인 실패'}")
    print(f"   메시지 발송: {'✅ 성공' if success else '❌ 실패'}")
    
    if is_valid and chat_id and success:
        print("\n🎉 Telegram 설정이 완료되었습니다!")
        print(f"\n📋 GitHub Secrets에 설정할 값들:")
        print(f"   TELEGRAM_BOT_TOKEN: {bot_token}")
        print(f"   TELEGRAM_CHAT_ID: {chat_id}")
    else:
        print("\n⚠️ Telegram 설정에 문제가 있습니다.")
        print("   → 위의 오류를 해결하고 다시 시도하세요.")

if __name__ == "__main__":
    main()
