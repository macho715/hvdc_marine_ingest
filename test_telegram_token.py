#!/usr/bin/env python3
import requests

# 제공받은 Bot Token
bot_token = "8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk"

print(f"🤖 Bot Token 검증: {bot_token[:10]}...{bot_token[-10:]}")

# Bot 정보 확인
try:
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data['result']
            print("✅ Bot Token 유효!")
            print(f"   Bot 이름: {bot_info['first_name']}")
            print(f"   Bot 사용자명: @{bot_info.get('username', 'N/A')}")
            print(f"   Bot ID: {bot_info['id']}")
        else:
            print(f"❌ Bot API 오류: {data.get('description', 'Unknown error')}")
    else:
        print(f"❌ HTTP 오류: {response.status_code}")
        print(f"   응답: {response.text}")
        
except Exception as e:
    print(f"❌ 요청 실패: {e}")

# Chat ID 확인
try:
    print("\n📱 Chat ID 확인 중...")
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            updates = data['result']
            if updates:
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
            else:
                print("⚠️ 메시지가 없습니다.")
                print("   → 봇과 대화를 시작하고 메시지를 보내세요")
        else:
            print(f"❌ getUpdates API 오류: {data.get('description', 'Unknown error')}")
    else:
        print(f"❌ HTTP 오류: {response.status_code}")
        
except Exception as e:
    print(f"❌ Chat ID 확인 실패: {e}")
