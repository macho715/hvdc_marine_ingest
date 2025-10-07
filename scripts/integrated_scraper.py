#!/usr/bin/env python3
"""통합 해양 데이터 스크래퍼 - Selenium + Playwright"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Playwright 스크래퍼 시도
try:
    from playwright_presets import run_scrape, RunOptions
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    PLAYWRIGHT_AVAILABLE = False
    print(f"⚠️ Playwright import error: {e}")

# Selenium 스크래퍼 폴백
try:
    from ncm_web.ncm_selenium_ingestor import NCMSeleniumIngestor
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"⚠️ Selenium import error: {e}")


def scrape_ncm_data(location: str = "AGI", use_playwright: bool = True) -> Optional[dict]:
    """NCM AlBahar 데이터 스크래핑 (Playwright 우선, Selenium 폴백)"""
    
    print(f"\n🌊 NCM AlBahar 데이터 수집 시작 ({location})")
    
    # 1. Playwright 시도 (우선순위 높음)
    if use_playwright and PLAYWRIGHT_AVAILABLE:
        try:
            print("  ✅ Playwright 스크래퍼 사용")
            opts = RunOptions(
                url="https://albahar.ncm.gov.ae/marine-observations",
                site=location,
                headless=True,
                timeout=25000,
                network_idle=True
            )
            result = run_scrape(opts)
            
            if result and result.get('success'):
                print(f"  ✅ Playwright 스크래핑 성공: {len(result.get('data', []))} 데이터")
                return result
            else:
                print("  ⚠️ Playwright 스크래핑 실패, Selenium으로 전환")
                
        except Exception as e:
            print(f"  ⚠️ Playwright 오류: {e}, Selenium으로 전환")
    
    # 2. Selenium 폴백
    if SELENIUM_AVAILABLE:
        try:
            print("  ✅ Selenium 스크래퍼 사용 (폴백)")
            ingestor = NCMSeleniumIngestor(headless=True)
            timeseries = ingestor.create_marine_timeseries(location=location, forecast_hours=24)
            
            print(f"  ✅ Selenium 스크래핑 성공: {len(timeseries.data_points)} 데이터")
            return {
                'success': True,
                'source': 'selenium',
                'timeseries': timeseries,
                'data_points': len(timeseries.data_points)
            }
            
        except Exception as e:
            print(f"  ❌ Selenium 오류: {e}")
    
    # 3. 모든 방법 실패
    print("  ❌ 모든 스크래핑 방법 실패, 폴백 데이터 생성")
    return None


def main():
    """테스트 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="통합 NCM 스크래퍼 테스트")
    parser.add_argument("--location", default="AGI", help="위치 (AGI/DAS)")
    parser.add_argument("--playwright", action="store_true", help="Playwright 우선 사용")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 통합 NCM 스크래퍼 테스트")
    print("=" * 70)
    print(f"Playwright 가능: {PLAYWRIGHT_AVAILABLE}")
    print(f"Selenium 가능: {SELENIUM_AVAILABLE}")
    
    result = scrape_ncm_data(args.location, use_playwright=args.playwright)
    
    if result:
        print("\n✅ 스크래핑 성공!")
        print(f"  소스: {result.get('source', 'unknown')}")
        print(f"  데이터 포인트: {result.get('data_points', 0)}")
    else:
        print("\n❌ 스크래핑 실패")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

