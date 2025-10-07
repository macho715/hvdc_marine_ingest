#!/usr/bin/env python3
"""KR: 전체 파이프라인 통합 테스트 / EN: Full pipeline integration test."""

from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.offline_support import decide_execution_mode, generate_offline_dataset
from src.marine_ops.eri.compute import ERICalculator
from src.marine_ops.decision.fusion import ForecastFusion, OperationalDecisionMaker


def main() -> None:
    """KR: 통합 파이프라인 실행 / EN: Execute integrated pipeline."""
    
    print("=" * 60)
    print("🚀 HVDC Marine 전체 파이프라인 통합 테스트")
    print("=" * 60)
    
    # 1. 실행 모드 결정
    print("\n📋 1단계: 실행 모드 결정")
    mode, reasons = decide_execution_mode("auto", ["STORMGLASS_API_KEY"], True)
    print(f"  ✅ 실행 모드: {mode}")
    if reasons:
        print(f"  ℹ️ 사유: {', '.join(reasons)}")
    
    # 2. 데이터 생성
    print("\n📊 2단계: 해양 데이터 생성")
    timeseries_list, statuses = generate_offline_dataset("AGI", 24)
    print(f"  ✅ 생성된 시계열: {len(timeseries_list)}개")
    print(f"  ✅ 데이터 포인트: {sum(len(ts.data_points) for ts in timeseries_list)}개")
    
    # 3. ERI 계산
    print("\n⚠️ 3단계: ERI (환경 위험 지수) 계산")
    eri_calculator = ERICalculator()
    all_eri_points = []
    for ts in timeseries_list:
        eri_points = eri_calculator.compute_eri_timeseries(ts)
        all_eri_points.extend(eri_points)
    print(f"  ✅ 계산된 ERI 포인트: {len(all_eri_points)}개")
    avg_eri = sum(p.eri_value for p in all_eri_points) / len(all_eri_points)
    print(f"  ✅ 평균 ERI: {avg_eri:.3f}")
    
    # 4. 예보 융합
    print("\n🔀 4단계: 예보 융합")
    fusion_settings = {
        'ncm_weight': 0.60,
        'system_weight': 0.40,
        'alpha': 0.7,
        'beta': 0.3
    }
    forecast_fusion = ForecastFusion(fusion_settings)
    fused_forecasts = forecast_fusion.fuse_forecast_sources(timeseries_list, "AGI")
    print(f"  ✅ 융합된 예보: {len(fused_forecasts)}개")
    
    avg_wind = sum(f.wind_speed_fused for f in fused_forecasts) / len(fused_forecasts)
    avg_wave = sum(f.wave_height_fused for f in fused_forecasts) / len(fused_forecasts)
    print(f"  ✅ 평균 풍속: {avg_wind:.1f} m/s")
    print(f"  ✅ 평균 파고: {avg_wave:.2f} m")
    
    # 5. 운항 판정
    print("\n🚢 5단계: 운항 판정")
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
    
    go_count = sum(1 for d in decisions if d.decision == "GO")
    cond_count = sum(1 for d in decisions if d.decision == "CONDITIONAL")
    nogo_count = sum(1 for d in decisions if d.decision == "NO-GO")
    
    print(f"  ✅ 생성된 판정: {len(decisions)}개")
    print(f"  ✅ GO: {go_count}개")
    print(f"  ⚠️ CONDITIONAL: {cond_count}개")
    print(f"  ❌ NO-GO: {nogo_count}개")
    
    # 6. 통합 결과 요약
    print("\n" + "=" * 60)
    print("📊 통합 파이프라인 실행 결과")
    print("=" * 60)
    print(f"✅ 실행 모드: {mode}")
    print(f"✅ 데이터 소스: {len(timeseries_list)}개")
    print(f"✅ 데이터 포인트: {sum(len(ts.data_points) for ts in timeseries_list)}개")
    print(f"✅ ERI 계산: {len(all_eri_points)}개")
    print(f"✅ 융합 예보: {len(fused_forecasts)}개")
    print(f"✅ 운항 판정: {len(decisions)}개")
    print(f"✅ 평균 ERI: {avg_eri:.3f}")
    print(f"✅ 평균 풍속: {avg_wind:.1f} m/s")
    print(f"✅ 평균 파고: {avg_wave:.2f} m")
    print(f"✅ 운항 가능률: {(go_count/len(decisions)*100):.1f}%")
    
    print("\n🎉 전체 파이프라인 통합 테스트 성공!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 파이프라인 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

