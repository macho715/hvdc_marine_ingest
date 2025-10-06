#!/usr/bin/env python3
import requests

# Bot Token
bot_token = "8396276442:AAGGmN1wfEPoCNqXTt7YnN3SXunsK6eULUk"

print("📱 Chat ID 확인 중...")
print("   → 봇과 대화를 시작하고 메시지를 보내세요")

try:
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            updates = data['result']
            if updates:
                print(f"✅ {len(updates)}개의 메시지 발견!")
                
                # 모든 Chat ID 출력
                chat_ids = set()
                for update in updates:
                    if 'message' in update:
                        chat_id = update['message']['chat']['id']
                        chat_info = update['message']['chat']
                        chat_ids.add(chat_id)
                        
                        print(f"\n📋 Chat 정보:")
                        print(f"   Chat ID: {chat_id}")
                        print(f"   타입: {chat_info.get('type', 'N/A')}")
                        if 'first_name' in chat_info:
                            print(f"   이름: {chat_info['first_name']}")
                        if 'username' in chat_info:
                            print(f"   사용자명: @{chat_info['username']}")
                        if 'last_name' in chat_info:
                            print(f"   성: {chat_info['last_name']}")
                        
                        # 최근 메시지 내용
                        if 'text' in update['message']:
                            print(f"   최근 메시지: {update['message']['text']}")
                
                # 가장 최근 Chat ID 사용
                latest_chat_id = updates[-1]['message']['chat']['id']
                print(f"\n🎯 사용할 Chat ID: {latest_chat_id}")
                
                # 테스트 메시지 발송
                print(f"\n📤 테스트 메시지 발송 중...")
                test_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                test_data = {
                    'chat_id': latest_chat_id,
                    'text': '🔍 HVDC Marine Weather System - Chat ID 검증 성공!\n\n이 메시지가 수신되면 설정이 완료되었습니다!',
                    'parse_mode': 'HTML'
                }
                
                test_response = requests.post(test_url, data=test_data, timeout=10)
                if test_response.status_code == 200:
                    result = test_response.json()
                    if result.get('ok'):
                        print("✅ 테스트 메시지 발송 성공!")
                        print(f"   Message ID: {result['result']['message_id']}")
                    else:
                        print(f"❌ 메시지 발송 실패: {result.get('description', 'Unknown error')}")
                else:
                    print(f"❌ HTTP 오류: {test_response.status_code}")
                    
            else:
                print("⚠️ 메시지가 없습니다.")
                print("   → @Logimarine_bot와 대화를 시작하고 메시지를 보내세요")
        else:
            print(f"❌ getUpdates API 오류: {data.get('description', 'Unknown error')}")
    else:
        print(f"❌ HTTP 오류: {response.status_code}")
        
except Exception as e:
    print(f"❌ 요청 실패: {e}")

print(f"\n📋 GitHub Secrets 설정 정보:")
print(f"   TELEGRAM_BOT_TOKEN: {bot_token}")
print(f"   TELEGRAM_CHAT_ID: [위에서 확인된 Chat ID]")
