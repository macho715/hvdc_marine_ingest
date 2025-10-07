"""ERI helpers for the 72-hour pipeline."""
from __future__ import annotations

from typing import Dict, List

from src.marine_ops.core.schema import ERIPoint, MarineTimeseries
from src.marine_ops.eri.compute import ERICalculator


def compute_eri_3d(timeseries_map: Dict[str, MarineTimeseries]) -> Dict[str, List[ERIPoint]]:
    calculator = ERICalculator()
    results: Dict[str, List[ERIPoint]] = {}
    for location, timeseries in timeseries_map.items():
        try:
            results[location] = calculator.compute_eri_timeseries(timeseries)
        except Exception:  # pragma: no cover - robustness guard
            results[location] = []
    return results
