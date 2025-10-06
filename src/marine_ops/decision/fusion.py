# KR: 다중 소스 융합 및 운항 판정
# EN: Multi-source fusion and operational decision making

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import numpy as np

from src.marine_ops.core.schema import (
    MarineTimeseries, FusedForecast, OperationalDecision, 
    MarineReport, ERIPoint
)

class ForecastFusion:
    """예보 융합 클래스"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.ncm_weight = settings.get('ncm_weight', 0.6)
        self.system_weight = settings.get('system_weight', 0.4)
        self.alpha = settings.get('alpha', 0.7)  # 축소 계수
        self.beta = settings.get('beta', 0.3)    # 스무딩 계수
    
    def fuse_forecast_sources(
        self, 
        timeseries_list: List[MarineTimeseries],
        location: str
    ) -> List[FusedForecast]:
        """다중 소스 예보 융합"""
        
        if not timeseries_list:
            return []
        
        # 시간별로 그룹화
        time_groups = self._group_by_time(timeseries_list)
        
        fused_forecasts = []
        for timestamp, sources in time_groups.items():
            if len(sources) < 2:
                # 소스가 하나뿐인 경우
                source = sources[0]
                # MarineDataPoint는 confidence 속성이 없으므로 timeseries에서 가져옴
                source_confidence = 0.5  # 기본값
                fused = FusedForecast(
                    location=location,
                    timestamp=timestamp,
                    wind_speed_fused=source.wind_speed,
                    wave_height_fused=source.wave_height,
                    confidence=source_confidence,
                    sources_used=[getattr(source, 'source', 'unknown')],
                    weights={getattr(source, 'source', 'unknown'): 1.0}
                )
            else:
                # 다중 소스 융합
                fused = self._fuse_multiple_sources(sources, location, timestamp)
            
            fused_forecasts.append(fused)
        
        return fused_forecasts
    
    def _group_by_time(self, timeseries_list: List[MarineTimeseries]) -> Dict[str, List]:
        """시간별로 데이터 포인트 그룹화"""
        time_groups = {}
        
        for ts in timeseries_list:
            for dp in ts.data_points:
                if dp.timestamp not in time_groups:
                    time_groups[dp.timestamp] = []
                time_groups[dp.timestamp].append(dp)
        
        return time_groups
    
    def _fuse_multiple_sources(self, sources: List, location: str, timestamp: str) -> FusedForecast:
        """다중 소스 융합 수행"""
        
        # 가중치 계산
        weights = self._calculate_weights(sources)
        
        # 가중 평균 계산
        wind_speed_fused = sum(dp.wind_speed * weights.get(getattr(dp, 'source', 'unknown'), 0.1) for dp in sources)
        wave_height_fused = sum(dp.wave_height * weights.get(getattr(dp, 'source', 'unknown'), 0.1) for dp in sources)
        
        # 신뢰도 계산 (MarineDataPoint는 confidence 속성이 없으므로 기본값 사용)
        confidence = sum(0.5 * weights.get(getattr(dp, 'source', 'unknown'), 0.1) for dp in sources)
        
        return FusedForecast(
            location=location,
            timestamp=timestamp,
            wind_speed_fused=wind_speed_fused,
            wave_height_fused=wave_height_fused,
            confidence=confidence,
            sources_used=list(weights.keys()),
            weights=weights
        )
    
    def _calculate_weights(self, sources: List) -> Dict[str, float]:
        """소스별 가중치 계산"""
        weights = {}
        
        # 기본 가중치
        base_weights = {
            'stormglass': 0.3,
            'open_meteo': 0.25,
            'worldtides': 0.15,
            'ncm_web': self.ncm_weight
        }
        
        # 실제 존재하는 소스만 사용
        total_weight = 0
        for source in sources:
            source_name = getattr(source, 'source', 'unknown')
            weight = base_weights.get(source_name, 0.1)
            weights[source_name] = weight
            total_weight += weight
        
        # 정규화
        for source_name in weights:
            weights[source_name] /= total_weight
        
        return weights

class OperationalDecisionMaker:
    """운항 판정 클래스"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.gate_go = settings.get('gate', {}).get('go', {'hs_m': 1.0, 'wind_kt': 20.0})
        self.gate_conditional = settings.get('gate', {}).get('conditional', {'hs_m': 1.2, 'wind_kt': 22.0})
        self.alert_gamma = settings.get('alert_gamma', {})
    
    def decide_and_eta(
        self, 
        fused_forecasts: List[FusedForecast],
        eri_points: List[ERIPoint]
    ) -> List[OperationalDecision]:
        """융합 예보를 기반으로 운항 판정"""
        
        decisions = []
        
        for forecast in fused_forecasts:
            # 해당 시간의 ERI 찾기
            eri_point = self._find_eri_for_time(eri_points, forecast.timestamp)
            
            # 판정 수행
            decision = self._make_decision(forecast, eri_point)
            decisions.append(decision)
        
        return decisions
    
    def _find_eri_for_time(self, eri_points: List[ERIPoint], timestamp: str) -> Optional[ERIPoint]:
        """특정 시간의 ERI 포인트 찾기"""
        for point in eri_points:
            if point.timestamp == timestamp:
                return point
        return None
    
    def _make_decision(self, forecast: FusedForecast, eri_point: Optional[ERIPoint]) -> OperationalDecision:
        """개별 판정 수행"""
        
        # 임계값 변환 (kt → m/s)
        wind_limit_go = self.gate_go['wind_kt'] * 0.514444
        wind_limit_conditional = self.gate_conditional['wind_kt'] * 0.514444
        hs_limit_go = self.gate_go['hs_m']
        hs_limit_conditional = self.gate_conditional['hs_m']
        
        # 판정 로직
        if (forecast.wind_speed_fused <= wind_limit_go and 
            forecast.wave_height_fused <= hs_limit_go):
            decision = "GO"
            reasoning = "풍속 및 파고 조건 양호"
            limiting_factor = None
        elif (forecast.wind_speed_fused <= wind_limit_conditional and 
              forecast.wave_height_fused <= hs_limit_conditional):
            decision = "CONDITIONAL"
            reasoning = "조건부 운항 가능 - 주의 필요"
            limiting_factor = self._identify_limiting_factor(forecast)
        else:
            decision = "NO-GO"
            reasoning = "풍속 또는 파고 조건 불량"
            limiting_factor = self._identify_limiting_factor(forecast)
        
        # ETA 영향 평가
        eta_impact = self._assess_eta_impact(forecast, decision)
        
        # Gamma 알림 계산
        gamma_alert = self._calculate_gamma_alert(forecast, eri_point)
        
        return OperationalDecision(
            location=forecast.location,
            timestamp=forecast.timestamp,
            decision=decision,
            reasoning=reasoning,
            limiting_factor=limiting_factor,
            eta_impact=eta_impact,
            gamma_alert=gamma_alert
        )
    
    def _identify_limiting_factor(self, forecast: FusedForecast) -> str:
        """제한 요소 식별"""
        wind_limit_conditional = self.gate_conditional['wind_kt'] * 0.514444
        hs_limit_conditional = self.gate_conditional['hs_m']
        
        if forecast.wind_speed_fused > wind_limit_conditional:
            return "High wind speed"
        elif forecast.wave_height_fused > hs_limit_conditional:
            return "High wave height"
        else:
            return "Multiple factors"
    
    def _assess_eta_impact(self, forecast: FusedForecast, decision: str) -> str:
        """ETA 영향 평가"""
        if decision == "GO":
            return "No significant impact"
        elif decision == "CONDITIONAL":
            return "Potential delay 1-2 hours"
        else:
            return "Significant delay expected"
    
    def _calculate_gamma_alert(self, forecast: FusedForecast, eri_point: Optional[ERIPoint]) -> Optional[float]:
        """Gamma 알림 계산"""
        if eri_point:
            # ERI 기반 gamma 계산
            if eri_point.eri_value > 0.7:
                return 0.3  # High seas
            elif eri_point.eri_value > 0.5:
                return 0.15  # Rough at times
            else:
                return 0.05  # Normal conditions
        
        return None
