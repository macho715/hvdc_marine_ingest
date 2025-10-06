#!/usr/bin/env python3
"""
KR: 통합된 운항 가능성 예측 데모
EN: Integrated operability prediction demo

이 스크립트는 HVDC 해양 데이터 수집 시스템과 operability_package를 통합하여
실제 기상 데이터를 기반으로 운항 가능성 예측을 수행합니다.
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.schema import MarineTimeseries, MarineDataPoint
from src.marine_ops.operability.api import OperabilityPredictor, create_operability_report
from src.marine_ops.connectors.stormglass import StormglassConnector
from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
from src.marine_ops.connectors.worldtides import fetch_worldtides_heights, create_marine_timeseries_from_worldtides
from src.marine_ops.eri.compute import ERICalculator

def collect_weather_data() -> List[MarineTimeseries]:
    """실제 기상 데이터 수집"""
    print("🌊 기상 데이터 수집 중...")
    
    weather_data = []
    
    # UAE 해역 좌표 (Dubai 근처)
    lat, lon = 25.2048, 55.2708
    
    try:
        # Stormglass 데이터 수집
        print("  📡 Stormglass API에서 데이터 수집...")
        sg_connector = StormglassConnector()
        sg_data = sg_connector.get_marine_weather(lat, lon, days=7)
        if sg_data and sg_data.data_points:
            weather_data.append(sg_data)
            print(f"    ✅ {len(sg_data.data_points)}개 데이터 포인트 수집")
        else:
            print("    ⚠️ Stormglass 데이터 없음")
    except Exception as e:
        print(f"    ❌ Stormglass 오류: {e}")
    
    try:
        # Open-Meteo 데이터 수집
        print("  📡 Open-Meteo API에서 데이터 수집...")
        om_connector = OpenMeteoConnector()
        om_data = om_connector.get_marine_weather(lat, lon, days=7)
        if om_data and om_data.data_points:
            weather_data.append(om_data)
            print(f"    ✅ {len(om_data.data_points)}개 데이터 포인트 수집")
        else:
            print("    ⚠️ Open-Meteo 데이터 없음")
    except Exception as e:
        print(f"    ❌ Open-Meteo 오류: {e}")
    
    try:
        # WorldTides 데이터 수집
        print("  📡 WorldTides API에서 데이터 수집...")
        wt_key = "a7b5bd88-041e-4316-8f8e-02670eb44bc7"  # API 키
        wt_raw = fetch_worldtides_heights(lat, lon, wt_key, hours=168)  # 7일
        if wt_raw and 'heights' in wt_raw:
            wt_data = create_marine_timeseries_from_worldtides(wt_raw, lat, lon)
            if wt_data and wt_data.data_points:
                weather_data.append(wt_data)
                print(f"    ✅ {len(wt_data.data_points)}개 데이터 포인트 수집")
            else:
                print("    ⚠️ WorldTides 데이터 변환 실패")
        else:
            print("    ⚠️ WorldTides 데이터 없음")
    except Exception as e:
        print(f"    ❌ WorldTides 오류: {e}")
    
    print(f"📊 총 {len(weather_data)}개 소스에서 데이터 수집 완료")
    return weather_data

def create_synthetic_ensemble_data() -> List[MarineTimeseries]:
    """합성 앙상블 데이터 생성 (실제 데이터가 부족할 경우)"""
    print("🎲 합성 앙상블 데이터 생성...")
    
    import random
    import numpy as np
    from datetime import datetime, timedelta
    
    random.seed(42)
    np.random.seed(42)
    
    # 7일간의 시간별 데이터 생성
    data_points = []
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    for day in range(7):
        for hour in range(0, 24, 3):  # 3시간 간격
            timestamp = base_time + timedelta(days=day, hours=hour)
            
            # 시간과 날짜에 따른 파라미터 변화
            day_factor = 1 + (day * 0.05)  # 날이 지날수록 조건 악화
            hour_factor = 1 + 0.1 * np.sin(hour / 4.0)  # 시간에 따른 변화
            
            # 파고 (Hs) 생성
            hs_base = 0.8 + (day * 0.1) * hour_factor
            hs = max(0.1, np.random.normal(hs_base, 0.2))
            
            # 풍속 생성
            wind_base = 15.0 + (day * 0.5) * hour_factor
            wind = max(0.5, np.random.normal(wind_base, 3.0))
            
            # 풍향 생성
            wind_dir = np.random.uniform(0, 360)
            
            data_point = MarineDataPoint(
                timestamp=timestamp.isoformat(),
                wind_speed=wind,
                wind_direction=wind_dir,
                wave_height=hs,
                wave_period=np.random.uniform(6, 12),
                wave_direction=wind_dir + np.random.uniform(-30, 30),
                sea_state="Moderate" if hs < 1.5 else "Rough",
                visibility=np.random.uniform(8, 15),
                temperature=np.random.uniform(22, 28),
                confidence=0.7  # 합성 데이터 신뢰도
            )
            data_points.append(data_point)
    
    # MarineTimeseries 객체 생성
    synthetic_timeseries = MarineTimeseries(
        source="synthetic_ensemble",
        location="UAE_Waters",
        data_points=data_points,
        ingested_at=datetime.now().isoformat()
    )
    
    print(f"    ✅ {len(data_points)}개 합성 데이터 포인트 생성")
    return [synthetic_timeseries]

def run_operability_prediction(weather_data: List[MarineTimeseries]) -> Dict[str, Any]:
    """운항 가능성 예측 실행"""
    print("🚢 운항 가능성 예측 실행 중...")
    
    # 항로 정보 정의
    routes = [
        {
            "name": "Abu Dhabi to AGI or DAS",
            "distance_nm": 65.0,
            "planned_speed_kt": 12.0,
            "hs_forecast": 1.2
        },
        {
            "name": "Dubai to Fujairah",
            "distance_nm": 85.0,
            "planned_speed_kt": 10.0,
            "hs_forecast": 1.5
        },
        {
            "name": "Dubai to Ras Al Khaimah",
            "distance_nm": 95.0,
            "planned_speed_kt": 8.0,
            "hs_forecast": 1.8
        }
    ]
    
    # 운항 가능성 보고서 생성
    report = create_operability_report(
        weather_data=weather_data,
        routes=routes,
        forecast_days=7
    )
    
    print(f"    ✅ {len(report['operability_forecasts'])}개 운항 가능성 예측 완료")
    print(f"    ✅ {len(report['eta_predictions'])}개 ETA 예측 완료")
    
    return report

def save_results(report: Dict[str, Any], output_dir: Path):
    """결과 저장"""
    print("💾 결과 저장 중...")
    
    # JSON 보고서 저장
    json_file = output_dir / "operability_report.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"  ✅ JSON 보고서: {json_file}")
    
    # CSV 형식으로 운항 가능성 예측 저장
    if report['operability_forecasts']:
        csv_data = []
        for forecast in report['operability_forecasts']:
            csv_data.append({
                'day': forecast.day,
                'daypart': forecast.daypart,
                'P_go': forecast.probabilities.P_go,
                'P_cond': forecast.probabilities.P_cond,
                'P_nogo': forecast.probabilities.P_nogo,
                'decision': forecast.decision,
                'confidence': forecast.confidence,
                'gate_hs_go': forecast.gate_used.hs_go,
                'gate_wind_go': forecast.gate_used.wind_go
            })
        
        df_forecasts = pd.DataFrame(csv_data)
        csv_file = output_dir / "operability_forecasts.csv"
        df_forecasts.to_csv(csv_file, index=False)
        print(f"  ✅ 운항 가능성 예측 CSV: {csv_file}")
    
    # ETA 예측 CSV 저장
    if report['eta_predictions']:
        eta_data = []
        for eta in report['eta_predictions']:
            eta_data.append({
                'route': eta.route,
                'distance_nm': eta.distance_nm,
                'planned_speed_kt': eta.planned_speed_kt,
                'effective_speed_kt': eta.effective_speed_kt,
                'eta_hours': eta.eta_hours,
                'buffer_minutes': eta.buffer_minutes,
                'hs_impact': eta.hs_impact
            })
        
        df_eta = pd.DataFrame(eta_data)
        eta_csv_file = output_dir / "eta_predictions.csv"
        df_eta.to_csv(eta_csv_file, index=False)
        print(f"  ✅ ETA 예측 CSV: {eta_csv_file}")

def print_summary(report: Dict[str, Any]):
    """결과 요약 출력"""
    print("\n" + "="*60)
    print("📊 운항 가능성 예측 결과 요약")
    print("="*60)
    
    summary = report['summary']
    print(f"📅 예측 기간: {report['forecast_days']}일")
    print(f"📈 총 예측 수: {summary['total_forecasts']}")
    print(f"✅ GO: {summary['go_count']}개")
    print(f"⚠️  CONDITIONAL: {summary['conditional_count']}개")
    print(f"❌ NO-GO: {summary['nogo_count']}개")
    print(f"🎯 평균 신뢰도: {summary['average_confidence']:.2f}")
    
    print("\n🚢 ETA 예측:")
    for eta in report['eta_predictions']:
        print(f"  • {eta.route}: {eta.eta_hours:.1f}시간 "
              f"(계획: {eta.planned_speed_kt}kt → 실제: {eta.effective_speed_kt:.1f}kt)")
    
    print("\n📋 일별 운항 가능성 (최소 P_go):")
    day_summary = {}
    for forecast in report['operability_forecasts']:
        day = forecast.day
        if day not in day_summary:
            day_summary[day] = []
        day_summary[day].append(forecast.probabilities.P_go)
    
    for day in sorted(day_summary.keys()):
        min_p_go = min(day_summary[day])
        status = "🟢" if min_p_go > 0.5 else "🟡" if min_p_go > 0.3 else "🔴"
        print(f"  {status} {day}: P(Go) = {min_p_go:.2f}")

def main():
    """메인 함수"""
    print("🚢 HVDC 해양 운항 가능성 예측 시스템")
    print("="*50)
    
    # 출력 디렉토리 생성
    output_dir = Path("out")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 1. 기상 데이터 수집
        weather_data = collect_weather_data()
        
        # 실제 데이터가 부족하면 합성 데이터 추가
        if len(weather_data) == 0 or sum(len(ts.data_points) for ts in weather_data) < 50:
            print("⚠️ 실제 데이터가 부족하여 합성 데이터를 추가합니다...")
            synthetic_data = create_synthetic_ensemble_data()
            weather_data.extend(synthetic_data)
        
        # 2. 운항 가능성 예측 실행
        report = run_operability_prediction(weather_data)
        
        # 3. 결과 저장
        save_results(report, output_dir)
        
        # 4. 요약 출력
        print_summary(report)
        
        print(f"\n✅ 운항 가능성 예측 완료! 결과는 {output_dir} 디렉토리에 저장되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
