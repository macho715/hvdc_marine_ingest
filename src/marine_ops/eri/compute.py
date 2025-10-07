# KR: ERI (Environmental Risk Index) 계산
# EN: Environmental Risk Index computation

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from src.marine_ops.core.schema import ERIPoint, MarineTimeseries

DEFAULT_ERI_RULES: Dict[str, Any] = {
    "wind": {
        "thresholds": [10, 15, 20, 25],
        "weights": [0.2, 0.4, 0.7, 1.0],
    },
    "wave": {
        "thresholds": [1.0, 1.5, 2.0, 2.5],
        "weights": [0.2, 0.4, 0.7, 1.0],
    },
    "swell": {
        "thresholds": [0.5, 1.0, 1.5, 2.0],
        "weights": [0.1, 0.3, 0.6, 1.0],
    },
    "wind_wave": {
        "thresholds": [0.5, 1.0, 1.5, 2.0],
        "weights": [0.1, 0.3, 0.6, 1.0],
    },
    "ocean_current": {
        "thresholds": [0.5, 1.0, 1.5, 2.0],
        "weights": [0.1, 0.3, 0.6, 1.0],
    },
    "visibility": {
        "thresholds": [10, 5, 2, 1],
        "weights": [0.1, 0.3, 0.6, 1.0],
    },
    "fog": {
        "thresholds": [0.1, 0.3, 0.5, 0.7],
        "weights": [0.2, 0.4, 0.7, 1.0],
    },
    "sea_surface_temp": {
        "thresholds": [20, 25, 30, 35],
        "weights": [0.1, 0.2, 0.3, 0.5],
    },
}


class ERICalculator:
    """ERI 계산기"""

    def __init__(self, rules_file: str = "config/eri_rules.yaml"):
        self.rules_file = Path(rules_file)
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """ERI 규칙 로드 / Load ERI rules."""
        merged_rules = deepcopy(DEFAULT_ERI_RULES)

        if self.rules_file.exists():
            with open(self.rules_file, "r", encoding="utf-8") as f:
                file_rules = yaml.safe_load(f) or {}
                merged_rules = self._merge_rules(merged_rules, file_rules)

        return merged_rules

    def _merge_rules(
        self, base: Dict[str, Any], overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ERI 규칙 병합 / Merge ERI rule dictionaries."""
        for key, value in overrides.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = self._merge_rules(base[key], value)
            else:
                base[key] = value
        return base

    def compute_eri_timeseries(self, timeseries: MarineTimeseries) -> List[ERIPoint]:
        """시계열 데이터에 대한 ERI 계산"""
        eri_points = []

        for data_point in timeseries.data_points:
            # 각 요소별 위험도 계산
            wind_risk = self._calculate_wind_risk(data_point.wind_speed)
            wave_risk = self._calculate_wave_risk(data_point.wave_height)
            visibility_risk = self._calculate_visibility_risk(data_point.visibility)
            fog_risk = self._calculate_fog_risk(data_point.fog_probability)

            # 가중 평균으로 전체 ERI 계산 (확장된 변수 포함)
            total_eri = (
                wind_risk * 0.3  # 풍속 30%
                + wave_risk * 0.25  # 파고 25%
                + self._calculate_swell_risk(data_point.swell_wave_height)
                * 0.15  # 스웰 15%
                + self._calculate_wind_wave_risk(data_point.wind_wave_height)
                * 0.1  # 바람파 10%
                + self._calculate_ocean_current_risk(data_point.ocean_current_speed)
                * 0.05  # 해류 5%
                + visibility_risk * 0.1  # 시정 10%
                + fog_risk * 0.05  # 안개 5%
            )

            eri_point = ERIPoint(
                timestamp=data_point.timestamp,
                eri_value=total_eri,
                wind_contribution=wind_risk,
                wave_contribution=wave_risk,
                visibility_contribution=visibility_risk,
                fog_contribution=fog_risk,
            )
            eri_points.append(eri_point)

        return eri_points

    def _calculate_wind_risk(self, wind_speed: float) -> float:
        """풍속 위험도 계산"""
        thresholds = self.rules["wind"]["thresholds"]
        weights = self.rules["wind"]["weights"]

        if wind_speed < thresholds[0]:
            return weights[0]
        elif wind_speed < thresholds[1]:
            return weights[1]
        elif wind_speed < thresholds[2]:
            return weights[2]
        elif wind_speed < thresholds[3]:
            return weights[3]
        else:
            return 1.0  # 최대 위험

    def _calculate_wave_risk(self, wave_height: float) -> float:
        """파고 위험도 계산"""
        thresholds = self.rules["wave"]["thresholds"]
        weights = self.rules["wave"]["weights"]

        if wave_height < thresholds[0]:
            return weights[0]
        elif wave_height < thresholds[1]:
            return weights[1]
        elif wave_height < thresholds[2]:
            return weights[2]
        elif wave_height < thresholds[3]:
            return weights[3]
        else:
            return 1.0  # 최대 위험

    def _calculate_visibility_risk(self, visibility: float) -> float:
        """시정 위험도 계산"""
        if visibility is None:
            return 0.5  # 중간 위험 (데이터 없음)

        thresholds = self.rules["visibility"]["thresholds"]
        weights = self.rules["visibility"]["weights"]

        if visibility > thresholds[0]:
            return weights[0]
        elif visibility > thresholds[1]:
            return weights[1]
        elif visibility > thresholds[2]:
            return weights[2]
        elif visibility > thresholds[3]:
            return weights[3]
        else:
            return 1.0  # 최대 위험

    def _calculate_fog_risk(self, fog_probability: float) -> float:
        """안개 위험도 계산"""
        if fog_probability is None:
            return 0.1  # 낮은 위험 (데이터 없음)

        thresholds = self.rules["fog"]["thresholds"]
        weights = self.rules["fog"]["weights"]

        if fog_probability < thresholds[0]:
            return weights[0]
        elif fog_probability < thresholds[1]:
            return weights[1]
        elif fog_probability < thresholds[2]:
            return weights[2]
        elif fog_probability < thresholds[3]:
            return weights[3]
        else:
            return 1.0  # 최대 위험

    def _calculate_swell_risk(self, swell_height: float) -> float:
        """스웰 파고 위험도 계산"""
        if swell_height is None:
            return 0.1  # 낮은 위험 (데이터 없음)

        thresholds = self.rules["swell"]["thresholds"]
        weights = self.rules["swell"]["weights"]

        if swell_height < thresholds[0]:
            return weights[0]
        elif swell_height < thresholds[1]:
            return weights[1]
        elif swell_height < thresholds[2]:
            return weights[2]
        elif swell_height < thresholds[3]:
            return weights[3]
        else:
            return 1.0  # 최대 위험

    def _calculate_wind_wave_risk(self, wind_wave_height: float) -> float:
        """바람파 위험도 계산"""
        if wind_wave_height is None:
            return 0.1  # 낮은 위험 (데이터 없음)

        thresholds = self.rules["wind_wave"]["thresholds"]
        weights = self.rules["wind_wave"]["weights"]

        if wind_wave_height < thresholds[0]:
            return weights[0]
        elif wind_wave_height < thresholds[1]:
            return weights[1]
        elif wind_wave_height < thresholds[2]:
            return weights[2]
        elif wind_wave_height < thresholds[3]:
            return weights[3]
        else:
            return 1.0  # 최대 위험

    def _calculate_ocean_current_risk(self, current_speed: float) -> float:
        """해류 속도 위험도 계산"""
        if current_speed is None:
            return 0.1  # 낮은 위험 (데이터 없음)

        thresholds = self.rules["ocean_current"]["thresholds"]
        weights = self.rules["ocean_current"]["weights"]

        if current_speed < thresholds[0]:
            return weights[0]
        elif current_speed < thresholds[1]:
            return weights[1]
        elif current_speed < thresholds[2]:
            return weights[2]
        elif current_speed < thresholds[3]:
            return weights[3]
        else:
            return 1.0  # 최대 위험


def compute_eri_for_ncm(
    timeseries: MarineTimeseries, ncm_discount: float = 0.8
) -> List[ERIPoint]:
    """NCM 데이터에 대한 특별 ERI 계산 (할인 적용)"""
    calculator = ERICalculator()
    eri_points = calculator.compute_eri_timeseries(timeseries)

    # NCM 데이터는 신뢰도가 낮으므로 위험도를 할인
    for point in eri_points:
        point.eri_value *= ncm_discount
        point.wind_contribution *= ncm_discount
        point.wave_contribution *= ncm_discount
        point.visibility_contribution *= ncm_discount
        point.fog_contribution *= ncm_discount

    return eri_points


def save_eri_timeseries(location: str, eri_points: List[ERIPoint]) -> None:
    """ERI 시계열을 JSON 파일로 저장"""
    output_dir = Path("out")
    output_dir.mkdir(exist_ok=True)

    filename = f"eri_{location}.json"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "timestamp": point.timestamp,
                    "eri_value": point.eri_value,
                    "wind_contribution": point.wind_contribution,
                    "wave_contribution": point.wave_contribution,
                    "visibility_contribution": point.visibility_contribution,
                    "fog_contribution": point.fog_contribution,
                }
                for point in eri_points
            ],
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"ERI 데이터 저장됨: {output_path}")
