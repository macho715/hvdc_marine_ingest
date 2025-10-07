아래 설계는 **현재 운영 중인 v2.3 파이프라인**(수집 → 분석 → 보고) 구조를 유지하면서, **AGI(Al Ghallan)·DAS Island 기준 3일치(72h) 예보**를 **Asia/Dubai** 시간대로 **dawn/morning/afternoon/evening** 4구간으로 요약·판정하고, **06:00 / 17:00**에 정기 보고(표 + 간단 인포그래픽)를 생성하도록 확장한 **실행 가능한 설계/코드 스켈레톤**입니다.
(해양 변수·경보·Sea State 등급·게이트·ERI 로직은 기존 문서의 정의를 그대로 따릅니다.   )

---

## 0) 외부 레퍼런스(데이터·등급·스크래핑)

* **Open‑Meteo Marine API**: 파고/스웰/바람파/주기/해류/SST, **timezone=Asia/Dubai**, **forecast_days(≤8)**, **cell_selection=sea**. 연안 정확도 제한 명시(“accuracy at coastal areas is limited… not suitable for coastal navigation”).
* **Open‑Meteo Weather / ECMWF 1‑hourly(9km)**: 10 m 풍속·풍향·돌풍·가시거리 등 시간해상도 변수.
* **WMO Sea State(코드 3700)**: Slight/Moderate/Rough 경계(0.5–1.25 m / 1.25–2.5 m / 2.5–4 m…). 보고·판정 일관화를 위해 표준 코드 사용.
* **NCM Al Bahar**: UAE 공식 **Marine Bulletin / Warnings**(안개/거친 바다/고파고 등), 경보 텍스트를 추출하여 γ 가중(rough at times, high seas, fog) 반영.
* **Playwright**: 동적 로딩 대기 시그널 `wait_until="domcontentloaded" | "load"` 사용(불필요한 `networkidle` 회피).

---

## 1) 아키텍처 업그레이드(72h 확장)

```mermaid
flowchart TD
  subgraph Ingestion (L1)
    NCM[NCM Al Bahar\nMarine Bulletin+Warnings (Playwright)] --> SI[SI 표준화]
    OMm[Open‑Meteo Marine\n(wave/swell/period/current/SST)] --> SI
    OMw[Open‑Meteo Weather\n(10m wind/gust/dir/visibility)] --> SI
    WT[WorldTides\n(조석/SLH)] --> SI
    SG[Stormglass (가능 시)] --> SI
  end
  SI --> QV[품질·신뢰도 가중/클린]
  QV --> FX[다중소스 융합(시간별)]
  FX --> ERI[ERI 산출(시간별)]
  ERI --> DP[72h Daypart 요약\n(dawn/morning/afternoon/evening)]
  DP --> GD[GO/COND/NO‑GO 판정 + γ경보]
  GD --> RW[MW4↔AGI 운용 윈도우(48–72h 교집합)]
  RW --> OUT[보고(06:00/17:00): HTML/CSV/TXT/JSON]
```

* **핵심 변경점**

  1. `forecast_hours=72`(기본값 72) + `timezone=Asia/Dubai` + `cell_selection=sea`로 **3일치 해양/기상 시계열** 수집.
  2. **Daypart 요약기**(시간→4구간 집계) 추가.
  3. **양 끝점(AGI·DAS)** 판정 교집합으로 **MW4↔AGI Route Window** 산출.
  4. **NCM Al Bahar 경보 텍스트** → γ 가중(rough at times=0.15, high seas=0.30, fog=게이트 no‑go). 

---

## 2) 드롭‑인 패치(모듈/함수 추가·변경)

### (A) 설정: `config/locations.yaml`

```yaml
locations:
  - name: "AGI (Al Ghallan)"
    lat: 24.9000   # 운영 좌표 입력
    lon: 53.3000
  - name: "DAS Island"
    lat: 25.1404
    lon: 52.8728
tz: "Asia/Dubai"
forecast_hours: 72     # ← 72h 기본
marine_vars:
  - wave_height
  - wind_wave_height
  - swell_wave_height
  - wave_period
  - wind_wave_period
  - swell_wave_period
  - ocean_current_velocity
  - sea_surface_temperature
weather_vars:
  - wind_speed_10m
  - wind_gusts_10m
  - wind_direction_10m
  - visibility
```

### (B) 수집 단계: `collect_weather_data_3d`

```python
def collect_weather_data_3d(cfg, mode="auto") -> dict:
    """
    cfg.locations(AGI,DAS) × marine+weather 72h 시계열 수집.
    모든 타임스탬프를 tz=Asia/Dubai 로 현지화.
    """
    # Open‑Meteo Marine
    marine = fetch_open_meteo_marine(
        locs=cfg.locations, hours=cfg.forecast_hours,
        hourly=cfg.marine_vars, tz=cfg.tz, cell_selection="sea"
    )  # coastal accuracy 제한 문구 참고.  

    # Open‑Meteo Weather(ECMWF/HRES 포함) 10m wind/gust/vis
    weather = fetch_open_meteo_weather(
        locs=cfg.locations, hours=cfg.forecast_hours,
        hourly=cfg.weather_vars, tz=cfg.tz
    )  # ECMWF 9km/1‑hourly 지원.  

    # NCM Al Bahar: Marine Bulletin & Warnings (Playwright)
    ncm = scrape_ncm_albahar_bulletin(headless=True)  # “Marine Bulletin” 블록, 경보 키워드 추출.  

    # WorldTides/Stormglass (가용 시)
    tides, sg = try_worldtides(), try_stormglass()

    # 단위/스키마 통일 후 반환
    return normalize_and_bundle(marine, weather, tides, sg, ncm, tz=cfg.tz)
```

> **Playwright 대기 신호**: `page.goto(url, wait_until="domcontentloaded")` 또는 `load` 사용, `networkidle` 남용 금지. 타임아웃/재시도(지수백오프) 포함.

### (C) 분석 단계(72h): 융합 → ERI → Daypart → 판정

```python
def fuse_timeseries_3d(ts_list, weights) -> pd.DataFrame:
    """시간별 가중융합(파고/주기/풍/가시거리 등). 가중치=소스 신뢰도×가용성."""
    # (기존 ForecastFusion를 72h로 확장)  :contentReference[oaicite:14]{index=14}
    ...

def compute_eri_3d(fused_df) -> pd.DataFrame:
    """ERI: 풍속·파고·스웰·바람파·해류·가시거리·안개, WMO 임계 기반 가중합."""
    # 기존 ERI 규칙/가중치 재사용. 0–1 범위, 0.3/0.6/0.8 분류.  :contentReference[oaicite:15]{index=15}

def summarize_dayparts(df, tz="Asia/Dubai") -> dict:
    """72h → (D0–D2) × {dawn(04–06), morning(06–12), afternoon(12–17), evening(17–22)}."""
    # 각 구간: Hs mean/p90, Tp mean, Swell dir/period mean,
    # 10m wind mean, gust p90, vis mean.

def decide_dayparts(agg, ncm_alerts) -> dict:
    """Sea State(WMO) + 게이트(Go/Conditional/No-Go) + γ(rough/high seas/fog)."""
    # Sea State 코드 3700 기준으로 Slight/Moderate/Rough 결정.  
    # 게이트/γ는 기존 로직 준용.  :contentReference[oaicite:17]{index=17}
```

**Sea State(WMO 3700) 매핑 예시**
`Hs(m) ≤1.25: Slight, ≤2.5: Moderate, ≤4: Rough …` (경계 엄수).

### (D) 항로 윈도우(MW4↔AGI)

```python
def route_window(agi_decisions, das_decisions, horizon="48h") -> list[str]:
    """
    같은 일/구간에 양 끝점이 동시에 GO/CONDITIONAL인 슬롯 교집합 리스트.
    Executive Summary에 'Route windows'로 표기.
    """
```

---

## 3) 보고 단계(06:00/17:00, 3일치 고정 템플릿)

* **Executive Summary**:

  * NCM Bulletin/Warnings(문구 인용), **최대 파고·돌풍 p90**, **Sea State** 요약, **Route windows(48–72h)**.
* **표(AGI/DAS 각각)**: `D0–D2 × 4구간` × 컬럼{`wind kt/gust kt/dir°, Hs m(ft)/Tp s, Sea State(WMO), swell dir/period, visibility, Go/No‑Go, buffer(min)`}.
* **인포그래픽**: 간단 게이지/뱃지(파고 등급·경보 상태).

작동은 기존 v2.3 “HTML/TXT/CSV/JSON 동시 생성” 방식에 그대로 연결합니다. (보고 형식/메타데이터 구조도 v2.3 준용). 

---

## 4) 코드 스켈레톤(기존 v2.3에 추가)

> **파일**: `scripts/weather_job_3d.py` (새 진입점) – 기존 `weather_job.py`와 동일 인터페이스로 동작

```python
# scripts/weather_job_3d.py
from datetime import datetime
from src.marine_ops.config import load_config
from src.marine_ops.ingest import collect_weather_data_3d
from src.marine_ops.fusion import fuse_timeseries_3d
from src.marine_ops.eri import compute_eri_3d
from src.marine_ops.daypart import summarize_dayparts, decide_dayparts, route_window
from src.marine_ops.reporting import render_html_3d, write_side_outputs

def main(location_group=("AGI","DAS"), hours=72, run_ts=None, out_dir="out"):
    cfg = load_config("config/locations.yaml")
    cfg.forecast_hours = hours
    run_ts = run_ts or datetime.utcnow()

    raw = collect_weather_data_3d(cfg, mode="auto")         # 수집
    fused = fuse_timeseries_3d(raw["timeseries"], raw["weights"])  # 융합(시간별)
    eri = compute_eri_3d(fused)                             # ERI(시간별)

    # 위치별 Daypart 요약/판정
    agi_dp = decide_dayparts(summarize_dayparts(fused["AGI"], cfg.tz), raw["ncm_alerts"])
    das_dp = decide_dayparts(summarize_dayparts(fused["DAS"], cfg.tz), raw["ncm_alerts"])

    # MW4↔AGI 운용 윈도우
    route_win = route_window(agi_dp, das_dp, horizon="72h")

    # 보고서 생성(표 + 인포그래픽)
    html_path = render_html_3d(
        run_ts=run_ts, cfg=cfg, agi=agi_dp, das=das_dp,
        route_windows=route_win, ncm_alerts=raw["ncm_alerts"], out_dir=out_dir
    )
    # CSV/TXT/JSON 동시 저장
    write_side_outputs(out_dir, raw, fused, eri, agi_dp, das_dp, route_win)
    return html_path

if __name__ == "__main__":
    main()
```

> **주의**: ERI·게이트·γ 가중과 Sea State 경계는 **기존 로직/문서 그대로** 사용합니다(판정 일관성 유지).

---

## 5) 스케줄러(06:00/17:00, Asia/Dubai)

* **Windows 작업 스케줄러**: 06:00 / 17:00에 `python -m scripts.weather_job_3d` 실행.
* 서버 TZ가 UTC인 경우, 래퍼에서 **Asia/Dubai**로 강제 변환(수집 시 `timezone=Asia/Dubai` 이미 지정).

---

## 6) 검증 체크리스트(3일 운용)

1. **API 요청**:

   * Marine: `forecast_days=3` 또는 `forecast_hours=72`, `cell_selection=sea`, `tz=Asia/Dubai`.
   * Weather/ECMWF: `wind_speed_10m, wind_gusts_10m, wind_direction_10m, visibility`.
2. **NCM 경보 파서**: “rough at times / high seas / fog” → γ(0.15/0.30/fog=no‑go). 
3. **Sea State(WMO 3700)**: Hs→Slight/Moderate/Rough 매핑이 보고·판정·UI에서 동일.
4. **Daypart**: (04–06 / 06–12 / 12–17 / 17–22) 구간별 **Hs_mean/p90, Tp_mean, swell_dir/period_mean, wind_mean/gust_p90, vis_mean** 산출.
5. **MW4↔AGI**: (AGI, DAS) **둘 다** GO/COND인 구간만 **Route Window**로 표기.
6. **출력**: `out/summary_3d.html`(+ CSV/TXT/JSON). 프런트는 v2.3 HTML 컴포넌트 재사용. 

---

## 7) 리스크 & 보정

* **연안 정확도**: Open‑Meteo Marine의 조석/해류는 **연안에서 정확도 제한**이 명시되어 있으므로, **NCM Al Bahar 경보·부이/관측과 교차 검증**, **보수적 버퍼** 적용을 권고합니다.
* **대기/스크래핑**: Playwright 대기 시 `domcontentloaded` 또는 `load` 사용, 재시도·백오프·User‑Agent 고정으로 **429/차단** 완화.
* **표준화**: Sea State(WMO 3700) 경계와 게이트 임계(Go ≤1.0 m/≤20 kt, Cond ≤1.2 m/≤22 kt)를 **하나의 상수 모듈**에서 참조(보고·판정·시각화 일관). 

---

## 8) 빠른 시작(로컬 테스트)

```bash
# 1) 가상환경 + 의존성
python -m venv .venv && . .venv/Scripts/activate  # Windows
pip install requests pandas numpy jinja2 playwright
python -m playwright install chromium

# 2) 72h 보고서 1회 생성
python -m scripts.weather_job_3d

# 3) 산출물
# out/summary_3d.html, out/api_status_*.csv, out/summary.txt, out/summary_*.json
```

---

### 결론

* 위 설계/스켈레톤만 추가하면 **기존 v2.3 파이프라인**에 **3일치(72h) 해양·기상 예보 → Daypart 요약 → Go/No‑Go 판정 → MW4↔AGI 운용 윈도우**까지 **자동 보고(06:00/17:00)**가 붙습니다.
* 데이터 정의(해양 변수·경보 가중·Sea State·게이트)는 **기존 ERI/판정 문서**와 완전히 합치되어 운영 일관성이 보장됩니다.

> 필요하시면, **ETA/ETD 지연 모델(유효속력 v_eff = v_hull × f(Hs, gust))**과 **경로각‑스웰 교차각 감쇠계수**까지 포함한 “정량 영향” 모듈을 바로 붙여 드리겠습니다.
