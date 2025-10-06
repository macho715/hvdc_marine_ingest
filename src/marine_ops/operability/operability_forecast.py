from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import math, numpy as np

def percentile(a: List[float], q: float) -> float:
    if not a: return float('nan')
    return float(np.percentile(a, q))

def p_beloweq(a: List[float], thr: float) -> float:
    if not a: return float('nan')
    n = len(a)
    return sum(1 for x in a if x <= thr) / n

def gamma_from_warning(warning: Optional[str]) -> float:
    w = (warning or "").lower().strip()
    if "high seas" in w: return 0.30
    if "rough at times" in w: return 0.15
    if "fog" in w: return 0.0
    return 0.0

def route_p95(samples: List[Dict[str, float]], key: str="hs_m") -> float:
    vals = [float(s.get(key, float('nan'))) for s in samples if key in s]
    vals = [v for v in vals if not math.isnan(v)]
    if not vals: return float('nan')
    return float(np.percentile(vals, 95))

def estimate_w_off(coastal_km: float, offshore_km: float) -> float:
    total = max(1e-6, coastal_km + offshore_km)
    return float(offshore_km) / total

def fuse_hs(Hs_route_m: float, Hs_from_ADNOC_m: float, beta: float=0.80, gamma: float=0.0) -> float:
    base = max(Hs_route_m, beta * Hs_from_ADNOC_m)
    return float(base * (1.0 + gamma))

def fuse_wind(w_adnoc_kt: float, w_ncm_kt: float) -> float:
    return float(max(w_adnoc_kt, w_ncm_kt))

@dataclass
class Gate:
    hs_go: float = 1.00
    wind_go: float = 20.0
    hs_cond: float = 1.20
    wind_cond: float = 22.0

def leadtime_adjust(day_idx: int, gate: Gate) -> Gate:
    add_hs = 0.0; add_wind = 0.0
    if day_idx in (4,5): add_hs, add_wind = 0.10, -1.0
    if day_idx in (6,7): add_hs, add_wind = 0.20, -2.0
    return Gate(
        hs_go  = gate.hs_go  + add_hs,
        wind_go= gate.wind_go + add_wind,
        hs_cond= gate.hs_cond + add_hs,
        wind_cond=gate.wind_cond + add_wind
    )

def prob_go_from_ensembles(hs_ens: List[float], wind_ens: List[float], gate: Gate) -> Dict[str, float]:
    p_hs_go   = p_beloweq(hs_ens, gate.hs_go)
    p_w_go    = p_beloweq(wind_ens, gate.wind_go)
    p_hs_cond = p_beloweq(hs_ens, gate.hs_cond)
    p_w_cond  = p_beloweq(wind_ens, gate.wind_cond)
    p_go   = p_hs_go * p_w_go
    p_cond = max(0.0, min(1.0, p_hs_cond * p_w_cond - p_go))
    p_nogo = max(0.0, 1.0 - (p_go + p_cond))
    return {"P_go": float(p_go), "P_cond": float(p_cond), "P_nogo": float(p_nogo)}

DAYPARTS = { "dawn": (3,6), "morning": (6,12), "afternoon": (12,17), "evening": (17,22) }

def aggregate_daypart(probs_by_hour: Dict[int, Dict[str,float]], mode: str="min") -> Dict[str, Dict[str,float]]:
    out = {}
    for name, (h1,h2) in DAYPARTS.items():
        hours = [h for h in probs_by_hour if h1 <= h < h2]
        if not hours:
            out[name] = {"P_go": float('nan'), "P_cond": float('nan'), "P_nogo": float('nan')}
            continue
        vec = {"P_go": [], "P_cond": [], "P_nogo": []}
        for h in hours:
            for k in vec: vec[k].append(probs_by_hour[h][k])
        if mode == "min":
            agg = {k: float(min(vec[k])) for k in vec}
        else:
            agg = {k: float(sum(vec[k])/len(vec[k])) for k in vec}
        out[name] = agg
    return out

def speed_effective(plan_kt: float, hs_m: float) -> float:
    dv = 0.60 * max(0.0, hs_m)
    return max(2.0, plan_kt - dv)

def eta_hours(distance_nm: float, v_eff_kt: float, buffer_min: int=45) -> float:
    sail = distance_nm / max(0.1, v_eff_kt)
    return round(sail + buffer_min/60.0, 2)

def operability_for_day(day_idx: int, hs_ens_by_hour: Dict[int, List[float]], wind_ens_by_hour: Dict[int, List[float]], base_gate: Gate) -> Dict:
    gate = leadtime_adjust(day_idx, base_gate)
    probs_by_hour = {}
    for hour, hs_ens in hs_ens_by_hour.items():
        wind_ens = wind_ens_by_hour.get(hour, [])
        probs_by_hour[hour] = prob_go_from_ensembles(hs_ens, wind_ens, gate)
    dayparts = aggregate_daypart(probs_by_hour, mode="min")
    return {"gate": gate.__dict__, "by_hour": probs_by_hour, "by_daypart": dayparts}

def decision_from_probs(p: Dict[str,float]) -> str:
    lab = max(p.items(), key=lambda kv: kv[1])[0]
    return {"P_go":"GO", "P_cond":"CONDITIONAL", "P_nogo":"NO-GO"}[lab]
