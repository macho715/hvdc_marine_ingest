# KR: 벡터 파이프라인 통합 테스트
# EN: Vector pipeline integration test

import sys
import json
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
from src.marine_ops.core.vector_db import MarineVectorDB, save_timeseries_to_vector_db
from scripts.demo_integrated import create_demo_data
from query_vec import MarineQueryEngine

def test_vector_pipeline():
    """벡터 파이프라인 통합 테스트"""
    
    print("=== 벡터 파이프라인 통합 테스트 ===")
    
    try:
        # 1. 데모 데이터 생성
        print("\n1. 데모 데이터 생성...")
        timeseries_list = create_demo_data()
        print(f"   생성된 시계열: {len(timeseries_list)}개")
        
        # 2. 벡터 DB에 저장
        print("\n2. 벡터 DB에 저장...")
        vector_db = MarineVectorDB("test_marine_vec.db")
        
        stored_results = {}
        for timeseries in timeseries_list:
            stored_count = vector_db.store_timeseries(timeseries)
            key = f"{timeseries.source}_{timeseries.location}"
            stored_results[key] = stored_count
            print(f"   {key}: {stored_count}개 저장")
        
        # 3. DB 통계 확인
        print("\n3. DB 통계 확인...")
        stats = vector_db.get_stats()
        print(f"   총 레코드: {stats['total_records']}")
        print(f"   벡터 임베딩: {stats['vector_embeddings']}")
        print(f"   소스별 통계: {stats['source_stats']}")
        print(f"   지역별 통계: {stats['location_stats']}")
        
        # 4. 벡터 검색 테스트
        print("\n4. 벡터 검색 테스트...")
        query_engine = MarineQueryEngine("test_marine_vec.db")
        
        test_queries = [
            "AGI high tide RORO window",
            "high wind speed conditions",
            "wave height rough seas",
            "operational window good conditions"
        ]
        
        for query in test_queries:
            print(f"\n   쿼리: '{query}'")
            results = query_engine.query_marine_conditions(query, top_k=3)
            print(f"   결과: {results['total_results']}개")
            if results['analysis']:
                analysis = results['analysis']
                if 'wind_summary' in analysis:
                    wind = analysis['wind_summary']
                    print(f"   풍속: {wind['min']:.1f}-{wind['max']:.1f} m/s (평균 {wind['avg']:.1f})")
                if 'wave_summary' in analysis:
                    wave = analysis['wave_summary']
                    print(f"   파고: {wave['min']:.1f}-{wave['max']:.1f} m (평균 {wave['avg']:.1f})")
        
        # 5. 운항 윈도우 분석 테스트
        print("\n5. 운항 윈도우 분석 테스트...")
        start_time = datetime.now().isoformat()
        end_time = (datetime.now().replace(hour=23, minute=59)).isoformat()
        
        for location in ["AGI", "DAS"]:
            print(f"\n   {location} 운항 윈도우:")
            result = query_engine.query_operational_window(location, start_time, end_time)
            if result['status'] == 'success':
                analysis = result['operational_analysis']
                print(f"   GO: {analysis['go_periods']}개")
                print(f"   CONDITIONAL: {analysis['conditional_periods']}개")
                print(f"   NO-GO: {analysis['no_go_periods']}개")
                print(f"   운항 가능률: {analysis['operational_percentage']:.1f}%")
                print(f"   권고사항: {analysis['recommendation']}")
        
        # 6. 최근 데이터 요약 테스트
        print("\n6. 최근 데이터 요약 테스트...")
        summary = query_engine.get_recent_summary(hours=24)
        if summary['status'] == 'success':
            print(f"   최근 24시간 데이터: {summary['total_records']}개")
            if 'wind_summary' in summary['summary']:
                wind = summary['summary']['wind_summary']
                print(f"   풍속 범위: {wind['min']:.1f}-{wind['max']:.1f} m/s")
        
        print("\n=== 테스트 완료 ===")
        return True
        
    except Exception as e:
        print(f"\n=== 테스트 실패 ===")
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cursor_hook():
    """Cursor 훅 테스트"""
    
    print("\n=== Cursor Browser Hook 테스트 ===")
    
    try:
        # agent_hooks.py 모듈 테스트
        from agent_hooks import NCMBrowserHook
        
        hook = NCMBrowserHook()
        
        # 샘플 HTML 콘텐츠
        sample_html = """
        <html>
            <body>
                <h1>NCM Marine Forecast</h1>
                <table>
                    <tr><th>Time</th><th>Wind</th><th>Wave</th><th>Visibility</th></tr>
                    <tr><td>06:00</td><td>15 kt</td><td>1.2m</td><td>10km</td></tr>
                    <tr><td>12:00</td><td>18 kt</td><td>1.5m</td><td>8km</td></tr>
                    <tr><td>18:00</td><td>12 kt</td><td>1.0m</td><td>12km</td></tr>
                </table>
            </body>
        </html>
        """
        
        result = hook.on_page_loaded("https://www.ncm.ae/marine-forecast", sample_html)
        
        print(f"훅 실행 결과: {result['status']}")
        if result['status'] == 'success':
            print(f"CSV 저장: {result['csv_path']}")
            print(f"벡터 DB 저장: {result['vector_results']}")
            print(f"데이터 포인트: {result['data_points']}개")
        
        return True
        
    except Exception as e:
        print(f"훅 테스트 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='벡터 파이프라인 테스트')
    parser.add_argument('--vector-only', action='store_true', help='벡터 파이프라인만 테스트')
    parser.add_argument('--hook-only', action='store_true', help='Cursor 훅만 테스트')
    
    args = parser.parse_args()
    
    success = True
    
    if args.vector_only:
        success = test_vector_pipeline()
    elif args.hook_only:
        success = test_cursor_hook()
    else:
        # 전체 테스트
        success &= test_vector_pipeline()
        success &= test_cursor_hook()
    
    if success:
        print("\n🎉 모든 테스트 통과!")
    else:
        print("\n❌ 일부 테스트 실패")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
