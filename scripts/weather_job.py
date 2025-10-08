#!/usr/bin/env python3
"""
GitHub Actions용 해양 날씨 작업 스크립트
매시간 실행되어 해양 날씨 데이터를 수집하고 요약 보고서를 생성합니다.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.connectors.stormglass import StormglassConnector, LOCATIONS as SG_LOCATIONS
from src.marine_ops.connectors.open_meteo import OpenMeteoConnector
from src.marine_ops.connectors.worldtides import create_marine_timeseries_from_worldtides
from src.marine_ops.eri.compute import ERICalculator
from src.marine_ops.decision.fusion import ForecastFusion, OperationalDecisionMaker
from src.marine_ops.core.schema import MarineTimeseries, ERIPoint
from scripts.offline_support import decide_execution_mode, generate_offline_dataset

try:
    from ncm_web.ncm_selenium_ingestor import NCMSeleniumIngestor

    NCM_IMPORT_ERROR: Exception | None = None
except Exception as import_error:  # pragma: no cover - import guard
    NCMSeleniumIngestor = None  # type: ignore[assignment]
    NCM_IMPORT_ERROR = import_error
def load_config(config_path: str) -> dict:
    """설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith('.yml') or config_path.endswith('.yaml'):
                import yaml
                return yaml.safe_load(f)
            else:
                return json.load(f)
    except FileNotFoundError:
        print(f"설정 파일을 찾을 수 없습니다: {config_path}")
        return {}

def collect_weather_data(location_name: str = "AGI", forecast_hours: int = 24, mode: str = "auto") -> dict:
    """해양 날씨 데이터 수집"""
    print(f"🌊 {location_name} 해역 날씨 데이터 수집 시작...")

    lat, lon = SG_LOCATIONS[location_name]['lat'], SG_LOCATIONS[location_name]['lon']
    now = datetime.now()
    end_date = now + timedelta(hours=forecast_hours)

    mandatory_secrets = ["STORMGLASS_API_KEY"]
    optional_secrets = ["WORLDTIDES_API_KEY"]

    missing_mandatory = [key for key in mandatory_secrets if not os.getenv(key)]
    missing_optional = [key for key in optional_secrets if not os.getenv(key)]

    resolved_mode, offline_reasons = decide_execution_mode(
        mode,
        missing_mandatory,
        NCMSeleniumIngestor is not None,
    )

    if missing_optional:
        print(
            "ℹ️ 선택 시크릿 누락: "
            + ", ".join(missing_optional)
            + " (실제 데이터 수집은 계속 진행됩니다)"
        )

    if resolved_mode == "offline":
        synthetic_series, statuses = generate_offline_dataset(location_name, forecast_hours)
        if offline_reasons:
            print(f"⚠️ 오프라인 모드 전환: {', '.join(offline_reasons)}")
        return {
            'timeseries': synthetic_series,
            'api_status': statuses,
            'location': location_name,
            'forecast_hours': forecast_hours,
            'collected_at': now.isoformat(),
            'mode': resolved_mode,
            'offline_reasons': offline_reasons,
        }

    all_timeseries: List[MarineTimeseries] = []
    api_status: dict[str, dict[str, float]] = {}

    # API 키 로드
    stormglass_key = os.getenv('STORMGLASS_API_KEY', '')
    worldtides_key = os.getenv('WORLDTIDES_API_KEY', '')

    # 1. Stormglass 데이터 수집
    try:
        if stormglass_key:
            sg_connector = StormglassConnector(api_key=stormglass_key)
            sg_timeseries = sg_connector.get_marine_weather(lat, lon, now, end_date, location=location_name)
            all_timeseries.append(sg_timeseries)
            api_status['STORMGLASS'] = {
                'status': '✅ 실제 데이터',
                'confidence': getattr(sg_timeseries, 'confidence', 0.5)
            }
            print(f"✅ Stormglass: {len(sg_timeseries.data_points)}개 데이터 포인트")
        else:
            api_status['STORMGLASS'] = {'status': '❌ API 키 없음', 'confidence': 0.0}
            print("❌ Stormglass API 키 없음")
    except Exception as e:
        print(f"❌ Stormglass 수집 실패: {e}")
        api_status['STORMGLASS'] = {'status': '❌ 실패', 'confidence': 0.0}

    # 2. Open-Meteo 데이터 수집
    try:
        om_connector = OpenMeteoConnector()
        om_timeseries = om_connector.get_marine_weather(lat, lon, now, end_date, location=location_name)
        all_timeseries.append(om_timeseries)
        api_status['OPEN_METEO'] = {
            'status': '✅ 실제 데이터',
            'confidence': getattr(om_timeseries, 'confidence', 0.5)
        }
        print(f"✅ Open-Meteo: {len(om_timeseries.data_points)}개 데이터 포인트")
    except Exception as e:
        print(f"❌ Open-Meteo 수집 실패: {e}")
        api_status['OPEN_METEO'] = {'status': '❌ 실패', 'confidence': 0.0}

    # 3. NCM Selenium 데이터 수집
    if NCMSeleniumIngestor is None:
        api_status['NCM_SELENIUM'] = {'status': '❌ 모듈 누락', 'confidence': 0.0}
        if NCM_IMPORT_ERROR is not None:
            print(f"❌ NCM Selenium 로드 실패: {NCM_IMPORT_ERROR}")
    else:
        try:
            ncm_ingestor = NCMSeleniumIngestor(headless=True)
            ncm_timeseries = ncm_ingestor.create_marine_timeseries(location=location_name, forecast_hours=forecast_hours)
            all_timeseries.append(ncm_timeseries)
            api_status['NCM_SELENIUM'] = {
                'status': '✅ 실제 데이터' if "fallback" not in ncm_timeseries.source else '⚠️ 폴백 데이터',
                'confidence': getattr(ncm_timeseries, 'confidence', 0.5)
            }
            print(f"✅ NCM Selenium: {len(ncm_timeseries.data_points)}개 데이터 포인트")
        except Exception as e:
            print(f"❌ NCM Selenium 수집 실패: {e}")
            api_status['NCM_SELENIUM'] = {'status': '❌ 실패', 'confidence': 0.0}

    # 4. WorldTides 데이터 수집 (선택사항)
    if worldtides_key:
        try:
            wt_timeseries = create_marine_timeseries_from_worldtides(lat, lon, worldtides_key, forecast_hours, location_name)
            all_timeseries.append(wt_timeseries)
            api_status['WORLDTIDES'] = {
                'status': '✅ 실제 데이터',
                'confidence': getattr(wt_timeseries, 'confidence', 0.5)
            }
            print(f"✅ WorldTides: {len(wt_timeseries.data_points)}개 데이터 포인트")
        except Exception as e:
            print(f"⚠️ WorldTides 수집 실패: {e}")
            api_status['WORLDTIDES'] = {'status': '⚠️ 크레딧 부족', 'confidence': 0.3}
    else:
        api_status['WORLDTIDES'] = {'status': '❌ API 키 없음', 'confidence': 0.0}

    if not all_timeseries:
        print("⚠️ 외부 데이터가 없어 합성 데이터로 대체합니다.")
        synthetic_series, synthetic_status = generate_offline_dataset(location_name, forecast_hours)
        all_timeseries.extend(synthetic_series)
        api_status.update(synthetic_status)
        offline_reasons.append("외부 데이터 수집 실패")
        resolved_mode = "offline"

    return {
        'timeseries': all_timeseries,
        'api_status': api_status,
        'location': location_name,
        'forecast_hours': forecast_hours,
        'collected_at': now.isoformat(),
        'mode': resolved_mode,
        'offline_reasons': offline_reasons,
    }

def analyze_weather_data(data: dict) -> dict:
    """수집된 날씨 데이터 분석"""
    print("📊 날씨 데이터 분석 중...")
    
    all_timeseries = data['timeseries']
    if not all_timeseries:
        return {'error': '수집된 데이터가 없습니다'}
    
    # ERI 계산
    eri_calculator = ERICalculator()
    all_eri_points = []
    
    for timeseries in all_timeseries:
        eri_points = eri_calculator.compute_eri_timeseries(timeseries)
        all_eri_points.extend(eri_points)
    
    # 예보 융합
    fusion_settings = {
        'ncm_weight': 0.60,
        'system_weight': 0.40,
        'alpha': 0.7,
        'beta': 0.3
    }
    
    forecast_fusion = ForecastFusion(fusion_settings)
    fused_forecasts = forecast_fusion.fuse_forecast_sources(all_timeseries, data['location'])
    
    # 운항 판정
    decision_settings = {
        'gate': {
            'go': {'hs_m': 1.0, 'wind_kt': 20.0},
            'conditional': {'hs_m': 1.2, 'wind_kt': 22.0}
        },
        'alert_gamma': {
            'rough_at_times': 0.15,
            'high_seas': 0.30
        }
    }
    
    decision_maker = OperationalDecisionMaker(decision_settings)
    decisions = decision_maker.decide_and_eta(fused_forecasts, all_eri_points)
    
    # 통계 계산
    go_count = sum(1 for d in decisions if d.decision == 'GO')
    conditional_count = sum(1 for d in decisions if d.decision == 'CONDITIONAL')
    no_go_count = sum(1 for d in decisions if d.decision == 'NO-GO')
    
    avg_eri = sum(p.eri_value for p in all_eri_points) / len(all_eri_points) if all_eri_points else 0
    avg_wind_speed = sum(f.wind_speed_fused for f in fused_forecasts) / len(fused_forecasts) if fused_forecasts else 0
    avg_wave_height = sum(f.wave_height_fused for f in fused_forecasts) / len(fused_forecasts) if fused_forecasts else 0
    
    return {
        'total_data_points': sum(len(ts.data_points) for ts in all_timeseries),
        'fused_forecasts': len(fused_forecasts),
        'decisions': {
            'total': len(decisions),
            'GO': go_count,
            'CONDITIONAL': conditional_count,
            'NO-GO': no_go_count
        },
        'averages': {
            'eri': avg_eri,
            'wind_speed_ms': avg_wind_speed,
            'wave_height_m': avg_wave_height
        },
        'eri_points': len(all_eri_points),
        'confidence_scores': [getattr(ts, 'confidence', 0.5) for ts in all_timeseries]
    }

def generate_summary_report(data: dict, analysis: dict, output_dir: str) -> dict:
    """요약 보고서 생성"""
    print("📝 요약 보고서 생성 중...")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # JSON 요약
    execution_mode = data.get('mode', 'online')
    success_sources = sum(1 for status in data['api_status'].values() if '✅' in status['status'])
    total_sources = max(len(data['api_status']), 1)
    collection_rate = success_sources / total_sources * 100
    summary_json = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'location': data['location'],
            'forecast_hours': data['forecast_hours'],
            'system_version': 'v2.1',
            'execution_mode': execution_mode,
        },
        'api_status': data['api_status'],
        'analysis': analysis,
        'collection_stats': {
            'total_timeseries': len(data['timeseries']),
            'total_data_points': analysis.get('total_data_points', 0),
            'data_collection_rate': collection_rate,
        }
    }

    if data.get('offline_reasons'):
        summary_json['metadata']['offline_reasons'] = data['offline_reasons']
    
    json_path = output_path / f"summary_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary_json, f, ensure_ascii=False, indent=2)
    
    # CSV 요약
    csv_data = []
    for api_name, status in data['api_status'].items():
        csv_data.append({
            'API': api_name,
            'Status': status['status'],
            'Confidence': status['confidence'],
            'Timestamp': datetime.now().isoformat()
        })
    
    csv_path = output_path / f"api_status_{timestamp}.csv"
    df = pd.DataFrame(csv_data)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    # 텍스트 요약
    txt_content = f"""🌊 UAE 해역 해양 날씨 보고서
========================================
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
위치: {data['location']} (Al Ghallan Island)
예보 기간: {data['forecast_hours']}시간
실행 모드: {execution_mode.upper()}
"""

    if data.get('offline_reasons'):
        txt_content += "오프라인 사유: " + "; ".join(data['offline_reasons']) + "\n"

    txt_content += "\n📊 데이터 수집 현황:\n"

    for api_name, status in data['api_status'].items():
        conf = status.get('confidence', None)
        conf_txt = f"{conf:.2f}" if isinstance(conf, (int, float)) else "N/A"
        txt_content += f"  {api_name}: {status['status']} (신뢰도: {conf_txt})\n"
    
    txt_content += f"""
📈 분석 결과:
  - 총 데이터 포인트: {analysis.get('total_data_points', 0):,}개
  - 융합 예보: {analysis.get('fused_forecasts', 0)}개
  - 평균 ERI: {analysis.get('averages', {}).get('eri', 0):.3f}
  - 평균 풍속: {analysis.get('averages', {}).get('wind_speed_ms', 0):.1f} m/s
  - 평균 파고: {analysis.get('averages', {}).get('wave_height_m', 0):.2f} m

🚢 운항 판정:
  - GO: {analysis.get('decisions', {}).get('GO', 0)}회
  - CONDITIONAL: {analysis.get('decisions', {}).get('CONDITIONAL', 0)}회
  - NO-GO: {analysis.get('decisions', {}).get('NO-GO', 0)}회

📋 상세 보고서: {json_path.name}
"""
    
    txt_path = output_path / "summary.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(txt_content)
    
    print(f"✅ 요약 보고서 생성 완료:")
    print(f"  - JSON: {json_path}")
    print(f"  - CSV: {csv_path}")
    print(f"  - TXT: {txt_path}")
    
    return {
        'json_path': str(json_path),
        'csv_path': str(csv_path),
        'txt_path': str(txt_path),
        'summary_json': summary_json
    }

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='GitHub Actions 해양 날씨 작업')
    parser.add_argument('--config', default='config/locations.yml', help='설정 파일 경로')
    parser.add_argument('--out', default='out', help='출력 디렉터리')
    parser.add_argument('--location', default='AGI', help='위치 코드')
    parser.add_argument('--hours', type=int, default=24, help='예보 시간')
    parser.add_argument('--mode', choices=['auto', 'online', 'offline'], default='auto', help='실행 모드 (auto/online/offline)')
    
    args = parser.parse_args()
    
    print("🤖 GitHub Actions 해양 날씨 작업 시작")
    print("=" * 50)
    
    try:
        # 설정 로드
        config = load_config(args.config)
        print(f"✅ 설정 로드: {args.config}")
        
        # 날씨 데이터 수집
        data = collect_weather_data(args.location, args.hours, args.mode)
        
        # 데이터 분석
        analysis = analyze_weather_data(data)
        
        # 요약 보고서 생성
        report = generate_summary_report(data, analysis, args.out)
        
        # 운항 가능성 예측 실행
        try:
            print("\n🚢 운항 가능성 예측 실행 중...")
            from src.marine_ops.operability.api import create_operability_report
            
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
            # data는 딕셔너리이므로 MarineTimeseries 리스트 추출
            weather_timeseries = data.get('timeseries', [])
            operability_report = create_operability_report(weather_timeseries, routes, forecast_days=7)
            
            # 운항 가능성 결과를 메인 보고서에 추가
            report['operability_summary'] = {
                'total_forecasts': operability_report['summary']['total_forecasts'],
                'go_count': operability_report['summary']['go_count'],
                'conditional_count': operability_report['summary']['conditional_count'],
                'nogo_count': operability_report['summary']['nogo_count'],
                'average_confidence': operability_report['summary']['average_confidence']
            }
            
            # 운항 가능성 CSV 저장
            import pandas as pd
            if operability_report['operability_forecasts']:
                csv_data = []
                for forecast in operability_report['operability_forecasts']:
                    csv_data.append({
                        'day': forecast.day,
                        'daypart': forecast.daypart,
                        'P_go': forecast.probabilities.P_go,
                        'P_cond': forecast.probabilities.P_cond,
                        'P_nogo': forecast.probabilities.P_nogo,
                        'decision': forecast.decision,
                        'confidence': forecast.confidence
                    })
                
                df = pd.DataFrame(csv_data)
                operability_csv = Path(args.out) / "operability_forecasts.csv"
                df.to_csv(operability_csv, index=False)
                print(f"  ✅ 운항 가능성 예측 저장: {operability_csv}")
            
            print(f"  ✅ 운항 가능성 예측 완료: GO {operability_report['summary']['go_count']}개, "
                  f"CONDITIONAL {operability_report['summary']['conditional_count']}개, "
                  f"NO-GO {operability_report['summary']['nogo_count']}개")
                  
        except Exception as e:
            print(f"  ⚠️ 운항 가능성 예측 실패: {e}")
            report['operability_summary'] = {'error': str(e)}
        
        # 성공 메시지
        data_rate = report['summary_json']['collection_stats']['data_collection_rate']
        print(f"\n🎉 작업 완료!")
        print(f"📊 데이터 수집률: {data_rate:.1f}%")
        print(f"📁 출력 디렉터리: {args.out}")
        
        return True
        
    except Exception as e:
        print(f"❌ 작업 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
