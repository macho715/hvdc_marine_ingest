"""Promote ZERO marine reports to NORMAL when data is available."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

REPORT_ROOT = Path("reports")
DATA_ROOT = Path("data")
DAYPARTS = (
    ("Dawn", time(3, 0), time(6, 0)),
    ("Morning", time(6, 0), time(12, 0)),
    ("Afternoon", time(12, 0), time(17, 0)),
    ("Evening", time(17, 0), time(22, 0)),
)
GO_THRESHOLDS = {
    "wave": 1.00,
    "wind": 20.0,
}
CONDITIONAL_THRESHOLDS = {
    "wave": 1.20,
    "wind": 22.0,
}


@dataclass
class TransitionInput:
    csv_path: Path
    zero_path: Optional[Path]


@dataclass
class DaypartSummary:
    hs_m: Optional[float]
    wind_kt: Optional[float]
    vis_km: Optional[float]
    warning: str
    gate: str


@dataclass
class TransitionResult:
    markdown_path: Path
    json_path: Path
    supersedes_path: Optional[Path]


class TransitionError(RuntimeError):
    """Raised when ZERO->NORMAL transition cannot be performed."""


def _latest_file(paths: Iterable[Path]) -> Optional[Path]:
    paths = list(paths)
    if not paths:
        return None
    return max(paths, key=lambda p: p.stat().st_mtime)


def _resolve_inputs(csv_hint: Optional[str]) -> TransitionInput:
    if csv_hint:
        csv_path = Path(csv_hint)
        if not csv_path.exists():
            raise TransitionError(f"CSV not found: {csv_path}")
    else:
        candidates = list(DATA_ROOT.glob("marine_*.csv")) + list(
            DATA_ROOT.glob("marine_playwright_*.csv")
        )
        csv_path = _latest_file(candidates)
        if csv_path is None:
            raise TransitionError("No marine CSV files available in data/ directory.")

    zero_path = _latest_file(REPORT_ROOT.glob("NCM_ZERO_*.json"))
    return TransitionInput(csv_path=csv_path, zero_path=zero_path)


def _match_column(df: pd.DataFrame, *aliases: str) -> Optional[str]:
    lower_map = {c.lower(): c for c in df.columns}
    for alias in aliases:
        name = lower_map.get(alias.lower())
        if name:
            return name
    return None


def _infer_daypart(dt: datetime) -> str:
    t = dt.time()
    for name, start, end in DAYPARTS:
        if start <= t < end:
            return name
    return "Other"


def _normalise_frame(df: pd.DataFrame) -> pd.DataFrame:
    copy = df.copy()
    ts_column = _match_column(copy, "timestamp", "time", "datetime", "valid_time")
    if not ts_column:
        raise TransitionError("No timestamp column found in CSV.")

    copy["_ts"] = pd.to_datetime(copy[ts_column], errors="coerce", utc=True)
    copy = copy.dropna(subset=["_ts"])
    if copy.empty:
        raise TransitionError("All timestamp rows are invalid after parsing.")

    copy["daypart"] = copy["_ts"].dt.tz_convert("UTC").apply(_infer_daypart)

    wave_col = _match_column(copy, "hs", "hs_m", "wave_m")
    wind_col = _match_column(copy, "wind", "wind_speed", "wind_speed_kt", "wind_kt")
    vis_col = _match_column(copy, "vis", "visibility", "visibility_km", "vis_km")
    warn_col = _match_column(copy, "warning", "warnings", "alert", "alerts", "ncm_warning")

    for target, source in ("hs_m", wave_col), ("wind_kt", wind_col), ("vis_km", vis_col):
        if source:
            copy[target] = pd.to_numeric(copy[source], errors="coerce")
        else:
            copy[target] = pd.NA

    copy["warning_text"] = copy[warn_col] if warn_col else ""
    return copy


def _gate_outcome(hs: Optional[float], wind: Optional[float], warning: str) -> str:
    warning = (warning or "").strip().lower()
    if warning and warning not in {"none", "ok", "normal"}:
        return "NO-GO"
    if hs is not None and wind is not None:
        if hs <= GO_THRESHOLDS["wave"] and wind <= GO_THRESHOLDS["wind"]:
            return "GO"
        if hs <= CONDITIONAL_THRESHOLDS["wave"] and wind <= CONDITIONAL_THRESHOLDS["wind"]:
            return "CONDITIONAL"
        return "NO-GO"
    if hs is not None:
        if hs <= GO_THRESHOLDS["wave"]:
            return "GO"
        if hs <= CONDITIONAL_THRESHOLDS["wave"]:
            return "CONDITIONAL"
        return "NO-GO"
    if wind is not None:
        if wind <= GO_THRESHOLDS["wind"]:
            return "GO"
        if wind <= CONDITIONAL_THRESHOLDS["wind"]:
            return "CONDITIONAL"
        return "NO-GO"
    return "UNKNOWN"


def _summarise_dayparts(df: pd.DataFrame) -> dict[str, DaypartSummary]:
    summaries: dict[str, DaypartSummary] = {}
    for name, _, _ in DAYPARTS:
        slot = df[df["daypart"] == name]
        if slot.empty:
            summaries[name] = DaypartSummary(None, None, None, "N/A", "N/A")
            continue
        hs = slot["hs_m"].median(skipna=True) if "hs_m" in slot else None
        hs_val = float(hs) if hs is not None and pd.notna(hs) else None
        wind = slot["wind_kt"].median(skipna=True) if "wind_kt" in slot else None
        wind_val = float(wind) if wind is not None and pd.notna(wind) else None
        vis = slot["vis_km"].median(skipna=True) if "vis_km" in slot else None
        vis_val = float(vis) if vis is not None and pd.notna(vis) else None
        warning = ""
        if "warning_text" in slot and slot["warning_text"].notna().any():
            warning = str(slot["warning_text"].dropna().mode().iat[0])
        warning = warning or "None"
        gate = _gate_outcome(hs_val, wind_val, warning)
        summaries[name] = DaypartSummary(hs_val, wind_val, vis_val, warning, gate)
    return summaries


def _format_value(value: Optional[float], unit: str) -> str:
    if value is None:
        return "N/A"
    precision = 2 if unit == "m" else 1 if unit == "kt" else 1
    return f"{value:.{precision}f}{unit}"


def _render_markdown(summary: dict[str, DaypartSummary], zero_name: Optional[str]) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Marine Weather Report — NORMAL", "", f"Run: {timestamp}", ""]
    if zero_name:
        lines.extend((f"Supersedes: `{zero_name}`", ""))
    lines.append("Daypart | Wave | Wind | Visibility | Warning | Gate")
    lines.append("---|---|---|---|---|---")
    for name, _, _ in DAYPARTS:
        part = summary[name]
        lines.append(
            " | ".join(
                [
                    name,
                    _format_value(part.hs_m, "m"),
                    _format_value(part.wind_kt, "kt"),
                    _format_value(part.vis_km, "km"),
                    part.warning,
                    part.gate,
                ]
            )
        )
    lines.append("")
    return "\n".join(lines)


def _write_outputs(
    summary: dict[str, DaypartSummary], zero_path: Optional[Path]
) -> TransitionResult:
    REPORT_ROOT.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    markdown_path = REPORT_ROOT / f"NCM_REPORT_{timestamp}.md"
    json_path = REPORT_ROOT / f"NCM_REPORT_{timestamp}.json"
    markdown = _render_markdown(summary, zero_path.name if zero_path else None)
    markdown_path.write_text(markdown, encoding="utf-8")
    json_payload = {
        name: {
            "hs_m": part.hs_m,
            "wind_kt": part.wind_kt,
            "vis_km": part.vis_km,
            "warning": part.warning,
            "gate": part.gate,
        }
        for name, part in summary.items()
    }
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    supersedes_path: Optional[Path] = None
    if zero_path:
        supersedes_path = REPORT_ROOT / "SUPERSEDES.json"
        supersedes_payload = {
            "zero": zero_path.name,
            "normal": markdown_path.name,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        supersedes_path.write_text(
            json.dumps(supersedes_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return TransitionResult(markdown_path, json_path, supersedes_path)


def perform_transition(csv_hint: Optional[str]) -> TransitionResult:
    inputs = _resolve_inputs(csv_hint)
    df = pd.read_csv(inputs.csv_path)
    normalised = _normalise_frame(df)
    summary = _summarise_dayparts(normalised)
    return _write_outputs(summary, inputs.zero_path)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert ZERO marine report to NORMAL when data CSV is present."
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        help="Explicit CSV path (defaults to latest marine_*.csv or marine_playwright_*.csv)",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        result = perform_transition(args.csv_path)
    except TransitionError as exc:
        print(f"[ZERO->NORMAL] {exc}")
        return 1

    print(f"[NORMAL] Markdown: {result.markdown_path}")
    print(f"[NORMAL] JSON: {result.json_path}")
    if result.supersedes_path:
        print(f"[NORMAL] Supersedes manifest: {result.supersedes_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
