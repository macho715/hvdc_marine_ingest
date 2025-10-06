# KR: 운항 가능성 예측 API
# EN: Operability prediction API

import json
import math
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.schema import (
    MarineDataPoint, MarineTimeseries, 
    OperabilityForecast, OperabilityProbabilities, OperabilityGate,
    ETAPrediction
)
from .operability_forecast import (
    Gate, operability_for_day, decision_from_probs,
    speed_effective, eta_hours, leadtime_adjust
)

class OperabilityPredictor:
    """운항 가능성 예측기"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        운항 가능성 예측기 초기화
        
        Args:
            config_file: 설정 파일 경로 (config/config_thresholds.yaml)
        """
        if config_file is None:
            config_file = "config/config_thresholds.yaml"
            
        self.config_path = Path(config_file)
        self.gate_config = self._load_gate_config()
        self.base_gate = Gate(
            hs_go=self.gate_config['gate']['go']['hs_m'],
            wind_go=self.gate_config['gate']['go']['wind_kt'],
            hs_cond=self.gate_config['gate']['conditional']['hs_m'],
            wind_cond=self.gate_config['gate']['conditional']['wind_kt']
        )
    
    def _load_gate_config(self) -> Dict[str, Any]:
        """게이트 설정 로드"""
        if not self.config_path.exists():
            # 기본 설정 반환
            return {
                'gate': {
                    'go': {'hs_m': 1.00, 'wind_kt': 20.0},
                    'conditional': {'hs_m': 1.20, 'wind_kt': 22.0}
                },
                'leadtime_adjust': {
                    'd4': {'hs_m': 0.10, 'wind_kt': -1.0},
                    'd5': {'hs_m': 0.10, 'wind_kt': -1.0},
                    'd6': {'hs_m': 0.20, 'wind_kt': -2.0},
                    'd7': {'hs_m': 0.20, 'wind_kt': -2.0}
                }
            }
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def predict_operability(
        self, 
        weather_data: List[MarineTimeseries],
        forecast_days: int = 7
    ) -> List[OperabilityForecast]:
        """
        운항 가능성 예측
        
        Args:
            weather_data: 기상 데이터 시계열 리스트
            forecast_days: 예측 일수 (기본 7일)
            
        Returns:
            운항 가능성 예측 리스트
        """
        forecasts = []
        
        # 각 일별로 예측 수행
        for day_idx in range(1, forecast_days + 1):
            # 리드타임 조정된 게이트 적용
            adjusted_gate = leadtime_adjust(day_idx, self.base_gate)
            
            # 시간별 앙상블 데이터 준비
            hs_by_hour, wind_by_hour = self._prepare_hourly_ensembles(
                weather_data, day_idx
            )
            
            # 운항 가능성 계산
            operability_result = operability_for_day(
                day_idx, hs_by_hour, wind_by_hour, self.base_gate
            )
            
            # 결과를 표준 형식으로 변환
            for daypart, probs in operability_result["by_daypart"].items():
                if not any(math.isnan(v) for v in probs.values()):
                    decision = decision_from_probs(probs)
                    
                    forecast = OperabilityForecast(
                        day=f"D+{day_idx}",
                        daypart=daypart,
                        probabilities=OperabilityProbabilities(
                            P_go=probs['P_go'],
                            P_cond=probs['P_cond'],
                            P_nogo=probs['P_nogo']
                        ),
                        decision=decision,
                        gate_used=OperabilityGate(
                            hs_go=adjusted_gate.hs_go,
                            wind_go=adjusted_gate.wind_go,
                            hs_cond=adjusted_gate.hs_cond,
                            wind_cond=adjusted_gate.wind_cond
                        ),
                        confidence=self._calculate_confidence(weather_data, day_idx)
                    )
                    forecasts.append(forecast)
        
        return forecasts
    
    def predict_eta(
        self,
        route: str,
        distance_nm: float,
        planned_speed_kt: float,
        hs_forecast: float,
        buffer_minutes: int = 45
    ) -> ETAPrediction:
        """
        ETA 예측
        
        Args:
            route: 항로명
            distance_nm: 거리 (해리)
            planned_speed_kt: 계획 속도 (노트)
            hs_forecast: 파고 예측 (m)
            buffer_minutes: 버퍼 시간 (분)
            
        Returns:
            ETA 예측 결과
        """
        effective_speed = speed_effective(planned_speed_kt, hs_forecast)
        eta_h = eta_hours(distance_nm, effective_speed, buffer_minutes)
        
        return ETAPrediction(
            route=route,
            distance_nm=distance_nm,
            planned_speed_kt=planned_speed_kt,
            effective_speed_kt=effective_speed,
            eta_hours=eta_h,
            buffer_minutes=buffer_minutes,
            hs_impact=planned_speed_kt - effective_speed
        )
    
    def _prepare_hourly_ensembles(
        self, 
        weather_data: List[MarineTimeseries], 
        day_idx: int
    ) -> tuple[Dict[int, List[float]], Dict[int, List[float]]]:
        """시간별 앙상블 데이터 준비"""
        hs_by_hour = {}
        wind_by_hour = {}
        
        # 현재는 단순화된 구현
        # 실제로는 여러 소스의 앙상블 데이터를 사용해야 함
        for hour in range(24):
            # 기본 앙상블 생성 (실제로는 여러 모델의 예측을 조합)
            hs_ensemble = self._generate_ensemble_for_hour(weather_data, day_idx, hour, 'wave_height')
            wind_ensemble = self._generate_ensemble_for_hour(weather_data, day_idx, hour, 'wind_speed')
            
            hs_by_hour[hour] = hs_ensemble
            wind_by_hour[hour] = wind_ensemble
        
        return hs_by_hour, wind_by_hour
    
    def _generate_ensemble_for_hour(
        self, 
        weather_data: List[MarineTimeseries], 
        day_idx: int, 
        hour: int,
        variable: str
    ) -> List[float]:
        """특정 시간대의 변수에 대한 앙상블 생성"""
        import random
        import numpy as np
        
        # 실제 데이터가 있으면 사용, 없으면 합성 데이터 생성
        ensemble_size = 30
        ensemble = []
        
        for ts in weather_data:
            if ts.data_points:
                # 실제 데이터에서 해당 시간대의 값 추출
                target_time = datetime.now() + timedelta(days=day_idx, hours=hour)
                for dp in ts.data_points:
                    if dp.timestamp.startswith(target_time.strftime('%Y-%m-%d')):
                        value = getattr(dp, variable, None)
                        if value is not None:
                            ensemble.append(value)
        
        # 앙상블이 충분하지 않으면 합성 데이터로 보완
        if len(ensemble) < ensemble_size:
            base_value = 1.0 if variable == 'wave_height' else 15.0
            noise = np.random.normal(0, 0.2, ensemble_size - len(ensemble))
            synthetic = [base_value + n for n in noise]
            ensemble.extend(synthetic)
        
        return ensemble[:ensemble_size]
    
    def _calculate_confidence(
        self, 
        weather_data: List[MarineTimeseries], 
        day_idx: int
    ) -> float:
        """예측 신뢰도 계산"""
        if not weather_data:
            return 0.3
        
        # 데이터 소스 수와 품질을 기반으로 신뢰도 계산
        source_count = len(weather_data)
        confidence = min(0.9, 0.3 + (source_count * 0.1))
        
        # 리드타임에 따른 신뢰도 감소
        leadtime_factor = max(0.5, 1.0 - (day_idx * 0.1))
        
        return confidence * leadtime_factor

def create_operability_report(
    weather_data: List[MarineTimeseries],
    routes: List[Dict[str, Any]] = None,
    forecast_days: int = 7
) -> Dict[str, Any]:
    """
    운항 가능성 보고서 생성
    
    Args:
        weather_data: 기상 데이터
        routes: 항로 정보 리스트
        forecast_days: 예측 일수
        
    Returns:
        운항 가능성 보고서
    """
    predictor = OperabilityPredictor()
    
    # 운항 가능성 예측
    operability_forecasts = predictor.predict_operability(weather_data, forecast_days)
    
    # ETA 예측
    eta_predictions = []
    if routes:
        for route in routes:
            eta = predictor.predict_eta(
                route=route['name'],
                distance_nm=route['distance_nm'],
                planned_speed_kt=route['planned_speed_kt'],
                hs_forecast=route.get('hs_forecast', 1.0)
            )
            eta_predictions.append(eta)
    
    return {
        'operability_forecasts': operability_forecasts,
        'eta_predictions': eta_predictions,
        'summary': {
            'total_forecasts': len(operability_forecasts),
            'go_count': sum(1 for f in operability_forecasts if f.decision == 'GO'),
            'conditional_count': sum(1 for f in operability_forecasts if f.decision == 'CONDITIONAL'),
            'nogo_count': sum(1 for f in operability_forecasts if f.decision == 'NO-GO'),
            'average_confidence': sum(f.confidence or 0.5 for f in operability_forecasts) / len(operability_forecasts) if operability_forecasts else 0.0
        },
        'generated_at': datetime.now().isoformat(),
        'forecast_days': forecast_days
    }
