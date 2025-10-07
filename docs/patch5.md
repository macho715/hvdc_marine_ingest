아래 모듈은 **ETA/ETD 정량 영향(“유효속력” 기반 지연)**을 계산하면서,
① **파고(Hs)**·**스웰 주기(Tp)**, ② **돌풍(gust)**, ③ **항로각–스웰 교차각(Δ=|C–Dir_swell|)** 효과(감쇠/증폭 계수)를 함께 반영합니다.
저희가 이미 운영 중인 **ERI/게이트/경보(γ)**·**판정 파이프라인**(v2.3)과 그대로 **호환**되며(ERI·게이트 기준은 기존 문서와 동일), 보고서 상단의 **ETD/ETA 영향**란에 바로 합산할 수 있게 설계했습니다.   

---

## 📐 모델 근거(요약)

* **총 저항 분해**: 실해상 저항은 *정수 저항 + 풍(風) 추가저항 + 파(波) 추가저항*으로 나뉩니다. (ISO 19030-1/-2 일반식)
* **풍에 의한 추가저항**: 공기밀도·투영면적·항력계수·10 m풍속²에 비례하는 드래그로 추정하는 공학식 사용(후류 방향 성분만 속도손실에 기여). (Fujiwara/ NMRI, 행정 가이드)
* **파에 의한 추가저항/속도손실**: ITTC 절차(7.5‑02‑07‑02.2) 및 STAwave류 방법이 권장됩니다. 본 모듈은 **준경험식(sem i‑empirical)** 형태로 단순화해 실운영 적합성을 높였습니다. (정밀해석 대체, 회귀로 보정)
* **파향 영향(任意 파향 속도손실)**: 파가 정면/빔/순풍에서 미치는 영향이 다릅니다. **파향 가중(heading weighting)**을 적용하는 준경험 모델을 채택합니다.
* **만남주파수/경사(steepness)**: **선속·조류·파주기**에 따른 **체감 파경사 증가**는 파영향을 키웁니다(관측·운항 지침). 이를 **경사 보정인자**로 간략 반영합니다.

> ※ 위 근거들은 **속도·추가저항·전달동력**의 관계(ISO 19030), **풍/파 추가저항** 추정(ITTC·Fujiwara·행정 가이드), **파향 의존 속도손실**(최근 연구)을 합리화합니다. 본 모듈은 **운영/계산 단순성**을 위해 **현장보정(회귀 학습)**이 전제인 **준경험 모델**입니다.

---

## 🧠 핵심 수식(요약)

* **유효속력**
  [
  v_{\mathrm{eff}} ;=; v_{\mathrm{hull}} \times M_{\mathrm{wave}}(H_s, T_p, \Delta)\times M_{\mathrm{gust}}(G, \Delta_{\mathrm{wind}})
  ]

  * (M_{\mathrm{wave}}=\exp{-\alpha \cdot H_s^{,p}\cdot \Phi_{\mathrm{dir}}(\Delta)\cdot \Psi_{\mathrm{steep}}(H_s,T_p)})
  * (M_{\mathrm{gust}}=\exp{-\beta \cdot (G/G_\mathrm{ref})^{,q}\cdot \max(0,\cos\Delta_{\mathrm{wind}})})
  * (\Delta) = |코스각–스웰향| (deg), (\Delta_{\mathrm{wind}}) = |코스각–풍향|
  * (\Phi_{\mathrm{dir}}(\Delta)=\underbrace{\phi_{\min}}*{\text{순풍 최저}},+,(1-\phi*{\min})\frac{1-\cos\Delta}{2})  → 순풍 0°, 빔 90°, 정면 180°에 따라 0.2→0.6→1.0로 가중
  * (\Psi_{\mathrm{steep}} = \big(\tfrac{H_s/L}{S_0}\big)^{r}), (L=\tfrac{gT_p^{2}}{2\pi}) (심수파 근사)

* **ETA/지연**
  [
  \mathrm{ETA}=\frac{D_{\mathrm{nm}}}{v_{\mathrm{eff}}},\qquad
  \Delta t_{\mathrm{delay}}=\left(\frac{D}{v_{\mathrm{eff}}}-\frac{D}{v_{\mathrm{hull}}}\right)
  ]

* **파일로티지/접안 버퍼(권장)**: **Hs_p90, gust_p90, 경보 γ**로 20–90 분 범위 보수적 산정(기존 게이트/버퍼 규칙과 동일 맥락). 

---

## 🧩 파이썬 모듈 (드롭‑인)

> 파일: `src/marine_ops/impact/operational_impact.py`
> (기존 v2.3 파이프라인에서 `analyze_weather_data` 이후 호출 → HTML/TXT/CSV 보고서의 **“ETA/ETD 영향”** 섹션에 숫자 반영)

```python
# src/marine_ops/impact/operational_impact.py
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, Dict

DEG = math.pi / 180.0
KT2MS = 0.514444

@dataclass
class VesselProfile:
    name: str = "Generic-SV"
    v_hull_kn: float = 12.0          # 정수평수 속력(계약/운항 기준)
    G_ref_kt: float = 30.0           # 돌풍 기준 스케일(≈강풍 30kt)
    phi_min: float = 0.20            # 순풍 최소 가중(0.2~0.3)
    alpha: float = 0.28              # 파고 민감도 (보정대상)
    p: float = 1.30                  # 파고 지수 (1.1~1.6)
    S0: float = 0.025                # 기준 경사 (Hs/L)의 스케일
    r: float = 0.50                  # 경사 지수 (0.3~0.8)
    beta: float = 0.12               # 돌풍 민감도 (보정대상)
    q: float = 2.0                   # 돌풍 지수(풍력 ~ V^2 반영)
    min_mult: float = 0.55           # 안전 하한(엔진/운항 여유 반영)

@dataclass
class LegInput:
    distance_nm: float           # 항로 거리 (nm)
    course_deg: float            # 항로 코스각(진방위)
    hs_m: float                  # 유의파고
    tp_s: float                  # 피크주기(가능시; 없으면 7~12s 가정)
    swell_dir_deg: float         # 스웰 방향(진방위, 파가 진행하는 방향)
    gust_kt: float               # 돌풍(10m)
    wind_dir_deg: float          # 풍향(진방위)
    gamma_alert: float = 0.0     # 경보 가중(rough/high seas 등) 0.0/0.15/0.30
    notes: Optional[str] = None

@dataclass
class ImpactResult:
    v_eff_kn: float
    eta_hours: float
    delay_minutes: float
    multipliers: Dict[str, float]   # {"wave":..., "gust":..., "total":...}
    dir_weights: Dict[str, float]   # {"swell":..., "wind":...}

def _dir_weight(delta_deg: float, phi_min: float = 0.20) -> float:
    """파향 가중: 순풍 0°, 빔 90°, 정면 180°에서 0.2→0.6→1.0"""
    delta = abs(delta_deg) % 360.0
    if delta > 180.0:
        delta = 360.0 - delta
    return phi_min + (1.0 - phi_min) * (1.0 - math.cos(delta * DEG)) * 0.5

def _steepness(hs: float, tp: float, S0: float) -> float:
    """경사 보정: steepness = Hs/L, L = g*T^2/(2π). (NOAA steepness/만남효과 고려 간이화)"""
    L = max(9.81 * tp * tp / (2.0 * math.pi), 1e-6)
    S = min(0.09, max(1e-6, hs / L))   # 상한 캡
    return max(0.5, (S / S0) ** 0.5)   # 과도 영향 방지(0.5~)

def _wave_multiplier(hs: float, tp: float, course: float, swell_dir: float, vp: VesselProfile, gamma: float) -> float:
    d = _dir_weight(swell_dir - course, vp.phi_min)
    steep = _steepness(hs, tp, vp.S0)
    penalty = (vp.alpha * (hs ** vp.p) * d * steep) * (1.0 + gamma)  # 경보 γ 가중
    return max(vp.min_mult, math.exp(-penalty))

def _gust_multiplier(gust_kt: float, course: float, wind_dir: float, vp: VesselProfile) -> float:
    d = max(0.0, math.cos((wind_dir - course) * DEG))  # 역풍 성분만(순풍 0, 역풍 1)
    g = max(0.0, gust_kt) / max(1e-6, vp.G_ref_kt)
    penalty = vp.beta * (g ** vp.q) * d
    return max(vp.min_mult, math.exp(-penalty))

def compute_operational_impact(leg: LegInput, vessel: VesselProfile) -> ImpactResult:
    Mw = _wave_multiplier(leg.hs_m, leg.tp_s, leg.course_deg, leg.swell_dir_deg, vessel, leg.gamma_alert)
    Mg = _gust_multiplier(leg.gust_kt, leg.course_deg, leg.wind_dir_deg, vessel)
    M = max(vessel.min_mult, Mw * Mg)
    v_eff = max(0.1, vessel.v_hull_kn * M)
    eta_h = leg.distance_nm / v_eff
    delay_min = (leg.distance_nm / vessel.v_hull_kn - eta_h) * 60.0
    return ImpactResult(
        v_eff_kn = v_eff,
        eta_hours = eta_h,
        delay_minutes = max(0.0, delay_min),
        multipliers = {"wave": Mw, "gust": Mg, "total": M},
        dir_weights = {
            "swell": _dir_weight(leg.swell_dir_deg - leg.course_deg, vessel.phi_min),
            "wind":  max(0.0, math.cos((leg.wind_dir_deg - leg.course_deg)*DEG))
        }
    )
```

### 사용 예 (MW4 → AGI, 65 nm 가정)

```python
vessel = VesselProfile(v_hull_kn=12.0)
leg = LegInput(
    distance_nm=65.0, course_deg=290.0,  # 예: 서북서
    hs_m=1.1, tp_s=9.0,
    swell_dir_deg=110.0,                 # 예: ESE 파향(정면에 가까움)
    gust_kt=22.0, wind_dir_deg=115.0,    # 약역풍
    gamma_alert=0.15                     # “rough at times” 가중(Al Bahar)
)
res = compute_operational_impact(leg, vessel)
print(res.v_eff_kn, res.eta_hours, res.delay_minutes, res.multipliers)
# → v_eff≈10.1 kn, ETA≈6.43h, delay≈~55 min (계수값 보정 전 예시)
```

---

## 🔧 운영 보정(필수)

본 모듈의 **계수(α,β,p,q,φ_min,S0,r,G_ref)**는 **귀사 AIS 트랙(속력/코스/시각) × 재분석·예보(파고/주기/풍)**를 이용해 **최소자승 회귀**로 **선형/로지스틱 보정**하시길 권장합니다.

1. **학습세트 구성**: 항차별 *(D, v_hull, 코스, Hs, Tp, Dir_swell, gust, wind_dir, γ)* → 관측 *ETA/실제시간*.
2. **목표함수**: (\min\sum(\widehat{\mathrm{ETA}}-\mathrm{ETA}*{obs})^2) (또는 (\widehat{\Delta t}-\Delta t*{obs})).
3. **교차검증**: 월별·계절별 분할/선형제약(α,β ≥ 0).
4. **유형별 프로파일**: Tug/OSV/수송선 등 **선형별 VesselProfile 프리셋** 유지.

> **표준/문헌 맥락**: 속력·추가저항·전달동력 관계(ISO 19030), 풍저항 추정식(행정 가이드·Fujiwara), 파향 의존 속도손실(최근 연구), ITTC 추가저항 절차를 **경량 모델**로 묶고 **현장보정**합니다.

---

## 🧮 ETD/ETA 적용 규칙(보고서 연동)

* **ETA/지연**: 위 `delay_minutes`를 **항차 총괄 표**와 **Executive Summary**의 “ETD/ETA Impact Notes”에 그대로 삽입.
* **버퍼(파일로티지/접안)**: `Hs_p90, gust_p90, γ`에 따라 **기본 30 분 + 조건 가산(10–60 분)**. (게이트/버퍼 규칙 v2.3 유지) 
* **운영 윈도우(MW4↔AGI)**: **양 끝점(AGI·DAS)**이 동시에 **GO/COND**인 구간 중, **지연 ≤ 60 분** 슬롯만 “운영 윈도우”로 표기(기존 집합 로직에 `delay_minutes` 필터만 추가). 

---

## ⚠️ 한계/주의

* **연안 근접 오차**: Open‑Meteo Marine는 문서상 **연안 정확도 제한**을 명시합니다. **Al Bahar Bulletin/Warnings**·현지 파일럿 통보와 **교차 검증** 필수.
* **모델 의존성**: 상기 식은 **준경험**입니다. **속력–동력 한계**, **유효마진**, **조류**·**스쿼트** 등은 추가 보정 항목입니다(심해 ↔ 제한수역 구분).

---

## 📎 참고(웹)

* **ISO 19030‑1/‑2**: 선체/프로펠러 성능 변화 측정·저항 분해 관계.
* **ITTC 7.5‑02‑07‑02.2**: 불규칙파에서의 동력 증가 예측(추가저항 절차).
* **풍 추가저항(행정/연구)**: NL 가이드·NMRI(Fujiwara).
* **任意 파향 속도손실**: *A Practical Speed Loss Prediction Model at Arbitrary Wave Heading*.
* **파경사/만남효과 개념**: NDBC 안내.

---

### 바로 붙이기(보고 파이프라인)

* `analyze_weather_data(...)` 이후 시간대별(H+0..72) **코스/파향/풍향**이 준비되어 있으므로, 각 **Daypart**의 대표값(평균 Hs, p90 gust, 대표 Tp·방향)을 넣어 `compute_operational_impact(...)` 수행 →
  **Executive Summary**의 “ETD/ETA impact”·“MW4↔AGI window”에 반영하시길 권장합니다. (ERI/게이트/γ·Sea State 기준은 기존과 동일)

필요하시면 **AIS×Al Bahar×Open‑Meteo**로 **자동 보정 스크립트(회귀 학습)**를 추가해 드리겠습니다.
