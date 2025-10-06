# KR: 통합 파이프라인 데모 (API 키 없이 실행)
# EN: Integrated pipeline demo (runs without API keys)

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.marine_ops.core.schema import (
    MarineTimeseries, MarineDataPoint, FusedForecast, 
    OperationalDecision, MarineReport, ERIPoint
)

def create_demo_data():
    """데모 데이터 생성"""
    
    print("=== 데모 데이터 생성 ===")
    
    # AGI와 DAS에 대한 샘플 데이터 생성
    locations = ['AGI', 'DAS']
    timeseries_list = []
    
    for location in locations:
        print(f"\n--- {location} 데모 데이터 ---")
        
        data_points = []
        base_time = datetime.now()
        
        # 24시간 예보 생성
        for i in range(24):
            timestamp = (base_time + timedelta(hours=i)).isoformat()
            
            # 시뮬레이션된 해양 조건
            wind_speed = 8.0 + (i % 8) * 2.0  # 8-22 m/s
            wave_height = 1.0 + (i % 6) * 0.3  # 1.0-2.5 m
            
            data_point = MarineDataPoint(
                timestamp=timestamp,
                wind_speed=wind_speed,
                wind_direction=270.0 + (i * 15) % 360,  # 회전하는 풍향
                wave_height=wave_height,
                sea_state="Slight" if wave_height < 1.5 else "Moderate"
            )
            data_points.append(data_point)
        
        timeseries = MarineTimeseries(
            source="demo_simulator",
            location=location,
            data_points=data_points,
            ingested_at=datetime.now().isoformat(),
            confidence=0.8
        )
        
        timeseries_list.append(timeseries)
        print(f"  생성된 데이터 포인트: {len(data_points)}개")
    
    return timeseries_list

def calculate_demo_eri(timeseries_list):
    """데모 ERI 계산"""
    
    print(f"\n=== ERI 계산 ===")
    
    eri_points = []
    
    for timeseries in timeseries_list:
        for dp in timeseries.data_points:
            # 간단한 ERI 계산
            wind_risk = min(1.0, dp.wind_speed / 25.0)  # 25 m/s에서 최대 위험
            wave_risk = min(1.0, dp.wave_height / 3.0)  # 3m에서 최대 위험
            
            total_eri = (wind_risk * 0.5 + wave_risk * 0.5) * 100  # 0-100 스케일
            
            eri_point = ERIPoint(
                timestamp=dp.timestamp,
                eri_value=total_eri,
                wind_contribution=wind_risk * 100,
                wave_contribution=wave_risk * 100,
                visibility_contribution=10.0,  # 고정값
                fog_contribution=5.0  # 고정값
            )
            eri_points.append(eri_point)
    
    print(f"  계산된 ERI 포인트: {len(eri_points)}개")
    return eri_points

def create_demo_fusion(timeseries_list):
    """데모 융합 예보 생성"""
    
    print(f"\n=== 융합 예보 생성 ===")
    
    fused_forecasts = []
    
    # 시간별로 그룹화
    time_groups = {}
    for ts in timeseries_list:
        for dp in ts.data_points:
            if dp.timestamp not in time_groups:
                time_groups[dp.timestamp] = []
            time_groups[dp.timestamp].append(dp)
    
    # 각 시간대에 대해 융합 수행
    for timestamp, data_points in time_groups.items():
        if len(data_points) >= 1:  # 최소 1개 데이터 포인트
            dp = data_points[0]  # 첫 번째 데이터 사용
            
            fused = FusedForecast(
                location=dp.timestamp.split('T')[0],  # 간단한 위치 추출
                timestamp=timestamp,
                wind_speed_fused=dp.wind_speed,
                wave_height_fused=dp.wave_height,
                confidence=0.8,
                sources_used=["demo_simulator"],
                weights={"demo_simulator": 1.0}
            )
            fused_forecasts.append(fused)
    
    print(f"  융합된 예보: {len(fused_forecasts)}개")
    return fused_forecasts

def make_demo_decisions(fused_forecasts):
    """데모 운항 판정"""
    
    print(f"\n=== 운항 판정 ===")
    
    decisions = []
    
    for forecast in fused_forecasts:
        # 간단한 판정 로직
        if forecast.wind_speed_fused <= 15.0 and forecast.wave_height_fused <= 1.5:
            decision = "GO"
            reasoning = "풍속 및 파고 조건 양호"
        elif forecast.wind_speed_fused <= 20.0 and forecast.wave_height_fused <= 2.0:
            decision = "CONDITIONAL"
            reasoning = "조건부 운항 가능 - 주의 필요"
        else:
            decision = "NO-GO"
            reasoning = "풍속 또는 파고 조건 불량"
        
        operational_decision = OperationalDecision(
            location="AGI",  # 간단히 고정
            timestamp=forecast.timestamp,
            decision=decision,
            reasoning=reasoning,
            eta_impact="No significant impact" if decision == "GO" else "Potential delay"
        )
        decisions.append(operational_decision)
    
    print(f"  생성된 판정: {len(decisions)}개")
    return decisions

def create_demo_report(timeseries_list, eri_points, fused_forecasts, decisions):
    """데모 보고서 생성"""
    
    print(f"\n=== 보고서 생성 ===")
    
    report = MarineReport(
        report_id=f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M')}",
        generated_at=datetime.now().isoformat(),
        locations=["AGI", "DAS"],
        forecast_horizon=24,
        decisions=decisions,
        fused_forecasts=fused_forecasts,
        eri_timeseries=eri_points,
        warnings=["데모 모드로 실행됨"],
        metadata={
            "demo_mode": True,
            "sources_used": ["demo_simulator"],
            "api_keys_required": False
        }
    )
    
    return report

def save_demo_report(report):
    """데모 보고서 저장"""
    
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # JSON 저장 (직렬화 가능한 형태로 변환)
    json_path = reports_dir / f"{report.report_id}.json"
    
    report_dict = {
        "report_id": report.report_id,
        "generated_at": report.generated_at,
        "locations": report.locations,
        "forecast_horizon": report.forecast_horizon,
        "warnings": report.warnings,
        "metadata": report.metadata,
        "decisions": [
            {
                "location": d.location,
                "timestamp": d.timestamp,
                "decision": d.decision,
                "reasoning": d.reasoning,
                "eta_impact": d.eta_impact
            }
            for d in report.decisions
        ],
        "fused_forecasts": [
            {
                "location": f.location,
                "timestamp": f.timestamp,
                "wind_speed_fused": f.wind_speed_fused,
                "wave_height_fused": f.wave_height_fused,
                "confidence": f.confidence,
                "sources_used": f.sources_used
            }
            for f in report.fused_forecasts
        ],
        "eri_timeseries": [
            {
                "timestamp": e.timestamp,
                "eri_value": e.eri_value,
                "wind_contribution": e.wind_contribution,
                "wave_contribution": e.wave_contribution
            }
            for e in report.eri_timeseries
        ]
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)
    
    print(f"  보고서 저장됨: {json_path}")
    
    # CSV 요약 저장
    csv_path = reports_dir / f"{report.report_id}_summary.csv"
    
    import pandas as pd
    
    summary_data = []
    for decision in report.decisions:
        summary_data.append({
            "timestamp": decision.timestamp,
            "decision": decision.decision,
            "reasoning": decision.reasoning
        })
    
    df = pd.DataFrame(summary_data)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    
    print(f"  요약 저장됨: {csv_path}")

def main():
    """메인 실행 함수"""
    
    print("=== 통합 해양 날씨 파이프라인 데모 ===")
    print("(API 키 없이 실행 가능한 버전)")
    
    try:
        # 1. 데모 데이터 생성
        timeseries_list = create_demo_data()
        
        # 2. ERI 계산
        eri_points = calculate_demo_eri(timeseries_list)
        
        # 3. 융합 예보 생성
        fused_forecasts = create_demo_fusion(timeseries_list)
        
        # 4. 운항 판정
        decisions = make_demo_decisions(fused_forecasts)
        
        # 5. 보고서 생성
        report = create_demo_report(timeseries_list, eri_points, fused_forecasts, decisions)
        
        # 6. 보고서 저장
        save_demo_report(report)
        
        # 7. 요약 출력
        print(f"\n=== 최종 요약 ===")
        go_count = sum(1 for d in decisions if d.decision == "GO")
        conditional_count = sum(1 for d in decisions if d.decision == "CONDITIONAL")
        no_go_count = sum(1 for d in decisions if d.decision == "NO-GO")
        
        print(f"총 판정: {len(decisions)}개")
        print(f"GO: {go_count}개, CONDITIONAL: {conditional_count}개, NO-GO: {no_go_count}개")
        print(f"보고서 ID: {report.report_id}")
        
        print(f"\n=== 데모 완료 ===")
        return True
        
    except Exception as e:
        print(f"\n=== 데모 실패 ===")
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
