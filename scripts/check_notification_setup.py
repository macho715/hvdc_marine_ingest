#!/usr/bin/env python3
"""
GitHub Actions 알림 시스템 설정 진단 스크립트
HVDC Marine Weather System
"""

import os
import sys
from pathlib import Path

def check_github_secrets():
    """GitHub Secrets 설정 상태 확인"""
    print("🔍 GitHub Secrets 설정 상태 확인")
    print("=" * 50)
    
    required_secrets = {
        'TELEGRAM_BOT_TOKEN': 'Telegram 봇 토큰',
        'TELEGRAM_CHAT_ID': 'Telegram 채팅 ID',
        'MAIL_USERNAME': 'Gmail 사용자명',
        'MAIL_PASSWORD': 'Gmail 앱 비밀번호',
        'MAIL_TO': '수신자 이메일 주소',
        'STORMGLASS_API_KEY': 'Stormglass API 키',
        'WORLDTIDES_API_KEY': 'WorldTides API 키'
    }
    
    print("📋 필수 GitHub Secrets 목록:")
    for secret, description in required_secrets.items():
        # GitHub Actions에서는 환경변수로 제공됨
        status = "✅ 설정됨" if os.getenv(secret) else "❌ 없음"
        print(f"  {secret}: {status} - {description}")
    
    print("\n🔧 GitHub Secrets 설정 방법:")
    print("1. GitHub 리포지토리 → Settings → Secrets and variables → Actions")
    print("2. 'New repository secret' 클릭")
    print("3. 각 Secret 추가:")
    
    for secret, description in required_secrets.items():
        print(f"   - Name: {secret}")
        print(f"   - Value: [실제 값 입력]")
        print(f"   - 설명: {description}")
        print()

def check_workflow_file():
    """워크플로우 파일 확인"""
    print("📄 GitHub Actions 워크플로우 파일 확인")
    print("=" * 50)
    
    workflow_file = Path(".github/workflows/marine-hourly.yml")
    if workflow_file.exists():
        print("✅ marine-hourly.yml 파일 존재")
        
        content = workflow_file.read_text(encoding='utf-8')
        
        # 알림 관련 설정 확인
        if "NOTIFY_TELEGRAM: '1'" in content:
            print("✅ Telegram 알림 활성화됨")
        else:
            print("❌ Telegram 알림 비활성화됨")
            
        if "NOTIFY_EMAIL: '1'" in content:
            print("✅ Email 알림 활성화됨")
        else:
            print("❌ Email 알림 비활성화됨")
            
        # 알림 단계 확인
        if "Send Telegram notification" in content:
            print("✅ Telegram 알림 단계 존재")
        else:
            print("❌ Telegram 알림 단계 없음")
            
        if "Send Email notification" in content:
            print("✅ Email 알림 단계 존재")
        else:
            print("❌ Email 알림 단계 없음")
    else:
        print("❌ marine-hourly.yml 파일이 없습니다")

def check_notification_test():
    """알림 테스트 파일 생성"""
    print("\n🧪 알림 테스트 파일 생성")
    print("=" * 50)
    
    # 테스트용 summary.txt 생성
    test_content = """🌊 HVDC Marine Weather Report - 테스트

📊 데이터 수집 현황 (4개 소스):
✅ Stormglass: API 기반 해양 날씨 데이터
✅ Open-Meteo: API 기반 기상 예보
✅ WorldTides: API 기반 조석 데이터  
✅ NCM Selenium: 웹 스크래핑 해양 관측 데이터

🚢 운항 가능성 예측:
✅ GO: 28개 예측
⚠️ CONDITIONAL: 0개
❌ NO-GO: 0개

📍 위치: AGI (Al Ghallan Island)
⏰ 생성 시간: $(date '+%Y-%m-%d %H:%M:%S')

---
HVDC Project - Samsung C&T Logistics
"""
    
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    
    summary_file = out_dir / "summary.txt"
    summary_file.write_text(test_content, encoding='utf-8')
    print(f"✅ 테스트 파일 생성: {summary_file}")
    print(f"📄 파일 크기: {summary_file.stat().st_size} bytes")

def generate_setup_guide():
    """설정 가이드 생성"""
    print("\n📖 GitHub Secrets 설정 가이드")
    print("=" * 50)
    
    guide_content = """# GitHub Secrets 설정 가이드

## 1. Telegram Bot 설정

### 1.1 Bot 생성
1. Telegram에서 @BotFather와 대화 시작
2. `/newbot` 명령어 입력
3. 봇 이름과 사용자명 설정
4. Bot Token 복사

### 1.2 Chat ID 확인
1. 봇과 대화 시작
2. 브라우저에서 `https://api.telegram.org/bot[BOT_TOKEN]/getUpdates` 접속
3. `chat.id` 값 복사

### 1.3 GitHub Secrets 설정
- `TELEGRAM_BOT_TOKEN`: Bot Token
- `TELEGRAM_CHAT_ID`: Chat ID (숫자)

## 2. Gmail 설정

### 2.1 앱 비밀번호 생성
1. Google 계정 → 보안 → 2단계 인증 활성화
2. 앱 비밀번호 생성 (16자리)
3. Gmail 사용자명과 앱 비밀번호 기록

### 2.2 GitHub Secrets 설정
- `MAIL_USERNAME`: Gmail 주소 (예: user@gmail.com)
- `MAIL_PASSWORD`: 앱 비밀번호 (16자리)
- `MAIL_TO`: 수신자 이메일 주소

## 3. API 키 설정
- `STORMGLASS_API_KEY`: Stormglass API 키
- `WORLDTIDES_API_KEY`: WorldTides API 키

## 4. 설정 확인
1. GitHub Actions 탭에서 워크플로우 실행
2. 로그에서 알림 상태 확인
3. Telegram과 Email 수신 확인
"""
    
    guide_file = Path("NOTIFICATION_SETUP_GUIDE.md")
    guide_file.write_text(guide_content, encoding='utf-8')
    print(f"✅ 설정 가이드 생성: {guide_file}")

def main():
    """메인 함수"""
    print("🚢 HVDC Marine Weather - 알림 시스템 진단")
    print("=" * 60)
    
    check_github_secrets()
    check_workflow_file()
    check_notification_test()
    generate_setup_guide()
    
    print("\n🎯 다음 단계:")
    print("1. GitHub Secrets 설정 완료")
    print("2. GitHub Actions 워크플로우 수동 실행")
    print("3. 로그에서 알림 상태 확인")
    print("4. Telegram과 Email 수신 테스트")

if __name__ == "__main__":
    main()
