#!/usr/bin/env python3
"""KR: 운항 가능성 예측 데모 / EN: Operability prediction demo."""

import argparse
import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.schema import MarineTimeseries
from src.marine_ops.operability.api import create_operability_report
from src.marine_ops.connectors.stormglass import StormglassConnector
from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
from src.marine_ops.connectors.worldtides import create_marine_timeseries_from_worldtides
from scripts.offline_support import decide_execution_mode, generate_offline_dataset

def collect_weather_data(mode: str = "auto") -> Tuple[List[MarineTimeseries], str, List[str]]:
    """KR: 기상 데이터 수집 / EN: Collect marine weather data."""

    print("🌊 기상 데이터 수집 중...")

    lat, lon = 25.2048, 55.2708
    forecast_hours = 24 * 7
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=forecast_hours)
    required_secrets = ["STORMGLASS_API_KEY", "WORLDTIDES_API_KEY"]
    missing_secrets = [key for key in required_secrets if not os.getenv(key)]
    resolved_mode, offline_reasons = decide_execution_mode(mode, missing_secrets, ncm_available=True)

    if resolved_mode == "offline":
        synthetic_series, _ = generate_offline_dataset("UAE_Waters", forecast_hours)
        if offline_reasons:
            print(f"⚠️ 오프라인 모드 전환: {', '.join(offline_reasons)}")
        return synthetic_series, resolved_mode, offline_reasons

    weather_data: List[MarineTimeseries] = []

    stormglass_key = os.getenv("STORMGLASS_API_KEY", "")
    if stormglass_key:
        try:
            print("  📡 Stormglass API에서 데이터 수집...")
            sg_connector = StormglassConnector(api_key=stormglass_key)
            sg_data = sg_connector.get_marine_weather(
                lat,
                lon,
                start_time,
                end_time,
                location="UAE_Waters",
            )
            if sg_data and sg_data.data_points:
                weather_data.append(sg_data)
                print(f"    ✅ {len(sg_data.data_points)}개 데이터 포인트 수집")
            else:
                print("    ⚠️ Stormglass 데이터 없음")
        except Exception as error:
            print(f"    ❌ Stormglass 오류: {error}")
    else:
        print("  ⚠️ Stormglass API 키 없음으로 건너뜀")

    try:
        print("  📡 Open-Meteo API에서 데이터 수집...")
        om_connector = OpenMeteoConnector()
        om_data = om_connector.get_marine_weather(
            lat,
            lon,
            start_time,
            end_time,
            location="UAE_Waters",
        )
        if om_data and om_data.data_points:
            weather_data.append(om_data)
            print(f"    ✅ {len(om_data.data_points)}개 데이터 포인트 수집")
        else:
            print("    ⚠️ Open-Meteo 데이터 없음")
    except Exception as error:
        print(f"    ❌ Open-Meteo 오류: {error}")

    worldtides_key = os.getenv("WORLDTIDES_API_KEY", "")
    if worldtides_key:
        try:
            print("  📡 WorldTides API에서 데이터 수집...")
            wt_data = create_marine_timeseries_from_worldtides(
                lat,
                lon,
                worldtides_key,
                forecast_hours,
                "UAE_Waters",
            )
            if wt_data and wt_data.data_points:
                weather_data.append(wt_data)
                print(f"    ✅ {len(wt_data.data_points)}개 데이터 포인트 수집")
            else:
                print("    ⚠️ WorldTides 데이터 없음")
        except Exception as error:
            print(f"    ❌ WorldTides 오류: {error}")
    else:
        print("  ⚠️ WorldTides API 키 없음으로 건너뜀")

    if not weather_data:
        print("⚠️ 외부 데이터가 없어 합성 데이터로 대체합니다.")
        synthetic_series, _ = generate_offline_dataset("UAE_Waters", forecast_hours)
        weather_data = synthetic_series
        offline_reasons.append("외부 데이터 수집 실패")
        resolved_mode = "offline"

    print(f"📊 총 {len(weather_data)}개 소스에서 데이터 수집 완료")
    return weather_data, resolved_mode, offline_reasons

def run_operability_prediction(weather_data: List[MarineTimeseries]) -> Dict[str, Any]:
    """KR: 운항 가능성 예측 실행 / EN: Run operability prediction."""
    print("🚢 운항 가능성 예측 실행 중...")
    
    # 항로 정보 정의
    routes = [
        {
            "name": "Abu Dhabi to AGI or DAS",
            "distance_nm": 65.0,
            "planned_speed_kt": 12.0,
            "hs_forecast": 1.2
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
    """KR: 결과 저장 / EN: Persist results."""
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
    """KR: 결과 요약 출력 / EN: Print result summary."""
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

def parse_args() -> argparse.Namespace:
    """KR: CLI 인자 파싱 / EN: Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="HVDC Marine operability demo")
    parser.add_argument("--mode", choices=["auto", "online", "offline"], default="auto", help="실행 모드 (auto/online/offline)")
    parser.add_argument("--output", default="out", help="결과 출력 디렉터리")
    return parser.parse_args()


def main() -> None:
    """KR: 데모 실행 / EN: Run demo."""

    args = parse_args()

    print("🚢 HVDC 해양 운항 가능성 예측 시스템")
    print("=" * 50)

    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True, parents=True)

    try:
        weather_data, resolved_mode, offline_reasons = collect_weather_data(args.mode)
        print(f"⚙️ 실행 모드: {resolved_mode}")
        if offline_reasons:
            print("  ↳ 사유: " + ", ".join(offline_reasons))

        report = run_operability_prediction(weather_data)
        save_results(report, output_dir)
        print_summary(report)

        print(f"\n✅ 운항 가능성 예측 완료! 결과는 {output_dir} 디렉토리에 저장되었습니다.")

    except Exception as error:
        print(f"\n❌ 오류 발생: {error}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
