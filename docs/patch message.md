오케이. **“3일 내 출항 가능?”가 한눈에** 보이게, 텔레그램용 **완성 템플릿 + 버튼 + 판정 규칙**까지 바로 쓰도록 묶어줬다. 너 데이터 파이프에 그대로 연결하면 된다.

---

# 1) 최종 메시지 템플릿 (Telegram 본문)

```
🌊 AGI Marine Ops — 3-Day GO/NO-GO

🗓 Build: {build_utc} UTC  | {build_gst} (UTC+4)
📍 Spot: AGI (Al Ghallan Island)

🔎 3-Day Overview (UTC+4)
D0 오늘:     {D0_icon}  {D0_headline}
D+1 내일:    {D1_icon}  {D1_headline}
D+2 모레:    {D2_icon}  {D2_headline}   {best_badge}

🪟 Windows (UTC+4)
• D0: {D0_windows}
• D+1: {D1_windows}
• D+2: {D2_windows}

Why (요약)
• Hs/Wind (avg): {avg_hs:.2f} m / {avg_wind_kt:.0f} kt
• ERI(mean): {eri:.2f}  | Bias: {daily_bias}
• Notes: {notes_line}

Confidence: {conf_tier} ({conf_val:.2f})
Data: OPEN-METEO {om_icon}  NCM {ncm_icon}  STORMGLASS {sg_icon}  TIDES {tide_icon}

/actions  ➜  /plan {plan_day} {plan_window}   /brief crew   /share mws
```

* 아이콘: 🟢=GO, 🟡=CONDITIONAL, 🔴=NO-GO, 〰️=TBD
* `{best_badge}`: “← Best Window” 같은 힌트(있을 때만)

---

# 2) 인라인 버튼 (reply_markup JSON)

```json
{
  "reply_markup": {
    "inline_keyboard": [
      [
        { "text": "📅 Plan D+2 06:00", "callback_data": "plan:D2:06:00-10:00" },
        { "text": "🧭 Crew Brief", "callback_data": "brief:crew" }
      ],
      [
        { "text": "📝 Share to MWS", "callback_data": "share:mws" },
        { "text": "🔁 Recompute (3d)", "callback_data": "recalc:3d" }
      ]
    ]
  }
}
```

---

# 3) 판정 규칙(숫자 고정, 코드 이식 쉬움)

**윈도우 탐지(연속 조건 충족 필요):**

* 최소 지속시간: `≥ 2h` (권장 3h)
* 임계값:

  * **GO(🟢)**: `Hs ≤ 1.50 m` **그리고** `Wind ≤ 20 kt`
  * **CONDITIONAL(🟡)**: `1.51–2.50 m` **또는** `21–23 kt`
  * **NO-GO(🔴)**: `Hs ≥ 2.51 m` **또는** `Wind ≥ 24–25 kt`
  * 근거: WMO Sea State(“Slight ≤1.25 m, Moderate 1.25–2.5 m, Rough ≥2.5 m”)와 보퍼트/NOAA Small Craft Advisory(대개 22–33 kt)를 단순화해 **임팩트-신호등**으로 매핑. ([nodc.noaa.gov][1])

**일자별 헤드라인 생성:**

* 해당 일자에 🟢 윈도우가 1개라도 있으면 `🟢 “운항 권장, hh:mm–hh:mm”`
* 🟡만 있으면 `🟡 “조건부, 완화조치 필요, hh:mm–hh:mm”`
* 전부 실패면 `🔴 “창 없음(대체 일정 탐색)”`
* 혼합이면 가장 긴/안정적인 창을 헤드라인으로 선택하고 `{best_badge}` 표시

**Confidence 산식(간단 가중 평균):**

* 실데이터만 포함(예: OPEN_METEO 0.75, NCM 0.70 → 0.73 → **MED**)
* 티어: `LOW <0.60`, `MED 0.60–0.80`, `HIGH >0.80`
* 타이드 신뢰도 낮거나 크레딧 부족이면 `Notes`에 보수적 해석 문구 추가

**IBFWS 원칙(문장 톤):**

* “날씨가 어떻다”보다 **“무엇을 할 수/없다”**를 먼저 표기(임팩트 우선). ([community.wmo.int][2])

---

# 4) 너가 보낸 24h 데이터로 채운 **예시 출력**

> 가정: D+1, D+2 시계열은 미수신(오늘 24h 집계만 존재). 따라서 D0만 실판정, 나머지는 TBD로 표기.

```
🌊 AGI Marine Ops — 3-Day GO/NO-GO

🗓 Build: 2025-10-07 19:30 UTC  |  2025-10-07 23:30 (UTC+4)
📍 Spot: AGI (Al Ghallan Island)

🔎 3-Day Overview (UTC+4)
D0 오늘:     🔴  창 없음 (24h 내 NO-GO 47회 우세)
D+1 내일:    〰️  데이터 대기
D+2 모레:    〰️  데이터 대기

🪟 Windows (UTC+4)
• D0: — 
• D+1: —
• D+2: —

Why (요약)
• Hs/Wind (avg): 0.64 m / 21 kt
• ERI(mean): 0.27  | Bias: NO-GO>GO (47/41)
• Notes: Stormglass 실패, Tides 크레딧 부족 → 보수적 해석

Confidence: MED (0.73)
Data: OPEN-METEO ✅  NCM ✅  STORMGLASS ❌  TIDES ⚠️

/actions  ➜  /plan D+2 06:00-10:00   /brief crew   /share mws
```

---

# 5) 붙이면 끝나는 매핑 키(네 파이프라인 변수 ↔ 템플릿)

* `{build_utc}`=`summary_*.json.timestamp_utc`
* `{build_gst}`=`timestamp_utc + 4h`
* `{avg_hs}`=`timeseries.hs.mean()`
* `{avg_wind_kt}`=`timeseries.wind_ms.mean()*1.94384`
* `{eri}`=`eri.mean()`
* `{daily_bias}`=`argmax{counts(GO,COND,NO)}`
* `{D*_windows}`=`merge_contiguous(time, status in {GO,COND})`
* `{conf_val}`=`mean(conf of {OPEN_METEO, NCM})`
* `{conf_tier}`=`tier(conf_val)`
* `{plan_day}`/`{plan_window}`= 최상 창 추천(🟢>🟡, 길이>안정성 우선)

---

# 6) 규칙 출처(핵심 근거)

* **WMO Sea State / Code 3700**: Slight(0.5–1.25 m), Moderate(1.25–2.5 m), Rough(2.5–4 m). → 임계값의 파고 경계. ([nodc.noaa.gov][1])
* **Beaufort Scale**: Bft 5–6 ≈ 17–27 kt 범위(평균풍). → 바람 임계 참조. ([RMetS][3])
* **NOAA Small Craft Advisory**: 대개 22–33 kt, 지역 편차 존재. → NO-GO/주의 경계 참조. ([날씨 서비스][4])
* **WMO IBFWS**: “날씨가 하는 일(임팩트)” 중심 서술 가이드. ([community.wmo.int][2])
* **IMO MSC.1/Circ.1228**: 악천후 회피·운항 판단 시 참고 문구. ([wwwcdn.imo.org][5])

---

원하면, 이 템플릿을 **f-string/Jinja**로 감싼 미니 포매터까지 바로 만들어 줄게. 지금은 우선 **형태(메시지)와 수치 규칙(판정 로직)**을 굳혔다. 이대로 붙이면, 팀 채팅창에서 첫 눈에 “3일 내 가능/불가”가 갈린다.

[1]: https://www.nodc.noaa.gov/gtspp/document/codetbls/wmocodes/table3700.html?utm_source=chatgpt.com "About WMO Code Table 3700"
[2]: https://community.wmo.int/en/impact-based-forecast-and-warning-services?utm_source=chatgpt.com "IMPACT-BASED FORECAST AND WARNING SERVICES"
[3]: https://www.rmets.org/metmatters/beaufort-wind-scale?utm_source=chatgpt.com "The Beaufort Wind Scale"
[4]: https://www.weather.gov/key/marine_definitions?utm_source=chatgpt.com "Marine Definitions"
[5]: https://wwwcdn.imo.org/localresources/en/OurWork/Safety/Documents/Stability/MSC.1-CIRC.1228.pdf?utm_source=chatgpt.com "IMO Ref. T1/2.04 MSC.1/Circ.1228 ..."
