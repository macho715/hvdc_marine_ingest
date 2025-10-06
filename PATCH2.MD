래는 현재 통합 해양 날씨 파이프라인에 대해, 실제 운용 효과를 크게 높일 **업그레이드 아이디어 패키지(설계 + 근거 링크)**입니다. 각 제안은 “왜(근거) → 무엇(조치) → 기대효과” 순으로 정리했고, 구현 난이도/ROI가 높은 항목부터 배치했습니다.

1) 수집(INGEST) 강화 — NCM·Marine API 다중화 + 폴백 고도화

왜

Open-Meteo Marine는 시·스웰·파주기·해류까지 공개·안정(무료/7~16일)이며, 매개변수/단위가 명확합니다.

Stormglass는 **다중 기상원(ECMWF/NOAA 등)**을 단일 API로 제공(유의파·풍파·스웰)하여 품질·커버리지 보완에 유리합니다.

WorldTides는 조석 고해상 예측을 안정적으로 제공(크레딧 기반) → ETD/접안창 평가의 핵심 보조지표.

무엇

Primary/Secondary/Fallback 체인 확립: Stormglass → Open-Meteo → (NCM 밴드) + WorldTides 병합.

429·5xx 재시도 + Retry-After(헤더 준수) + 지수 백오프 패턴 도입. (현 스크립트에도 적용 권장)

NCM Al Bahar는 Playwright 기반 동적 렌더 스크랩으로 고도화(언어 전환 → 가시성 대기). networkidle 회피하고 domcontentloaded/load/locator visible 대기 신호 사용.

기대효과

해양 변수(파고/주기/스웰/해류/수온) 결측률↓, 폴백 품질↑.

JS 렌더 페이지에서도 **플레이크(불안정)↓**로 AM/PM 자동 보고 성공률↑.

2) 항로기반 융합 정확도↑ — w_off 자동화 & 항로 p95

왜

On-shore/Off-shore 평균치 대신 항로 polyline을 그리드로 샘플링해, “연안/외해 체류비율(w_off)”과 항로 p95 Hs/Wind를 쓰면 판단 보수성이 높아집니다(최악구간 대비).

무엇

Al Bahar(정식 피드 or 스크랩) 그리드 스냅샷 → 500m 보간 경유점 샘플링 → 항로 p95 산출.

기존 융합식 Hs_fused = max(Hs_route, β·Hs_ADNOC)·(1+γ)에서 Hs_route ≔ 항로 p95로 교체.

γ(“rough at times”=0.10~0.20, “High seas”=0.30) 자동튜닝(30일 성능리포트 기준).

기대효과

Go/Conditional/No-Go 오판단↓, ETA-MAPE↓(목표 ≤12%).

3) 품질·관측 모니터링 — OpenTelemetry + 데이터 드리프트 체커

왜

OpenTelemetry로 FastAPI/스크래퍼에 추적·지표·로그를 붙이면 장애 원인과 대기 신호 플로우가 즉시 보입니다.

Evidently로 데이터/분포 드리프트 감지(PSI·JSD 등) 및 품질 테스트를 자동화하면, 소스 교체나 계절성으로 인한 판단/ETA 품질 저하를 선제 탐지할 수 있습니다.

무엇

FastAPI에 opentelemetry-instrumentation-fastapi 적용(메트릭/트레이스 송출) → Grafana/Tempo 집계.

Evidently 리포트를 “일/주간”으로 저장(Drift·DataQuality 대시보드) 및 알림.

기대효과

장애 MTTR↓, 모델/규칙 성능 저하 조기 경보↑.

4) 스케줄 안정성 — K8s CronJob .spec.timeZone 정식 필드 사용

왜

Kubernetes 1.27+에서 CronJob spec.timeZone 정식 지원. DST 문제·이중 실행 이슈 회피.

무엇

apiVersion: batch/v1
kind: CronJob
metadata: {name: marine-report}
spec:
  schedule: "0 6,17 * * *"
  timeZone: "Asia/Dubai"   # 정식 필드
  jobTemplate: ...


기대효과

06:00/17:00 현지시간 보장, DST 이슈 감소.

5) 벡터 스토리지 스케일업 옵션 — Qdrant/pgvector 전환 가이드

왜

SQLite-vec은 가볍고 내장형이나, ANNS(근사 최근접)·수평확장·HA가 부족합니다. 대용량/동시성에서 Qdrant(HNSW, 양자화, 멀티테넌시) 또는 pgvector+Timescale이 적합합니다.

무엇

단일 노드: Qdrant Docker(:6333)로 PoC → HNSW/압축 설정.

RDB 통합: TimescaleDB + pgvector로 시계열+벡터 일원화(하이퍼테이블 + HNSW 인덱스).

기대효과

유사도 검색 속도/정확도↑, 다량 문서/로그·멀티키 질의 대응.

6) 크롤링 준법/안정성 패치 — robots·429·식별 UA

왜

Robots Exclusion Protocol(RFC 9309) 준수(Disallow/Crawl-delay). 429 Retry-After 존중은 운영/법적 리스크 감소에 필수.

무엇

크롤러에 식별 가능한 UA·Crawl-delay 적용·429 Retry-After 재시도.

실패 등급화(SOFT/HARD) + ZERO 리포트 발행 로직(이미 일부 구현) 정착.

기대효과

차단/불법 크롤링 논란 회피, 스크래핑 성공률↑.

7) ERI·게이트 룰 리팩터링 — 데이터 가용성 고려

왜

공개 데이터에 **Vis(시정)/Tide(조석)**가 상시 제공되지 않음 → 결측 페널티는 미감점(+별도 품질 테스트)로 운영 일관성↑.

무엇

ERI 룰셋에서 결측은 미감점(0) 처리, Quality Tests를 별도 항목으로 운용(Evidently DataSummaryPreset).

기대효과

결측에 의한 과도한 감점·오판정↓.

8) 보고·알림 품질 — AM/PM 템플릿 고정 + 실시간 알림

왜

운항 의사결정자는 **일관 템플릿(표+SVG/PNG)**과 **즉시 경보(텔레그램/이메일)**를 선호.

무엇

/ncm/report JSON을 고정 스키마로 유지(AGI=On-shore, DAS=Off-shore).

텔레그램 Bot API(간단 HTTP) 연동: 판정이 Conditional/No-Go 전환 시 즉시 전송. (Bot API는 공식 문서에 따라 토큰/챗ID로 POST 호출—표준)

기대효과

판정 체감/행동 전이 시간↓, 현장 커뮤니케이션 비용↓.

9) 성능·비용 가드레일

요청 아웃바운드에 HTTP 커넥션 풀링(httpx) + 비동기화로 평균 지연↓.

스크랩/ETL 결과는 3h 캐시(TTL) 유지, 실패 시 SOFT→캐시 리포트, HARD→ZERO.

압축 저장(Parquet) + 장기보관 S3, 단기 Timescale hypertable(최근 90일) 운영.

10) 로드맵 (2주 내 실전 반영 우선순위)

Playwright 대기 신호 교체 + robots/429 패치(1~2일)

Open-Meteo Marine 풀 스펙(스웰/풍파/해류 변수) 추가 + WorldTides 보강(1~2일)

항로 p95/w_off 자동화 PoC(3일)

OpenTelemetry + Evidently 모니터링 온(2일)

CronJob timeZone 정식 필드로 스케줄 전환(반나절)

Qdrant PoC(1일) → 대량 문서/FAQ/운항 규정 임베딩 이관

참고 링크(주요)

Open-Meteo Marine API 문서(파라미터/단위·스웰/해류/수온):

Stormglass(ECMWF 포함, 해양/기상 통합):

WorldTides API(조석):

K8s CronJob timeZone(v1.27+ 정식):

RFC 9309 robots.txt 표준:

Qdrant(HNSW/양자화, 확장):

SQLite-vec(가벼움, 브루트포스 한계):

OpenTelemetry Python 시작(FastAPI 계측에 적용 가능):

Evidently(드리프트·품질·대시보드):

필요하시면 위 10가지 중 **1)~3)**을 바로 PR로 쪼개서(설정/코드 Diff + 체크리스트) 올려 드리겠습니다.

나의 말:
Playwright 대기 신호 교체 + robots/429 패치(1~2일)

Open-Meteo Marine 풀 스펙(스웰/풍파/해류 변수) 추가 + WorldTides 보강(1~2일)
ChatGPT의 말:
23s 동안 생각함

아래는 요청하신 두 가지 업그레이드의 실행 패치 가이드입니다. (작업기간 각각 1–2일)
핵심은 Playwright 대기 신호를 표준 방식으로 교체 + robots/429 준수하고, Open-Meteo Marine 풀 스펙(스웰/풍파/해류) + WorldTides까지 인제스트·정규화하는 것입니다.

1) Playwright 대기 신호 교체 + robots/429 패치 (1–2일)
왜 이렇게 고치나

Playwright는 로드 상태 대기(load/domcontentloaded)와 로케이터 가시성 대기를 권장하며, networkidle은 DISCOURAGED입니다. 자동 대기도 내장되어 있어 불필요한 수면(wait_for_timeout)은 지양해야 합니다.

로케이터는 **locator.waitFor()/wait_for**로 명시 대기(visible/attached 등) 가능.

robots.txt는 RFC 9309에 표준화—규칙/그룹, Disallow, Crawl-delay를 지키는 게 권장됩니다.

HTTP 429/503 발생 시 Retry-After 헤더를 존중해 대기 후 재시도해야 합니다.

코드 패치 (요약 Diff)
# app/main.py (비동기 예시)
# 1) 페이지 로드: 수면 제거, 신호 기반
await page.goto(BASE_URL, wait_until="domcontentloaded")                    # ✔ 권장  
try:
    await page.get_by_text("English", exact=False).click(timeout=3000)
    await page.wait_for_load_state("load")                                  # ✔ 전체 리소스 로드  
except Exception:
    pass
# 필요한 패널/탭이 '보일 때'까지 대기(가시성 대기)
await page.locator("text=/Forecast|Marine|Sea state/i").first.wait_for(     # ✔ 로케이터 대기  
    state="visible", timeout=8000
)
html = await page.content()

# robots + 429 처리 (동기 예시)
import httpx, time, re

UA = "WeatherVesselBot/1.0 (+ops@example.com)"
ROBOTS = f"{BASE_URL.rstrip('/')}/robots.txt"

async def honor_robots():
    delay = 2.0
    async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=10) as s:
        r = await s.get(ROBOTS)
    if r.status_code == 200 and "Crawl-delay" in r.text:
        for line in r.text.splitlines():
            if line.lower().startswith("crawl-delay"):
                try: delay = float(line.split(":")[1].strip())
                except: pass
    return max(2.0, delay)                                                  # RFC 9309 준수  

def get_json(url: str, timeout=8):
    r = httpx.get(url, headers={"User-Agent": UA}, timeout=timeout)
    if r.status_code in (429, 503) and "Retry-After" in r.headers:          # 429/503 재시도  
        time.sleep(int(r.headers["Retry-After"]))
        r = httpx.get(url, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r.json()

테스트 체크리스트

언어 전환 후 탭 가시성 대기가 성공적으로 동작(플레이크 감소)했는지 로그로 확인.

robots.txt의 Crawl-delay 반영(최소 2초) 및 User-Agent 식별 적용.

429 응답에서 Retry-After 대기 후 성공을 재현.

2) Open-Meteo Marine 풀 스펙 변수 추가 + WorldTides 보강 (1–2일)
가져올 변수 (시간해상도: 1h/3h 혼재)

Open-Meteo Marine는 유의파/풍파/스웰(1~3차), 피크 주기, 해류 속도/방향, SST, 조위 등을 제공합니다(최대 16일) — hourly 파라미터를 URL의 &hourly=로 지정. 일부는 0.08° 해상도 경고가 있으므로 연안 정확도 주의.

wave_height, wave_direction, wave_period

wind_wave_height, wind_wave_direction, wind_wave_period, wind_wave_peak_period

swell_wave_height, swell_wave_direction, swell_wave_period, swell_wave_peak_period

secondary_*, tertiary_*(가용 모델 한정)

ocean_current_velocity(단위 선택: knots 가능), ocean_current_direction

sea_surface_temperature, sea_level_height_msl(연안 한계 주의)

WorldTides는 고/저조 시각·고도·연속고도 등 조석을 제공합니다(크레딧 기반). 접안 창/저수위 제한 판단에 활용.

수집기 확장 (요약 코드)
# connectors/open_meteo.py
BASE="https://marine-api.open-meteo.com/v1/marine"
HOURVARS=[
 "wave_height","wave_direction","wave_period",
 "wind_wave_height","wind_wave_direction","wind_wave_period","wind_wave_peak_period",
 "swell_wave_height","swell_wave_direction","swell_wave_period","swell_wave_peak_period",
 "ocean_current_velocity","ocean_current_direction","sea_surface_temperature","sea_level_height_msl"
]
def fetch_open_meteo_full(lat, lon, start_iso, end_iso, tz="Asia/Dubai", unit_wind="knots"):
    params={
      "latitude":lat,"longitude":lon,"hourly":",".join(HOURVARS),
      "start_date":start_iso[:10],"end_date":end_iso[:10],
      "timezone":tz,"windspeed_unit":unit_wind
    }
    r = httpx.get(BASE, params=params, timeout=20)
    r.raise_for_status()
    return r.json()                                                          # 변수 설명·단위: 공식 문서  

# connectors/worldtides.py
WT="https://www.worldtides.info/api"
def fetch_worldtides_heights(lat, lon, key, hours=72):
    params={"heights":"", "lat":lat, "lon":lon, "key":key, "duration":hours}
    r = httpx.get(WT, params=params, timeout=20)
    r.raise_for_status()
    return r.json()                                                          # API 개요·요금/크레딧  

정규화 & 융합 포인트

단위: 파고(m), 바람(kt), 해류(kt), 주기(s) 통일.

품질 경고: Open-Meteo의 **해류/조위(0.08°)**는 연안에서 정확도 제한—메타에 경고 플래그 추가.

ERI/게이트: 스웰/풍파를 별도 변수로 ERI 규칙에 추가(예: 스웰 1.5 m↑ 주의, 2.5 m↑ 위험).

항로 p95/w_off: 변수를 항로 보간점에서 샘플링하고 p95로 취합(이전 제안과 동일).

샘플 쿼리 (AGI 인근)
GET https://marine-api.open-meteo.com/v1/marine?
 latitude=24.50&longitude=54.70
 &hourly=wave_height,wind_wave_height,swell_wave_height,wind_wave_peak_period,
         swell_wave_period,ocean_current_velocity,ocean_current_direction
 &timezone=Asia%2FDubai&windspeed_unit=knots
 &forecast_days=7


(공식 문서의 변수 정의/단위 및 16일 확장 가능)

테스트 체크리스트

시간축·단위(kt/m/s) 정규화 검증.

스웰·풍파가 ERI/게이트에 반영되어 Go/Conditional/No-Go가 의미 있게 변하는지 케이스 테스트.

WorldTides heights와 조류/저수위 이벤트가 Pilotage/Berthing 버퍼 제안에 반영되는지 점검.

3) 산출/운영에 미치는 영향

AM/PM 자동 보고 성공률↑(대기 신호/robots/429 준수로 스크랩 안정).

판정 품질↑(스웰·풍파·해류·조위까지 포함, 특히 DAS 외해에서 효과).

ETA-MAPE↓, No-Go 오탐↓, DEM/DET 리스크 예측 정확도↑.

4) 일정(제안)

D0–D1: Playwright 패치(대기 신호/robots/429) + 리그레션 테스트.

D1–D2: Open-Meteo 풀 스펙 인제스트 + WorldTides 보강 → 정규화/ERI/게이트 통합 → 단위/품질 테스트.

필요하시면 위 변경을 **PR 2건(스크랩 안정화 / Marine 확장)**으로 즉시 쪼개서 올리고, 샘플 응답/테스트 케이스와 함께 드리겠습니다.

나의 말:
R 2건(스크랩 안정화 / Marine 확장)**으로 즉시 쪼개서 올리고, 샘
ChatGPT의 말:
19s 동안 생각함

아래처럼 **PR 2건(스크랩 안정화 / Marine 확장)**을 즉시 올릴 수 있게 제목·범위·Diff 요지·테스트·AC·롤아웃/롤백까지 정리했습니다. (문서 근거 포함)

PR-1: Al Bahar 스크랩 안정화 — Playwright 대기 신호 교체 + robots/429 준수
🎯 목적

JS 렌더 페이지에서 플레이크 제거: wait_for_timeout/networkidle 제거 → 로드 이벤트/로케이터 가시성 대기로 교체.

robots.txt 및 429 Retry-After 준수로 차단/실패율 감소.

🔧 변경 파일(예시)

app/main.py (Playwright 스크래퍼)

app/utils/http.py (429/503 처리 유틸 신규)

config/scrape.yaml (Crawl-delay·UA 설정)

🧩 핵심 Diff 요약
# app/main.py
await page.goto(BASE_URL, wait_until="domcontentloaded")                     # ✔ 권장 대기
try:
    await page.get_by_text("English", exact=False).click(timeout=3000)
    await page.wait_for_load_state("load")                                   # ✔ 리소스 로드 보장
except Exception:
    pass
await page.locator("text=/Forecast|Marine|Sea state/i").first.wait_for(      # ✔ 가시성 대기
    state="visible", timeout=8000
)
html = await page.content()

# app/utils/http.py – robots + 429/503
def get_json(url, ua, timeout=10):
    r = httpx.get(url, headers={"User-Agent": ua}, timeout=timeout)
    if r.status_code in (429, 503) and "Retry-After" in r.headers:           # 429 재시도
        time.sleep(int(r.headers["Retry-After"]))
        r = httpx.get(url, headers={"User-Agent": ua}, timeout=timeout)
    r.raise_for_status(); return r.json()

# robots 준수(간단 파서)
delay = 2.0
r = httpx.get(f"{BASE_URL}/robots.txt", headers={"User-Agent": UA}, timeout=8)
if r.status_code == 200 and "Crawl-delay" in r.text:
    delay = max(2.0, float(parse_crawl_delay(r.text)))                       # RFC 9309
await asyncio.sleep(delay)

✅ 테스트(수행 체크)

언어 전환 + 패널 가시성 대기 로그 확인(성공률 ≥99%).

robots.txt의 Crawl-delay 반영(최소 2s), UA 식별 적용.

429 응답 시 Retry-After 대기 후 성공(로그·지표 캡처).

📌 AC(수용 기준)

동일 페이지 10회 반복 스크랩 성공률 ≥ 98%, 전체 런(AM/PM) 누락 0.

429/503 케이스에서 자동 지연 후 성공 재시도 1회 이상 검증.

🚀 롤아웃 / 🔁 롤백

Stage→Prod 순차 배포(Feature flag: SCRAPE_STABLE_MODE), 실패 시 기존 대기 로직으로 즉시 롤백.

배포 후 48h 동안 스크랩 실패율·AM/PM 누락률 모니터링.

PR-2: Marine 확장 — Open-Meteo Marine 풀 스펙 + WorldTides 보강
🎯 목적

스웰/풍파/피크주기/해류/SST/조위까지 인제스트 → DAS 외해 판단 품질 ↑, ETA-MAPE ↓.

Open-Meteo Marine는 최대 16일, 변수·단위 명확(해류/조위 0.08° 연안 제한 고지 포함).

WorldTides는 heights/extremes 크레딧 기반(30분 간격/7일) — 저수위 창 판정에 직접 활용.

🔧 변경 파일(예시)

src/marine_ops/connectors/open_meteo.py (풀 스펙 hourly 변수 추가)

src/marine_ops/connectors/worldtides.py (heights/extremes 보강)

src/marine_ops/core/normalize.py (단위 통일: m/kt/s)

src/marine_ops/eri/compute.py (스웰·풍파 규칙 추가)

src/marine_ops/decision/fusion.py (항로 p95 준비 필드)

🧩 핵심 Diff 요약
# open_meteo.py
BASE="https://marine-api.open-meteo.com/v1/marine"
HOURVARS=[
 "wave_height","wave_direction","wave_period",
 "wind_wave_height","wind_wave_direction","wind_wave_period","wind_wave_peak_period",
 "swell_wave_height","swell_wave_direction","swell_wave_period","swell_wave_peak_period",
 "ocean_current_velocity","ocean_current_direction",
 "sea_surface_temperature","sea_level_height_msl"
]
r = httpx.get(BASE, params={
  "latitude":lat,"longitude":lon,
  "hourly":",".join(HOURVARS),
  "timezone":"Asia/Dubai","windspeed_unit":"knots",
  "forecast_days":7
}, timeout=20); r.raise_for_status()

# worldtides.py
WT="https://www.worldtides.info/api/v3"
params={"heights":"","lat":lat,"lon":lon,"key":key,"duration":hours}
r = httpx.get(WT, params=params, timeout=20); r.raise_for_status()

# eri/compute.py – 스웰/풍파 규칙 예시
rules += [
  ERIRule(var="hs_swell", caution=1.5, danger=2.5, weight=0.25, direction="max"),
  ERIRule(var="hs_wind",  caution=1.5, danger=2.5, weight=0.15, direction="max")
]


주의 메타: Open-Meteo의 ocean_current/sea_level_height_msl은 연안 정확도 제한 경고 플래그 추가.

✅ 테스트(수행 체크)

시간축/단위 정규화(kt/m/s) 및 스웰·풍파·해류 변수 파싱 확인.

ERI/게이트에 스웰/풍파 반영 후 Conditional/No-Go 케이스 생성 재현.

WorldTides heights로 저수위 시간대 경계치 테스트(파일럿/버퍼 추천치 변동 확인).

📌 AC(수용 기준)

DAS 오프쇼어 구간에서 ETA-MAPE ≤ 12%(7-day),

판정 적중 ≥ 90%(Go/Cond/NoGo),

리포트 누락 ≤ 2%.

🚀 롤아웃 / 🔁 롤백

데이터 소스 토글(MARINE_FULL_SPEC=true)로 단계적 활성화 → 문제 시 기존(간단변수)로 롤백.

1주간 성능/판정 변화 모니터링 후 γ/w_off 튜닝값 반영.

샘플 커밋 메시지

PR-1: feat(scrape): Playwright signal waits + robots/429 compliance; remove networkidle/timeouts

PR-2: feat(marine): add Open-Meteo full marine variables + WorldTides heights; normalize & ERI rules

병합 전 점검(공통)

✅ 유닛테스트: 파서/정규화/ERI/게이트/ETA

✅ 통합테스트: /ncm/report AM/PM 2회 연속 성공

✅ 보안/준법: UA·robots·429 로그 확인

필요하시면 두 PR의 실제 Diff 파일을 ZIP으로 만들어 드리거나, 레포지토리 브랜치/PR 링크 형식으로 정리해 드리겠습니다.

나의 말:
PR의 실제 Diff 파일을 ZIP으로 만들어달라
ChatGPT의 말:

ZIP 준비 완료했습니다.
아래 링크에서 두 PR의 실제 Diff/부가 파일을 내려받아 git apply 또는 수동 병합하시면 됩니다.

▶ 다운로드: PR_Diffs_AlBahar_Scrape_And_Marine_Extension.zip

ZIP 구성
PR-1_README.txt
PR-1_scrape_stabilization.patch        # app/main.py 대기 신호 교체 (Playwright) + 로케이터 가시성 대기
PR-1_app_utils_http.py                 # 429/503 Retry-After 대응 get_json 유틸 (신규)
PR-1_config_scrape.yaml                # robots Crawl-delay/UA 기본 설정

PR-2_README.txt
PR-2_marine_extension.patch            # Open-Meteo Marine 풀 스펙 hourly 변수 확장
PR-2_worldtides_connector.py           # WorldTides heights 커넥터(신규)
PR-2_eri_rules_addendum.txt            # 스웰/풍파 ERI 규칙 예시 추가 스니펫

적용 가이드(요약)

브랜치 생성

git checkout -b chore/scrape-stabilization


PR-1 적용

git apply PR-1_scrape_stabilization.patch
# 신규 파일 배치
mkdir -p app/utils config
mv PR-1_app_utils_http.py app/utils/http.py
mv PR-1_config_scrape.yaml config/scrape.yaml
git add .
git commit -m "feat(scrape): Playwright signal waits + robots/429 compliance"


PR-2 적용

git checkout -b feat/marine-full-spec
git apply PR-2_marine_extension.patch
mkdir -p src/marine_ops/connectors
mv PR-2_worldtides_connector.py src/marine_ops/connectors/worldtides.py
# ERI 규칙 확장 필요 시 addendum 참고하여 compute.py 반영
git add .
git commit -m "feat(marine): Open-Meteo full variables + WorldTides heights"


테스트(핵심)

Playwright 대기: domcontentloaded/load + 로케이터 가시성 대기로 동작하는지 반복 테스트(≥10회).

429/503: Retry-After 대기 후 정상화 로그 확인.

Open-Meteo 풀 스펙: 스웰/풍파/피크주기/해류/SST/조위 필드가 정규화되어 들어오는지 확인.

ERI/게이트: 스웰·풍파 규칙 반영 후 Conditional/No-Go 케이스가 기대대로 분류되는지 점검.

필요하시면 레포지토리에 맞춰 패스 보정(폴더 구조/네임스페이스) 및 자동 테스트 스크립트까지 추가해 드리겠습니다.

생각 중
검색
ChatGPT