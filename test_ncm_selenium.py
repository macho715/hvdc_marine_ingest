# KR: NCM Selenium 수집기 테스트
# EN: NCM Selenium ingestor test

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ncm_web.ncm_selenium_ingestor import NCMSeleniumIngestor

def test_ncm_selenium():
    """NCM Selenium 수집기 테스트"""
    
    print("=== NCM Selenium 수집기 테스트 ===")
    
    try:
        # Selenium 수집기 초기화 (헤드리스 모드)
        ingestor = NCMSeleniumIngestor(headless=True)
        
        # 실제 페이지에서 데이터 수집
        print("\n1. NCM 페이지에서 Selenium으로 데이터 수집 중...")
        timeseries = ingestor.create_marine_timeseries("AGI", 24)
        
        print(f"\n2. 수집 결과:")
        print(f"   소스: {timeseries.source}")
        print(f"   지역: {timeseries.location}")
        print(f"   데이터 포인트 수: {len(timeseries.data_points)}")
        print(f"   신뢰도: {timeseries.confidence}")
        print(f"   수집 시간: {timeseries.ingested_at}")
        
        if timeseries.data_points:
            print(f"\n3. 샘플 데이터:")
            for i, dp in enumerate(timeseries.data_points[:3]):  # 처음 3개만
                print(f"   [{i+1}] {dp.timestamp}")
                print(f"       풍속: {dp.wind_speed} m/s")
                print(f"       풍향: {dp.wind_direction}°")
                print(f"       파고: {dp.wave_height} m")
                if dp.visibility:
                    print(f"       시정: {dp.visibility} km")
                if dp.temperature:
                    print(f"       온도: {dp.temperature}°C")
                if dp.sea_state:
                    print(f"       바다상태: {dp.sea_state}")
                print()
        
        # CSV 저장
        if timeseries.data_points:
            import pandas as pd
            from datetime import datetime
            
            data_list = []
            for dp in timeseries.data_points:
                data_list.append({
                    'timestamp': dp.timestamp,
                    'wind_speed': dp.wind_speed,
                    'wind_direction': dp.wind_direction,
                    'wave_height': dp.wave_height,
                    'visibility': dp.visibility,
                    'temperature': dp.temperature,
                    'sea_state': dp.sea_state
                })
            
            df = pd.DataFrame(data_list)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            csv_path = f"data/ncm_selenium_{timestamp}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"4. CSV 저장됨: {csv_path}")
        
        # 벡터 DB 저장
        print(f"\n5. 벡터 DB에 저장 중...")
        from src.marine_ops.core.vector_db import MarineVectorDB
        vector_db = MarineVectorDB("test_ncm_selenium.db")
        stored_count = vector_db.store_timeseries(timeseries)
        print(f"   저장된 데이터 포인트: {stored_count}개")
        
        # 검색 테스트
        print(f"\n6. 검색 테스트...")
        from query_vec import MarineQueryEngine
        query_engine = MarineQueryEngine("test_ncm_selenium.db")
        
        test_queries = [
            "AGI marine observations",
            "wind speed conditions",
            "wave height data"
        ]
        
        for query in test_queries:
            results = query_engine.query_marine_conditions(query, top_k=3)
            print(f"   '{query}': {results['total_results']}개 결과")
        
        print(f"\n=== 테스트 완료 ===")
        return True
        
    except Exception as e:
        print(f"\n=== 테스트 실패 ===")
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ncm_selenium()
    sys.exit(0 if success else 1)
