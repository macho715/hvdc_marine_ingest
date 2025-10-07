"""Operational ETA/ETD impact modelling based on wave and wind modifiers."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional

DEG = math.pi / 180.0
KT2MS = 0.514444


@dataclass
class VesselProfile:
    """Static vessel characteristics used by the impact model."""

    name: str = "Generic-SV"
    v_hull_kn: float = 12.0
    G_ref_kt: float = 30.0
    phi_min: float = 0.20
    alpha: float = 0.28
    p: float = 1.30
    S0: float = 0.025
    r: float = 0.50
    beta: float = 0.12
    q: float = 2.0
    min_mult: float = 0.55


@dataclass
class LegInput:
    """Environmental inputs describing a voyage leg."""

    distance_nm: float
    course_deg: float
    hs_m: float
    tp_s: float
    swell_dir_deg: float
    gust_kt: float
    wind_dir_deg: float
    gamma_alert: float = 0.0
    notes: Optional[str] = None


@dataclass
class ImpactResult:
    """Computed effective speed, ETA and delay information."""

    v_eff_kn: float
    eta_hours: float
    delay_minutes: float
    multipliers: Dict[str, float]
    dir_weights: Dict[str, float]


def _dir_weight(delta_deg: float, phi_min: float) -> float:
    delta = abs(delta_deg) % 360.0
    if delta > 180.0:
        delta = 360.0 - delta
    return phi_min + (1.0 - phi_min) * (1.0 - math.cos(delta * DEG)) * 0.5


def _steepness(hs: float, tp: float, S0: float) -> float:
    L = max(9.81 * tp * tp / (2.0 * math.pi), 1e-6)
    S = min(0.09, max(1e-6, hs / L))
    return max(0.5, (S / S0) ** 0.5)


def _wave_multiplier(leg: LegInput, vessel: VesselProfile) -> float:
    dir_factor = _dir_weight(leg.swell_dir_deg - leg.course_deg, vessel.phi_min)
    steepness = _steepness(leg.hs_m, leg.tp_s, vessel.S0)
    penalty = vessel.alpha * (leg.hs_m ** vessel.p) * dir_factor * steepness * (1.0 + leg.gamma_alert)
    return max(vessel.min_mult, math.exp(-penalty))


def _gust_multiplier(leg: LegInput, vessel: VesselProfile) -> float:
    rel = max(0.0, math.cos((leg.wind_dir_deg - leg.course_deg) * DEG))
    scaled = max(0.0, leg.gust_kt) / max(1e-6, vessel.G_ref_kt)
    penalty = vessel.beta * (scaled ** vessel.q) * rel
    return max(vessel.min_mult, math.exp(-penalty))


def compute_operational_impact(leg: LegInput, vessel: VesselProfile) -> ImpactResult:
    wave_multiplier = _wave_multiplier(leg, vessel)
    gust_multiplier = _gust_multiplier(leg, vessel)
    total_multiplier = max(vessel.min_mult, wave_multiplier * gust_multiplier)

    v_eff = max(0.1, vessel.v_hull_kn * total_multiplier)
    eta_hours = leg.distance_nm / v_eff
    baseline_eta = leg.distance_nm / max(0.1, vessel.v_hull_kn)
    delay_minutes = max(0.0, (eta_hours - baseline_eta) * 60.0)

    return ImpactResult(
        v_eff_kn=v_eff,
        eta_hours=eta_hours,
        delay_minutes=delay_minutes,
        multipliers={
            "wave": wave_multiplier,
            "gust": gust_multiplier,
            "total": total_multiplier,
        },
        dir_weights={
            "swell": _dir_weight(leg.swell_dir_deg - leg.course_deg, vessel.phi_min),
            "wind": max(0.0, math.cos((leg.wind_dir_deg - leg.course_deg) * DEG)),
        },
    )
