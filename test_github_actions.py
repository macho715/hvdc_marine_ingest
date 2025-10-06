#!/usr/bin/env python3
"""
GitHub Actions 워크플로우 테스트 스크립트
로컬에서 GitHub Actions 환경을 시뮬레이션하여 테스트합니다.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_weather_job():
    """weather_job.py 스크립트 테스트"""
    print("🧪 GitHub Actions 워크플로우 테스트 시작")
    print("=" * 60)
    
    # 환경 변수 설정 (테스트용)
    os.environ['STORMGLASS_API_KEY'] = os.getenv('STORMGLASS_API_KEY', 'test_key')
    os.environ['WORLDTIDES_API_KEY'] = os.getenv('WORLDTIDES_API_KEY', 'test_key')
    
    try:
        # weather_job.py 스크립트 실행
        from scripts.weather_job import main as weather_main
        
        # 출력 디렉터리 생성
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        # 테스트 실행
        print("📊 날씨 데이터 수집 테스트...")
        sys.argv = ['weather_job.py', '--location', 'AGI', '--hours', '6', '--out', str(output_dir)]
        
        success = weather_main()
        
        if success:
            print("✅ 날씨 작업 스크립트 테스트 성공!")
            
            # 생성된 파일 확인
            output_files = list(output_dir.glob("*"))
            print(f"📁 생성된 파일: {len(output_files)}개")
            for file in output_files:
                print(f"  - {file.name}")
            
            return True
        else:
            print("❌ 날씨 작업 스크립트 테스트 실패!")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_files():
    """설정 파일 테스트"""
    print("\n📋 설정 파일 테스트...")
    
    config_files = [
        "config/locations.yml",
        "config/settings.yaml", 
        "config/eri_rules.yaml",
        "config/scrape.yaml"
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} 없음")
            all_exist = False
    
    return all_exist

def test_workflow_files():
    """워크플로우 파일 테스트"""
    print("\n🔄 워크플로우 파일 테스트...")
    
    workflow_files = [
        ".github/workflows/marine-hourly.yml",
        ".github/workflows/test.yml"
    ]
    
    all_exist = True
    for workflow_file in workflow_files:
        if Path(workflow_file).exists():
            print(f"✅ {workflow_file}")
        else:
            print(f"❌ {workflow_file} 없음")
            all_exist = False
    
    return all_exist

def test_dependencies():
    """의존성 테스트"""
    print("\n📦 의존성 테스트...")
    
    required_modules = [
        'requests',
        'httpx', 
        'bs4',  # beautifulsoup4는 bs4로 import됨
        'pandas',
        'numpy',
        'yaml',
        'selenium'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} 없음")
            missing_modules.append(module)
    
    return len(missing_modules) == 0

def generate_test_report():
    """테스트 보고서 생성"""
    print("\n📝 테스트 보고서 생성...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report = {
        'test_timestamp': timestamp,
        'test_results': {
            'config_files': test_config_files(),
            'workflow_files': test_workflow_files(), 
            'dependencies': test_dependencies(),
            'weather_job': test_weather_job()
        },
        'environment': {
            'python_version': sys.version,
            'platform': os.name,
            'current_dir': str(Path.cwd())
        }
    }
    
    # 보고서 저장
    report_file = Path(f"test_report_{timestamp}.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 테스트 보고서 저장: {report_file}")
    
    # 요약 출력
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    for test_name, result in report['test_results'].items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    all_passed = all(report['test_results'].values())
    print(f"\n🎯 전체 결과: {'✅ 모든 테스트 통과' if all_passed else '❌ 일부 테스트 실패'}")
    
    return all_passed

def main():
    """메인 함수"""
    print("🚀 GitHub Actions 워크플로우 테스트")
    print("=" * 60)
    
    success = generate_test_report()
    
    if success:
        print("\n🎉 GitHub Actions 워크플로우가 정상 작동할 준비가 되었습니다!")
        print("📋 다음 단계:")
        print("  1. GitHub 저장소에서 Actions 탭 확인")
        print("  2. 'marine-hourly' 워크플로우 수동 실행 테스트")
        print("  3. 알림 설정 확인 (Telegram/Email)")
        print("  4. 매시간 자동 실행 모니터링")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 위의 결과를 확인하고 수정하세요.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
