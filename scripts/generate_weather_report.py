# KR: 통합 해양 날씨 보고서 생성
# EN: Integrated marine weather report generation

import os
import sys
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from zoneinfo import ZoneInfo

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.schema import MarineReport
from src.marine_ops.core.cache import MarineDataCache
from src.marine_ops.connectors.stormglass import StormglassConnector, LOCATIONS as SG_LOCATIONS
from src.marine_ops.connectors.open_meteo import OpenMeteoConnector, LOCATIONS as OM_LOCATIONS
from src.marine_ops.connectors.worldtides import WorldTidesConnector, LOCATIONS as WT_LOCATIONS
from ncm_web.ncm_web_ingestor import NCMWebIngestor
from src.marine_ops.eri.compute import ERICalculator
from src.marine_ops.decision.fusion import ForecastFusion, OperationalDecisionMaker

class MarineWeatherOrchestrator:
    """해양 날씨 오케스트레이터"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.settings = self._load_settings()
        self.cache = MarineDataCache(
            cache_dir=self.settings.get('cache_dir', 'cache'),
            ttl_hours=self.settings.get('cache_ttl_hours', 3)
        )
        
        # 커넥터 초기화
        self.stormglass = StormglassConnector()
        self.open_meteo = OpenMeteoConnector()
        self.worldtides = WorldTidesConnector()
        self.ncm_ingestor = NCMWebIngestor()
        
        # ERI 및 융합 초기화
        self.eri_calculator = ERICalculator()
        self.fusion = ForecastFusion(self.settings)
        self.decision_maker = OperationalDecisionMaker(self.settings)
    
    def _load_settings(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        settings_file = self.config_dir / "settings.yaml"
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def generate_report(self, locations: List[str] = None) -> MarineReport:
        """통합 해양 보고서 생성"""
        
        if locations is None:
            locations = self.settings.get('locations', {}).keys()
        
        print(f"=== 해양 날씨 보고서 생성 시작 ===")
        print(f"대상 지역: {', '.join(locations)}")
        print(f"생성 시간: {datetime.now()}")
        
        # 1. 데이터 수집
        all_timeseries = []
        for location in locations:
            print(f"\n--- {location} 데이터 수집 ---")
            timeseries = self._collect_data_for_location(location)
            all_timeseries.extend(timeseries)
        
        # 2. ERI 계산
        print(f"\n--- ERI 계산 ---")
        all_eri_points = []
        for timeseries in all_timeseries:
            eri_points = self.eri_calculator.compute_eri_timeseries(timeseries)
            all_eri_points.extend(eri_points)
        
        # 3. 융합 및 판정
        print(f"\n--- 융합 및 판정 ---")
        all_fused_forecasts = []
        all_decisions = []
        
        for location in locations:
            # 해당 지역의 시계열 필터링
            location_timeseries = [ts for ts in all_timeseries if ts.location == location]
            
            if location_timeseries:
                # 융합 수행
                fused_forecasts = self.fusion.fuse_forecast_sources(location_timeseries, location)
                all_fused_forecasts.extend(fused_forecasts)
                
                # 판정 수행
                location_eri_points = [ep for ep in all_eri_points if ep.timestamp in [f.timestamp for f in fused_forecasts]]
                decisions = self.decision_maker.decide_and_eta(fused_forecasts, location_eri_points)
                all_decisions.extend(decisions)
        
        # 4. 보고서 생성
        report = MarineReport(
            report_id=f"MARINE_{datetime.now().strftime('%Y%m%d_%H%M')}",
            generated_at=datetime.now().isoformat(),
            locations=list(locations),
            forecast_horizon=self.settings.get('forecast_horizon_hours', 72),
            decisions=all_decisions,
            fused_forecasts=all_fused_forecasts,
            eri_timeseries=all_eri_points,
            warnings=self._generate_warnings(all_decisions),
            metadata={
                'sources_used': list(set(ts.source for ts in all_timeseries)),
                'cache_stats': self.cache.get_stats(),
                'settings_used': self.settings
            }
        )
        
        # 5. 보고서 저장
        self._save_report(report)
        
        print(f"\n=== 보고서 생성 완료 ===")
        print(f"보고서 ID: {report.report_id}")
        print(f"총 판정 수: {len(all_decisions)}")
        print(f"경고 수: {len(report.warnings)}")
        
        return report
    
    def _collect_data_for_location(self, location: str) -> List:
        """특정 지역에 대한 데이터 수집"""
        timeseries_list = []
        
        # 캐시 확인
        cache_key = f"data_{location}_{datetime.now().strftime('%Y%m%d_%H')}"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            print(f"  캐시된 데이터 사용: {location}")
            return [cached_data]
        
        # 위치 정보 가져오기
        locations_config = self.settings.get('locations', {})
        if location not in locations_config:
            print(f"  위치 정보 없음: {location}")
            return []
        
        loc_config = locations_config[location]
        lat, lon = loc_config['lat'], loc_config['lon']
        
        # 시간 범위 설정
        now = datetime.now()
        start_time = now
        end_time = now + timedelta(hours=self.settings.get('forecast_horizon_hours', 72))
        
        # 각 소스에서 데이터 수집
        sources = self.settings.get('fallback_order', ['open_meteo'])
        
        for source in sources:
            try:
                print(f"  {source}에서 데이터 수집 중...")
                
                if source == 'stormglass':
                    timeseries = self.stormglass.get_marine_weather(lat, lon, start_time, end_time, location)
                elif source == 'open_meteo':
                    timeseries = self.open_meteo.get_marine_weather(lat, lon, start_time, end_time, location)
                elif source == 'worldtides':
                    timeseries = self.worldtides.get_marine_weather(lat, lon, start_time, end_time, location)
                elif source == 'ncm_web':
                    timeseries = self.ncm_ingestor.create_marine_timeseries(location, self.settings.get('forecast_horizon_hours', 72))
                else:
                    continue
                
                timeseries_list.append(timeseries)
                print(f"  ✓ {source}: {len(timeseries.data_points)}개 데이터 포인트")
                
            except Exception as e:
                print(f"  ✗ {source} 실패: {e}")
                continue
        
        # 캐시 저장
        if timeseries_list:
            self.cache.set(cache_key, timeseries_list[0])  # 첫 번째 결과만 캐시
        
        return timeseries_list
    
    def _generate_warnings(self, decisions: List) -> List[str]:
        """경고 메시지 생성"""
        warnings = []
        
        no_go_count = sum(1 for d in decisions if d.decision == "NO-GO")
        conditional_count = sum(1 for d in decisions if d.decision == "CONDITIONAL")
        
        if no_go_count > 0:
            warnings.append(f"{no_go_count}개 시간대에서 NO-GO 판정")
        
        if conditional_count > 0:
            warnings.append(f"{conditional_count}개 시간대에서 CONDITIONAL 판정")
        
        return warnings
    
    def _save_report(self, report: MarineReport) -> None:
        """보고서 저장"""
        reports_dir = Path(self.settings.get('reports_dir', 'reports'))
        reports_dir.mkdir(exist_ok=True)
        
        # JSON 저장
        json_path = reports_dir / f"{report.report_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report.__dict__, f, ensure_ascii=False, indent=2, default=str)
        
        # CSV 저장 (판정 요약)
        csv_path = reports_dir / f"{report.report_id}.csv"
        self._save_decisions_csv(report.decisions, csv_path)
        
        print(f"보고서 저장됨:")
        print(f"  JSON: {json_path}")
        print(f"  CSV:  {csv_path}")

    def _save_decisions_csv(self, decisions: List, csv_path: Path) -> None:
        """판정 결과를 CSV로 저장"""
        import pandas as pd
        
        data = []
        for decision in decisions:
            data.append({
                'timestamp': decision.timestamp,
                'location': decision.location,
                'decision': decision.decision,
                'reasoning': decision.reasoning,
                'limiting_factor': decision.limiting_factor,
                'eta_impact': decision.eta_impact,
                'gamma_alert': decision.gamma_alert
            })
        
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding='utf-8')

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='해양 날씨 보고서 생성')
    parser.add_argument('--locations', default='AGI,DAS', help='대상 지역 (쉼표 구분)')
    parser.add_argument('--config', default='config', help='설정 디렉토리')
    
    args = parser.parse_args()
    
    # 오케스트레이터 초기화
    orchestrator = MarineWeatherOrchestrator(args.config)
    
    # 보고서 생성
    locations = args.locations.split(',')
    report = orchestrator.generate_report(locations)
    
    # 요약 출력
    print(f"\n=== 최종 요약 ===")
    for location in locations:
        location_decisions = [d for d in report.decisions if d.location == location]
        if location_decisions:
            go_count = sum(1 for d in location_decisions if d.decision == "GO")
            conditional_count = sum(1 for d in location_decisions if d.decision == "CONDITIONAL")
            no_go_count = sum(1 for d in location_decisions if d.decision == "NO-GO")
            
            print(f"{location}: GO={go_count}, COND={conditional_count}, NO-GO={no_go_count}")

if __name__ == "__main__":
    main()
