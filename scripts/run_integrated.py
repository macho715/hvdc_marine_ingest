# KR: 통합 파이프라인 실행 스크립트
# EN: Integrated pipeline execution script

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generate_weather_report import MarineWeatherOrchestrator

def run_integrated_pipeline():
    """통합 파이프라인 실행"""
    
    print("=== 통합 해양 날씨 파이프라인 시작 ===")
    
    try:
        # 오케스트레이터 초기화
        orchestrator = MarineWeatherOrchestrator()
        
        # 보고서 생성
        report = orchestrator.generate_report(['AGI', 'DAS'])
        
        print("\n=== 파이프라인 실행 완료 ===")
        print(f"보고서 ID: {report.report_id}")
        print(f"생성 시간: {report.generated_at}")
        
        return True
        
    except Exception as e:
        print(f"\n=== 파이프라인 실행 실패 ===")
        print(f"오류: {e}")
        return False

if __name__ == "__main__":
    success = run_integrated_pipeline()
    sys.exit(0 if success else 1)
