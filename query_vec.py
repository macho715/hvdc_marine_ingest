# KR: 벡터 DB 검색 및 LLM 질의 시스템
# EN: Vector DB search and LLM query system

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.vector_db import MarineVectorDB
from src.marine_ops.core.schema import MarineDataPoint

class MarineQueryEngine:
    """해양 데이터 질의 엔진"""
    
    def __init__(self, db_path: str = "marine_vec.db"):
        self.vector_db = MarineVectorDB(db_path)
        self.query_templates = self._load_query_templates()
    
    def _load_query_templates(self) -> Dict[str, str]:
        """질의 템플릿 로드"""
        return {
            "wind_high": "high wind speed strong winds windy conditions",
            "wave_high": "high wave height rough seas large waves",
            "visibility_low": "low visibility fog mist poor visibility",
            "operational_window": "operational window good conditions safe navigation",
            "agi_conditions": "AGI Al Ghallan conditions weather forecast",
            "das_conditions": "DAS Das Island conditions weather forecast",
            "roro_operations": "RORO operations ferry service vessel movement",
            "pilotage": "pilotage berthing docking vessel operations"
        }
    
    def query_marine_conditions(self, query: str, location: str = None, top_k: int = 10) -> Dict[str, Any]:
        """해양 조건 질의"""
        print(f"[QUERY] 질의: {query}")
        if location:
            print(f"[QUERY] 지역 필터: {location}")
        
        # 벡터 검색 수행
        search_results = self.vector_db.vector_search(query, top_k, location)
        
        if not search_results:
            return {
                "status": "no_results",
                "message": "검색 결과가 없습니다",
                "query": query,
                "location": location
            }
        
        # 결과 분석 및 요약
        analysis = self._analyze_search_results(search_results, query)
        
        return {
            "status": "success",
            "query": query,
            "location": location,
            "total_results": len(search_results),
            "analysis": analysis,
            "raw_results": search_results[:5]  # 상위 5개만 반환
        }
    
    def _analyze_search_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """검색 결과 분석"""
        if not results:
            return {}
        
        # 통계 분석
        locations = {}
        sources = {}
        time_ranges = []
        wind_speeds = []
        wave_heights = []
        
        for result in results:
            data = result.get('data', {})
            location = result.get('location', 'Unknown')
            source = result.get('source', 'Unknown')
            timestamp = result.get('timestamp', '')
            
            # 지역별 통계
            locations[location] = locations.get(location, 0) + 1
            
            # 소스별 통계
            sources[source] = sources.get(source, 0) + 1
            
            # 시간 범위
            if timestamp:
                time_ranges.append(timestamp)
            
            # 해양 조건 데이터
            if 'wind_speed' in data:
                wind_speeds.append(float(data['wind_speed']))
            if 'wave_height' in data:
                wave_heights.append(float(data['wave_height']))
        
        # 분석 결과 생성
        analysis = {
            "locations": locations,
            "sources": sources,
            "time_span": {
                "earliest": min(time_ranges) if time_ranges else None,
                "latest": max(time_ranges) if time_ranges else None,
                "total_periods": len(time_ranges)
            }
        }
        
        # 해양 조건 요약
        if wind_speeds:
            analysis["wind_summary"] = {
                "min": min(wind_speeds),
                "max": max(wind_speeds),
                "avg": sum(wind_speeds) / len(wind_speeds),
                "count": len(wind_speeds)
            }
        
        if wave_heights:
            analysis["wave_summary"] = {
                "min": min(wave_heights),
                "max": max(wave_heights),
                "avg": sum(wave_heights) / len(wave_heights),
                "count": len(wave_heights)
            }
        
        # 조건별 분류
        analysis["conditions"] = self._classify_conditions(results)
        
        return analysis
    
    def _classify_conditions(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """조건별 분류"""
        conditions = {
            "good": [],
            "moderate": [],
            "poor": [],
            "extreme": []
        }
        
        for result in results:
            data = result.get('data', {})
            wind_speed = float(data.get('wind_speed', 0))
            wave_height = float(data.get('wave_height', 0))
            
            # 조건 분류 로직
            if wind_speed <= 15 and wave_height <= 1.5:
                conditions["good"].append(result)
            elif wind_speed <= 20 and wave_height <= 2.0:
                conditions["moderate"].append(result)
            elif wind_speed <= 25 and wave_height <= 2.5:
                conditions["poor"].append(result)
            else:
                conditions["extreme"].append(result)
        
        return {
            "good_count": len(conditions["good"]),
            "moderate_count": len(conditions["moderate"]),
            "poor_count": len(conditions["poor"]),
            "extreme_count": len(conditions["extreme"])
        }
    
    def query_operational_window(self, location: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """운항 윈도우 질의"""
        print(f"[QUERY] 운항 윈도우: {location} {start_time} ~ {end_time}")
        
        # 시간 범위 질의
        time_query = f"operational window {location} {start_time} {end_time}"
        results = self.vector_db.vector_search(time_query, location_filter=location)
        
        # 시간 필터링
        filtered_results = []
        for result in results:
            timestamp = result.get('timestamp', '')
            if start_time <= timestamp <= end_time:
                filtered_results.append(result)
        
        if not filtered_results:
            return {
                "status": "no_data",
                "message": f"지정된 시간 범위에 데이터가 없습니다",
                "location": location,
                "time_range": f"{start_time} ~ {end_time}"
            }
        
        # 운항 가능성 분석
        operational_analysis = self._analyze_operational_window(filtered_results)
        
        return {
            "status": "success",
            "location": location,
            "time_range": f"{start_time} ~ {end_time}",
            "total_periods": len(filtered_results),
            "operational_analysis": operational_analysis,
            "detailed_data": filtered_results
        }
    
    def _analyze_operational_window(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """운항 윈도우 분석"""
        if not results:
            return {}
        
        go_periods = []
        conditional_periods = []
        no_go_periods = []
        
        for result in results:
            data = result.get('data', {})
            wind_speed = float(data.get('wind_speed', 0))
            wave_height = float(data.get('wave_height', 0))
            
            # 운항 판정
            if wind_speed <= 15 and wave_height <= 1.5:
                go_periods.append(result)
            elif wind_speed <= 20 and wave_height <= 2.0:
                conditional_periods.append(result)
            else:
                no_go_periods.append(result)
        
        return {
            "go_periods": len(go_periods),
            "conditional_periods": len(conditional_periods),
            "no_go_periods": len(no_go_periods),
            "operational_percentage": (len(go_periods) + len(conditional_periods)) / len(results) * 100,
            "recommendation": self._get_operational_recommendation(len(go_periods), len(conditional_periods), len(no_go_periods))
        }
    
    def _get_operational_recommendation(self, go_count: int, conditional_count: int, no_go_count: int) -> str:
        """운항 권고사항 생성"""
        total = go_count + conditional_count + no_go_count
        if total == 0:
            return "데이터 부족으로 판단 불가"
        
        go_ratio = go_count / total
        conditional_ratio = conditional_count / total
        
        if go_ratio >= 0.7:
            return "운항 조건 양호 - 정상 운영 가능"
        elif go_ratio + conditional_ratio >= 0.6:
            return "부분적 운항 가능 - 조건부 운영 권고"
        else:
            return "운항 조건 불량 - 운항 중단 권고"
    
    def get_recent_summary(self, hours: int = 24, location: str = None) -> Dict[str, Any]:
        """최근 데이터 요약"""
        print(f"[QUERY] 최근 {hours}시간 요약 (지역: {location or '전체'})")
        
        recent_data = self.vector_db.get_recent_data(hours, location)
        
        if not recent_data:
            return {
                "status": "no_data",
                "message": f"최근 {hours}시간 데이터가 없습니다"
            }
        
        # 요약 분석
        summary = self._analyze_search_results(recent_data, "recent_summary")
        
        return {
            "status": "success",
            "time_range": f"최근 {hours}시간",
            "location": location or "전체",
            "total_records": len(recent_data),
            "summary": summary
        }

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='해양 데이터 벡터 검색')
    parser.add_argument('--query', default='AGI high tide RORO window', help='검색 쿼리')
    parser.add_argument('--location', help='지역 필터 (AGI, DAS)')
    parser.add_argument('--top-k', type=int, default=10, help='검색 결과 수')
    parser.add_argument('--operational', action='store_true', help='운항 윈도우 분석')
    parser.add_argument('--recent', type=int, help='최근 N시간 요약')
    
    args = parser.parse_args()
    
    # 질의 엔진 초기화
    engine = MarineQueryEngine()
    
    if args.operational and args.location:
        # 운항 윈도우 분석
        start_time = datetime.now().isoformat()
        end_time = (datetime.now() + timedelta(hours=12)).isoformat()
        
        result = engine.query_operational_window(args.location, start_time, end_time)
        print(f"\n=== 운항 윈도우 분석 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.recent:
        # 최근 데이터 요약
        result = engine.get_recent_summary(args.recent, args.location)
        print(f"\n=== 최근 {args.recent}시간 요약 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        # 일반 검색
        result = engine.query_marine_conditions(args.query, args.location, args.top_k)
        print(f"\n=== 검색 결과 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # DB 통계 출력
    stats = engine.vector_db.get_stats()
    print(f"\n=== DB 통계 ===")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
