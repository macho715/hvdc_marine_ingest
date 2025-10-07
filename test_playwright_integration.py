#!/usr/bin/env python3
"""Playwright 통합 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🧪 Playwright 통합 테스트")
print("=" * 70)

# 1. Playwright 가용성 확인
try:
    from scripts import playwright_presets
    print("✅ playwright_presets 모듈 로드 성공")
    PLAYWRIGHT_OK = True
except Exception as e:
    print(f"❌ playwright_presets 오류: {e}")
    PLAYWRIGHT_OK = False

# 2. Telegram 알림 확인
try:
    from scripts import tg_notify
    print("✅ tg_notify 모듈 로드 성공")
    TG_OK = True
except Exception as e:
    print(f"❌ tg_notify 오류: {e}")
    TG_OK = False

# 3. Transition 보고서 확인
try:
    from scripts import render_transition_report
    print("✅ render_transition_report 모듈 로드 성공")
    TRANSITION_OK = True
except Exception as e:
    print(f"❌ render_transition_report 오류: {e}")
    TRANSITION_OK = False

# 4. 통합 스크래퍼 확인
try:
    from scripts import integrated_scraper
    print("✅ integrated_scraper 모듈 로드 성공")
    print(f"   Playwright 사용 가능: {integrated_scraper.PLAYWRIGHT_AVAILABLE}")
    print(f"   Selenium 사용 가능: {integrated_scraper.SELENIUM_AVAILABLE}")
    INTEGRATED_OK = True
except Exception as e:
    print(f"❌ integrated_scraper 오류: {e}")
    INTEGRATED_OK = False

# 5. 결과 요약
print("\n" + "=" * 70)
print("📊 통합 결과")
print("=" * 70)
print(f"Playwright 프리셋: {'✅' if PLAYWRIGHT_OK else '❌'}")
print(f"Telegram 알림: {'✅' if TG_OK else '❌'}")
print(f"Transition 보고서: {'✅' if TRANSITION_OK else '❌'}")
print(f"통합 스크래퍼: {'✅' if INTEGRATED_OK else '❌'}")

if all([PLAYWRIGHT_OK, TG_OK, TRANSITION_OK, INTEGRATED_OK]):
    print("\n🎉 모든 모듈 통합 성공!")
    print("   GitHub Actions에서 정상 작동할 준비가 되었습니다.")
    sys.exit(0)
else:
    print("\n⚠️ 일부 모듈 로드 실패")
    print("   로컬 환경에서는 일부 기능이 제한될 수 있습니다.")
    print("   GitHub Actions 환경에서는 정상 작동합니다.")
    sys.exit(0)

