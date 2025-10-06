# KR: 실제 데이터 수집 및 처리 검증 테스트
# EN: Real data collection and processing validation test

import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timedelta
import time

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_data_collection():
    """1. 데이터 수집 검증"""
    print("=== 1. 데이터 수집 검증 ===")
    
    validation_results = {
        'ncm_selenium': False,
        'worldtides': False,
        'open_meteo': False,
        'stormglass': False
    }
    
    # 1-1. NCM Selenium 데이터 수집 검증
    print("\n1-1. NCM Selenium 데이터 수집 검증")
    try:
        from ncm_web.ncm_selenium_ingestor import NCMSeleniumIngestor
        
        ingestor = NCMSeleniumIngestor(headless=True)
        ncm_data = ingestor.create_marine_timeseries("AGI", 24)
        
        print(f"   소스: {ncm_data.source}")
        print(f"   데이터 포인트 수: {len(ncm_data.data_points)}")
        print(f"   신뢰도: {ncm_data.confidence}")
        print(f"   수집 시간: {ncm_data.ingested_at}")
        
        if ncm_data.data_points:
            sample = ncm_data.data_points[0]
            print(f"   샘플 데이터:")
            print(f"     - 시간: {sample.timestamp}")
            print(f"     - 풍속: {sample.wind_speed} m/s")
            print(f"     - 파고: {sample.wave_height} m")
            print(f"     - 시정: {sample.visibility} km")
            
            # 데이터 무결성 검사
            has_real_data = (
                sample.wind_speed > 0 or 
                sample.wave_height > 0 or 
                (sample.visibility and sample.visibility > 0)
            )
            
            if has_real_data:
                print("   ✅ 실제 데이터 감지됨")
                validation_results['ncm_selenium'] = True
            else:
                print("   ⚠️  폴백 데이터만 있음 (실제 데이터 없음)")
        
    except Exception as e:
        print(f"   ❌ NCM 수집 실패: {e}")
    
    # 1-2. WorldTides 데이터 수집 검증
    print("\n1-2. WorldTides 데이터 수집 검증")
    try:
        from src.marine_ops.connectors.worldtides import create_marine_timeseries_from_worldtides
        
        # UAE 좌표로 테스트
        lat, lon = 25.2111, 54.1578  # AGI 근처
        api_key = ""  # API 키 없이 테스트
        
        worldtides_data = create_marine_timeseries_from_worldtides(
            lat, lon, api_key, "AGI", 24
        )
        
        print(f"   소스: {worldtides_data.source}")
        print(f"   데이터 포인트 수: {len(worldtides_data.data_points)}")
        print(f"   신뢰도: {worldtides_data.confidence}")
        
        if worldtides_data.data_points:
            sample = worldtides_data.data_points[0]
            print(f"   샘플 데이터:")
            print(f"     - 시간: {sample.timestamp}")
            print(f"     - 조석 높이: {getattr(sample, 'tide_height', 'N/A')}")
            
            # API 키 없이는 폴백 데이터만 생성됨
            if worldtides_data.confidence >= 0.7:
                print("   ✅ 실제 API 데이터")
                validation_results['worldtides'] = True
            else:
                print("   ⚠️  폴백 데이터 (API 키 필요)")
        
    except Exception as e:
        print(f"   ❌ WorldTides 수집 실패: {e}")
    
    # 1-3. Open-Meteo 데이터 수집 검증
    print("\n1-3. Open-Meteo 데이터 수집 검증")
    try:
        from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
        
        connector = OpenMeteoConnector()
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=24)
        lat, lon = 25.2111, 54.1578
        
        open_meteo_data = connector.get_marine_weather(
            lat, lon, start_time, end_time, "AGI"
        )
        
        print(f"   소스: {open_meteo_data.source}")
        print(f"   데이터 포인트 수: {len(open_meteo_data.data_points)}")
        print(f"   신뢰도: {open_meteo_data.confidence}")
        
        if open_meteo_data.data_points:
            sample = open_meteo_data.data_points[0]
            print(f"   샘플 데이터:")
            print(f"     - 시간: {sample.timestamp}")
            print(f"     - 풍속: {sample.wind_speed} m/s")
            print(f"     - 파고: {sample.wave_height} m")
            print(f"     - 스웰: {sample.swell_wave_height} m")
            print(f"     - 해수면 온도: {sample.sea_surface_temperature}°C")
            
            # 실제 API 데이터 확인
            if (sample.wind_speed > 0 or sample.wave_height > 0 or 
                sample.swell_wave_height is not None):
                print("   ✅ 실제 API 데이터 수집됨")
                validation_results['open_meteo'] = True
            else:
                print("   ⚠️  데이터 없음")
        
    except Exception as e:
        print(f"   ❌ Open-Meteo 수집 실패: {e}")
    
    # 1-4. Stormglass 데이터 수집 검증 (API 키 필요)
    print("\n1-4. Stormglass 데이터 수집 검증")
    try:
        from src.marine_ops.connectors.stormglass import StormglassConnector
        
        connector = StormglassConnector()
        lat, lon = 25.2111, 54.1578
        
        stormglass_data = connector.get_marine_weather(
            lat, lon, datetime.now(), datetime.now() + timedelta(hours=24), "AGI"
        )
        
        print(f"   소스: {stormglass_data.source}")
        print(f"   데이터 포인트 수: {len(stormglass_data.data_points)}")
        print(f"   신뢰도: {stormglass_data.confidence}")
        
        if stormglass_data.data_points:
            sample = stormglass_data.data_points[0]
            print(f"   샘플 데이터:")
            print(f"     - 시간: {sample.timestamp}")
            print(f"     - 풍속: {sample.wind_speed} m/s")
            print(f"     - 파고: {sample.wave_height} m")
            
            if sample.wind_speed > 0 or sample.wave_height > 0:
                print("   ✅ 실제 API 데이터 수집됨")
                validation_results['stormglass'] = True
            else:
                print("   ⚠️  데이터 없음")
        
    except Exception as e:
        print(f"   ❌ Stormglass 수집 실패: {e}")
    
    return validation_results

def validate_data_processing():
    """2. 데이터 처리 검증"""
    print("\n=== 2. 데이터 처리 검증 ===")
    
    processing_results = {
        'unit_conversion': False,
        'eri_calculation': False,
        'vector_storage': False,
        'data_integrity': False
    }
    
    # 2-1. 단위 변환 검증
    print("\n2-1. 단위 변환 검증")
    try:
        from src.marine_ops.core.units import normalize_to_si
        
        # 테스트 데이터
        test_data = {
            'wind_speed': 20,  # kt
            'wind_unit': 'kt',
            'wave_height': 3.28,  # ft
            'wave_unit': 'ft'
        }
        
        normalized = normalize_to_si(test_data, 'test')
        
        print(f"   원본 풍속: {test_data['wind_speed']} kt")
        print(f"   변환된 풍속: {normalized['wind_speed']:.2f} m/s")
        print(f"   원본 파고: {test_data['wave_height']} ft")
        print(f"   변환된 파고: {normalized['wave_height']:.2f} m")
        
        # 변환 정확도 검증
        expected_wind = 20 * 0.514444  # kt to m/s
        expected_wave = 3.28 * 0.3048  # ft to m
        
        if (abs(normalized['wind_speed'] - expected_wind) < 0.01 and
            abs(normalized['wave_height'] - expected_wave) < 0.01):
            print("   ✅ 단위 변환 정확함")
            processing_results['unit_conversion'] = True
        else:
            print("   ❌ 단위 변환 오류")
        
    except Exception as e:
        print(f"   ❌ 단위 변환 검증 실패: {e}")
    
    # 2-2. ERI 계산 검증
    print("\n2-2. ERI 계산 검증")
    try:
        from src.marine_ops.eri.compute import ERICalculator
        from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries
        
        # 테스트 데이터 생성
        test_data_points = []
        for i in range(24):
            timestamp = (datetime.now() + timedelta(hours=i)).isoformat()
            data_point = MarineDataPoint(
                timestamp=timestamp,
                wind_speed=10 + i * 0.5,  # 10-22 m/s
                wind_direction=270 + i * 5,
                wave_height=1.0 + i * 0.1,  # 1.0-3.4 m
                visibility=10.0,
                fog_probability=0.1
            )
            test_data_points.append(data_point)
        
        test_timeseries = MarineTimeseries(
            source="test",
            location="AGI",
            data_points=test_data_points,
            ingested_at=datetime.now().isoformat(),
            confidence=1.0
        )
        
        calculator = ERICalculator()
        eri_points = calculator.compute_eri_timeseries(test_timeseries)
        
        print(f"   ERI 계산 포인트: {len(eri_points)}개")
        
        if eri_points:
            sample_eri = eri_points[0]
            print(f"   샘플 ERI:")
            print(f"     - 전체 ERI: {sample_eri.eri_value:.2f}")
            print(f"     - 풍속 기여도: {sample_eri.wind_contribution:.2f}")
            print(f"     - 파고 기여도: {sample_eri.wave_contribution:.2f}")
            
            # ERI 값 범위 검증
            if 0 <= sample_eri.eri_value <= 1.0:
                print("   ✅ ERI 계산 정상")
                processing_results['eri_calculation'] = True
            else:
                print("   ❌ ERI 값 범위 오류")
        
    except Exception as e:
        print(f"   ❌ ERI 계산 검증 실패: {e}")
    
    # 2-3. 벡터 저장 검증
    print("\n2-3. 벡터 저장 검증")
    try:
        from src.marine_ops.core.vector_db import MarineVectorDB
        from src.marine_ops.core.schema import MarineDataPoint, MarineTimeseries
        
        # 테스트 데이터 생성
        test_data_points = []
        for i in range(5):
            timestamp = (datetime.now() + timedelta(hours=i)).isoformat()
            data_point = MarineDataPoint(
                timestamp=timestamp,
                wind_speed=8.0 + i,
                wind_direction=270.0,
                wave_height=1.0 + i * 0.2
            )
            test_data_points.append(data_point)
        
        test_timeseries = MarineTimeseries(
            source="validation_test",
            location="AGI",
            data_points=test_data_points,
            ingested_at=datetime.now().isoformat(),
            confidence=0.9
        )
        
        vector_db = MarineVectorDB("validation_test.db")
        stored_count = vector_db.store_timeseries(test_timeseries)
        
        print(f"   저장된 데이터 포인트: {stored_count}개")
        
        if stored_count == len(test_data_points):
            print("   ✅ 벡터 저장 정상")
            processing_results['vector_storage'] = True
        else:
            print("   ❌ 벡터 저장 개수 불일치")
        
    except Exception as e:
        print(f"   ❌ 벡터 저장 검증 실패: {e}")
    
    # 2-4. 데이터 무결성 검증
    print("\n2-4. 데이터 무결성 검증")
    try:
        # 생성된 데이터 파일들 확인
        data_files = []
        
        # CSV 파일 확인
        csv_files = list(Path("data").glob("*.csv"))
        data_files.extend([f"CSV: {f.name}" for f in csv_files])
        
        # JSON 파일 확인
        json_files = list(Path("out").glob("*.json"))
        data_files.extend([f"JSON: {f.name}" for f in json_files])
        
        # DB 파일 확인
        db_files = list(Path(".").glob("*.db"))
        data_files.extend([f"DB: {f.name}" for f in db_files])
        
        print(f"   발견된 데이터 파일:")
        for file_info in data_files:
            print(f"     - {file_info}")
        
        if len(data_files) > 0:
            print("   ✅ 데이터 파일 존재")
            processing_results['data_integrity'] = True
        else:
            print("   ⚠️  데이터 파일 없음")
        
    except Exception as e:
        print(f"   ❌ 데이터 무결성 검증 실패: {e}")
    
    return processing_results

def validate_system_integration():
    """3. 시스템 통합 테스트"""
    print("\n=== 3. 시스템 통합 테스트 ===")
    
    integration_results = {
        'end_to_end': False,
        'query_engine': False,
        'error_handling': False,
        'performance': False
    }
    
    # 3-1. End-to-End 테스트
    print("\n3-1. End-to-End 테스트")
    try:
        start_time = time.time()
        
        # 전체 파이프라인 실행
        from scripts.demo_integrated import main as demo_main
        
        print("   데모 파이프라인 실행 중...")
        demo_main()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"   실행 시간: {execution_time:.2f}초")
        
        if execution_time < 60:  # 1분 이내
            print("   ✅ End-to-End 테스트 성공")
            integration_results['end_to_end'] = True
        else:
            print("   ⚠️  실행 시간 초과")
        
    except Exception as e:
        print(f"   ❌ End-to-End 테스트 실패: {e}")
    
    # 3-2. 질의 엔진 테스트
    print("\n3-2. 질의 엔진 테스트")
    try:
        from query_vec import MarineQueryEngine
        
        query_engine = MarineQueryEngine("validation_test.db")
        
        test_queries = [
            "AGI marine conditions",
            "wind speed analysis",
            "wave height trends"
        ]
        
        all_queries_successful = True
        for query in test_queries:
            results = query_engine.query_marine_conditions(query, top_k=3)
            print(f"   '{query}': {results['total_results']}개 결과")
            
            if results['total_results'] == 0:
                all_queries_successful = False
        
        if all_queries_successful:
            print("   ✅ 질의 엔진 정상")
            integration_results['query_engine'] = True
        else:
            print("   ⚠️  일부 질의 결과 없음")
        
    except Exception as e:
        print(f"   ❌ 질의 엔진 테스트 실패: {e}")
    
    # 3-3. 에러 처리 테스트
    print("\n3-3. 에러 처리 테스트")
    try:
        # 잘못된 API 키로 테스트
        from src.marine_ops.connectors.stormglass import StormglassConnector
        
        connector = StormglassConnector()
        # 잘못된 API 키 설정
        connector.api_key = "invalid_key"
        
        try:
            result = connector.get_marine_weather(
                25.2111, 54.1578, 
                datetime.now(), 
                datetime.now() + timedelta(hours=24), 
                "AGI"
            )
            # 에러가 발생해야 정상
            print("   ❌ 에러 처리 실패 (에러가 발생하지 않음)")
        except Exception:
            print("   ✅ 에러 처리 정상")
            integration_results['error_handling'] = True
        
    except Exception as e:
        print(f"   ❌ 에러 처리 테스트 실패: {e}")
    
    # 3-4. 성능 테스트
    print("\n3-4. 성능 테스트")
    try:
        # 벡터 검색 성능 테스트
        from query_vec import MarineQueryEngine
        
        query_engine = MarineQueryEngine("validation_test.db")
        
        start_time = time.time()
        for i in range(10):
            results = query_engine.query_marine_conditions("test query", top_k=5)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        
        print(f"   평균 검색 시간: {avg_time:.3f}초")
        
        if avg_time < 1.0:  # 1초 이내
            print("   ✅ 성능 테스트 통과")
            integration_results['performance'] = True
        else:
            print("   ⚠️  성능 저하 감지")
        
    except Exception as e:
        print(f"   ❌ 성능 테스트 실패: {e}")
    
    return integration_results

def generate_validation_report(collection_results, processing_results, integration_results):
    """검증 결과 보고서 생성"""
    print("\n" + "="*60)
    print("📊 데이터 검증 결과 보고서")
    print("="*60)
    
    # 데이터 수집 결과
    print("\n🔍 데이터 수집 검증:")
    for source, result in collection_results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {source}: {status}")
    
    # 데이터 처리 결과
    print("\n⚙️ 데이터 처리 검증:")
    for process, result in processing_results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {process}: {status}")
    
    # 시스템 통합 결과
    print("\n🔗 시스템 통합 검증:")
    for integration, result in integration_results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {integration}: {status}")
    
    # 전체 점수 계산
    total_tests = len(collection_results) + len(processing_results) + len(integration_results)
    passed_tests = (
        sum(collection_results.values()) + 
        sum(processing_results.values()) + 
        sum(integration_results.values())
    )
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📈 전체 검증 결과:")
    print(f"   통과: {passed_tests}/{total_tests}")
    print(f"   성공률: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("   🎉 시스템 검증 통과!")
    elif success_rate >= 60:
        print("   ⚠️ 시스템 부분 검증")
    else:
        print("   ❌ 시스템 검증 실패")
    
    # 실제 데이터 vs 폴백 데이터 분석
    print(f"\n📊 실제 데이터 분석:")
    real_data_sources = []
    fallback_data_sources = []
    
    if collection_results.get('ncm_selenium'):
        real_data_sources.append("NCM Selenium")
    else:
        fallback_data_sources.append("NCM Selenium")
    
    if collection_results.get('open_meteo'):
        real_data_sources.append("Open-Meteo")
    else:
        fallback_data_sources.append("Open-Meteo")
    
    print(f"   실제 데이터 소스: {', '.join(real_data_sources) if real_data_sources else '없음'}")
    print(f"   폴백 데이터 소스: {', '.join(fallback_data_sources) if fallback_data_sources else '없음'}")
    
    return success_rate

def main():
    """메인 검증 함수"""
    print("🚢 통합 해양 날씨 파이프라인 데이터 검증 시작")
    print("="*60)
    
    # 1. 데이터 수집 검증
    collection_results = validate_data_collection()
    
    # 2. 데이터 처리 검증
    processing_results = validate_data_processing()
    
    # 3. 시스템 통합 테스트
    integration_results = validate_system_integration()
    
    # 4. 검증 결과 보고서 생성
    success_rate = generate_validation_report(
        collection_results, 
        processing_results, 
        integration_results
    )
    
    return success_rate >= 60  # 60% 이상 성공 시 통과

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
