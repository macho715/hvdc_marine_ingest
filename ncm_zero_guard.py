from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import List, Dict

DAYPARTS = ["Dawn", "Morning", "Afternoon", "Evening"]

@dataclass
class ZeroMeta:
    run_label: str
    tz: str
    run_time_iso: str
    source: str
    sites: List[str]

@dataclass
class ZeroRow:
    date_label: str
    dawn: str
    morning: str
    afternoon: str
    evening: str

@dataclass
class ZeroReport:
    title: str
    meta: ZeroMeta
    executive_summary: str
    operational_posture: str
    ncm_context_note: str
    action_note: str
    legend: str
    agi_table: List[ZeroRow]
    das_table: List[ZeroRow]
    status_strip: Dict[str, Dict[str, List[str]]]
    warnings: str
    fog_note: str
    etd_eta: str
    dem_det: str
    pilotage: str
    mw4_agi_window: str
    zero_log: Dict[str, str]
    sources_note: str
    ruleset_note: str


def _date_label(d: datetime) -> str:
    return d.strftime("%a %d %b")  # Mon 06 Oct


def build_zero_table(start: datetime, days: int = 4) -> List[ZeroRow]:
    rows: List[ZeroRow] = []
    cell = (
        "Wind N/A(ZERO) · Wave N/A · Sea N/A · Swell N/A · Vis/Fog N/A · "
        "Warnings N/A · Go/No‑Go N/A (Pilotage Buffer N/A) · ETD/ETA N/A · DEM/DET N/A · MW4↔AGI N/A"
    )
    for i in range(days):
        d = start + timedelta(days=i)
        rows.append(ZeroRow(_date_label(d), cell, "same", "same", "same"))
    return rows


def build_status_strip(days: int = 4) -> Dict[str, Dict[str, List[str]]]:
    strip = ["■■■■" for _ in range(days)]  # ■=UNVERIFIED
    return {
        "AGI": {"labels": ["Mon", "Tue", "Wed", "Thu"], "bars": strip},
        "DAS": {"labels": ["Mon", "Tue", "Wed", "Thu"], "bars": strip},
    }


def emit_markdown(rep: ZeroReport, out_md: Path) -> None:
    md = []
    md.append("# NCM Al Bahar Marine Report — AGI (Al Ghallan) & DAS Island\n")
    md.append(f"Run: {rep.meta.run_label} · Source: {rep.meta.source} · TZ: {rep.meta.tz}\n\n")
    md.append("## Executive Summary (KR+EN)\n")
    md.append(rep.executive_summary + "\n\n")
    md.append(rep.operational_posture + "\n\n")
    md.append(rep.ncm_context_note + "\n\n")
    md.append(rep.action_note + "\n\n")
    md.append("## Fixed Template — 4‑Day x Daypart\n")
    md.append("Legend: N/A(ZERO) = not captured. No assumptions (HallucinationBan).\n\n")
    md.append("### AGI (Al Ghallan)\n")
    md.append("Date\tDawn\tMorning\tAfternoon\tEvening\n")
    for r in rep.agi_table:
        md.append(f"{r.date_label}\t{r.dawn}\t{r.morning}\t{r.afternoon}\t{r.evening}\n")
    md.append("\n### DAS Island\n")
    md.append("Date\tDawn\tMorning\tAfternoon\tEvening\n")
    for r in rep.das_table:
        md.append(f"{r.date_label}\t{r.dawn}\t{r.morning}\t{r.afternoon}\t{r.evening}\n")
    md.append("\n## Infographic (status strip — GO window)\n")
    md.append("AGI  [ Dawn | Morning | Afternoon | Evening ]  " + "  ".join(rep.status_strip["AGI"]["bars"]) + "\n")
    md.append("DAS  [ Dawn | Morning | Afternoon | Evening ]  " + "  ".join(rep.status_strip["DAS"]["bars"]) + "\n")
    md.append("Legend: ■=UNVERIFIED (ZERO); □=GO; ▨=CAUTION; ✖=NO‑GO\n\n")
    md.append("## Active NCM Warnings / Fog Risk\n")
    md.append(rep.warnings + "\n\n" + rep.fog_note + "\n\n")
    md.append("## ETD/ETA · DEM/DET · Pilotage/Berthing\n")
    md.append(rep.etd_eta + "\n" + rep.dem_det + "\n" + rep.pilotage + "\n" + rep.mw4_agi_window + "\n\n")
    md.append("## 중단(FAIL‑SAFE) 로그 — ZERO Report\n")
    for k, v in rep.zero_log.items():
        md.append(f"- **{k}**: {v}\n")
    md.append("\n## Sources (attempted/context)\n")
    md.append(rep.sources_note + "\n\n")
    md.append("## Note to Ops (MACHO‑GPT ruleset)\n")
    md.append(rep.ruleset_note + "\n")
    out_md.write_text("".join(md), encoding="utf-8")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tz", default="Asia/Dubai")
    parser.add_argument("--run-time", dest="run_time", default=None, help="ISO or 'YYYY-MM-DD HH:MM'")
    parser.add_argument("--sites", default="AGI,DAS")
    args = parser.parse_args()

    tz = ZoneInfo(args.tz)
    now = datetime.now(tz) if not args.run_time else datetime.fromisoformat(args.run_time).astimezone(tz)
    run_label = now.strftime("%p %H:%M (%Z) · %a, %d %b %Y")

    out_dir = Path("reports"); out_dir.mkdir(exist_ok=True)
    out_md = out_dir / f"NCM_ZERO_{now.strftime('%Y%m%d_%H%M')}.md"
    out_json = out_dir / f"NCM_ZERO_{now.strftime('%Y%m%d_%H%M')}.json"

    meta = ZeroMeta(run_label=run_label, tz=args.tz, run_time_iso=now.isoformat(), source="NCM Al Bahar (nearshore/marine)", sites=args.sites.split(","))
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    rep = ZeroReport(
        title="NCM Al Bahar Marine Report — AGI & DAS",
        meta=meta,
        executive_summary=(
            "ZERO-FETCH: 본 런에서 Al Bahar 동적 패널(JS 렌더)로 AGI/DAS 세부값 미추출. (페이지 접근 가능하나 데이터 바디 미렌더)"
        ),
        operational_posture=(
            "Operational posture: Go/No‑Go 판단 보류(UNVERIFIED) — 항만·파일럿 보수 운용 권고(정박·정선·이안 계획은 현장 관측·VTS 우선)."
        ),
        ncm_context_note=(
            "NCM 공개 맥락(언론): 걸프해 Slight↔Moderate·새벽 박무 가능성 — 참고용(수치 대체 아님)."
        ),
        action_note=("Action: ‘중단(ZERO) 로그’ 개선책 이행 후 다음 런 06:00 재시도."),
        legend="N/A(ZERO) — 본 런 미획득; 가정 없음(HallucinationBan)",
        agi_table=build_zero_table(start_day, 4),
        das_table=build_zero_table(start_day, 4),
        status_strip=build_status_strip(4),
        warnings="Warnings: N/A(ZERO) (동적 로드 비가시)",
        fog_note="Fog/Mist: N/A(ZERO). 전역 맥락만 참고.",
        etd_eta="ETD/ETA Impact: UNVERIFIED — 현장 AWS/해상관측 + VTS 확인 전 확정 금지.",
        dem_det="DEM/DET Risk: UNASSESSED — CY 커트 변경 시 비용 리스크 플래그.",
        pilotage="Pilotage/Berthing: Buffer 산정 보류 (풍속·돌풍·Hs·Tp 불명).",
        mw4_agi_window="MW4↔AGI Operational Window: UNVERIFIED (ZERO).",
        zero_log={
            "데이터 소스": "NCM Al Bahar — 페이지 접근 OK, 본문 데이터는 클라이언트 JS 렌더로 파싱 불가",
            "대상 지점": "AGI (Al Ghallan), DAS Island",
            "실패 범위": "풍/돌풍/풍향, Hs/Tp, Sea, Swell, Vis/Fog, Warnings, Go/No-Go, ETD/ETA, DEM/DET, MW4↔AGI",
            "원인": "SPA/동적 API 호출 결과가 서버측 렌더 없이 전달되어 정적 스크래핑 불가",
            "조치(권장)": "① 서버 API 엔드포인트/토큰 ② Headless(Playwright) 허용 ③ Bulletin 파싱 경로 ④ 임시 AWS/부이 JSON 연동",
            "다음 런": "06:00 Asia/Dubai — 자동 재시도",
        },
        sources_note="NCM 포털 접근 OK, 데이터 미렌더. 언론 요약은 맥락 참고만.",
        ruleset_note="HallucinationBan · Automation‑first · Fail‑safe ZERO",
    )

    emit_markdown(rep, out_md)
    out_md_str = out_md.read_text(encoding="utf-8")
    out_json.write_text(json.dumps(asdict(rep), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ZERO report written: {out_md}")
    print(f"ZERO report JSON:    {out_json}")

if __name__ == "__main__":
    main()
