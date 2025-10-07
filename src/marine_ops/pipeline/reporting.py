"""Reporting helpers for the 72-hour marine pipeline."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
from zoneinfo import ZoneInfo

from src.marine_ops.pipeline.config import PipelineConfig


def _decisions_to_rows(
    location: str,
    decisions: Dict[str, Dict[str, Dict[str, object]]],
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for day_label, parts in decisions.items():
        for part_name, payload in parts.items():
            row = {
                "location": location,
                "day": day_label,
                "daypart": part_name,
            }
            row.update(payload)
            rows.append(row)
    return rows


def _safe_json(value):
        if isinstance(value, float) and (pd.isna(value) or pd.isnull(value)):
            return None
        if isinstance(value, dict):
            return {k: _safe_json(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_safe_json(item) for item in value]
        return value


def render_html_3d(
    run_ts: datetime,
    cfg: PipelineConfig,
    agi: Dict[str, Dict[str, Dict[str, object]]],
    das: Dict[str, Dict[str, Dict[str, object]]],
    route_windows: Iterable[Dict[str, object]],
    ncm_alerts: Iterable[str],
    out_dir: str = "out",
) -> Path:
    output_dir = Path(out_dir)
    output_dir.mkdir(exist_ok=True)

    local_ts = run_ts.astimezone(ZoneInfo(cfg.tz))
    timestamp_label = local_ts.strftime("%Y%m%d_%H%M")
    html_path = output_dir / f"summary_3d_{timestamp_label}.html"

    agi_rows = pd.DataFrame(_decisions_to_rows("AGI", agi))
    das_rows = pd.DataFrame(_decisions_to_rows("DAS", das))
    route_rows = pd.DataFrame(list(route_windows)) if route_windows else pd.DataFrame()

    def _render_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "<p>No data available.</p>"
        friendly = df.copy()
        friendly = friendly.drop(columns=[col for col in friendly.columns if col.startswith("alerts_")], errors="ignore")
        return friendly.to_html(index=False, classes="table", justify="center", border=0)

    html = f"""
<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>72h Marine Report {timestamp_label}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #111; }}
h1 {{ color: #004c97; }}
section {{ margin-bottom: 32px; }}
.table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
.table th, .table td {{ border: 1px solid #ddd; padding: 6px; text-align: center; }}
.badge {{ display: inline-block; padding: 4px 8px; margin-right: 6px; border-radius: 4px; background: #eef; color: #004c97; }}
</style>
</head>
<body>
<h1>72h Marine Report — {local_ts.strftime('%Y-%m-%d %H:%M %Z')}</h1>
<section>
  <h2>Executive Summary</h2>
  <p>Configured locations: {', '.join(cfg.location_ids())}. Forecast horizon: {cfg.forecast_hours} hours.</p>
  <p>NCM alerts detected: {'None' if not ncm_alerts else ', '.join(ncm_alerts)}</p>
</section>
<section>
  <h2>Route Windows (MW4 ↔ AGI)</h2>
  {_render_table(route_rows)}
</section>
<section>
  <h2>AGI Daypart Decisions</h2>
  {_render_table(agi_rows)}
</section>
<section>
  <h2>DAS Daypart Decisions</h2>
  {_render_table(das_rows)}
</section>
</body>
</html>
"""

    html_path.write_text(html, encoding="utf-8")
    return html_path


def write_side_outputs(
    run_ts: datetime,
    cfg: PipelineConfig,
    agi: Dict[str, Dict[str, Dict[str, object]]],
    das: Dict[str, Dict[str, Dict[str, object]]],
    route_windows: Iterable[Dict[str, object]],
    ncm_alerts: Iterable[str],
    api_status: Dict[str, Dict[str, str]],
    out_dir: str = "out",
) -> Dict[str, Path]:
    output_dir = Path(out_dir)
    output_dir.mkdir(exist_ok=True)
    local_ts = run_ts.astimezone(ZoneInfo(cfg.tz))
    timestamp_label = local_ts.strftime("%Y%m%d_%H%M")

    agi_rows = _decisions_to_rows("AGI", agi)
    das_rows = _decisions_to_rows("DAS", das)
    combined_rows = agi_rows + das_rows

    json_payload = {
        "generated_at": local_ts.isoformat(),
        "tz": cfg.tz,
        "alerts": list(ncm_alerts),
        "route_windows": list(route_windows),
        "decisions": {
            "AGI": agi,
            "DAS": das,
        },
        "api_status": api_status,
    }

    json_path = output_dir / f"summary_3d_{timestamp_label}.json"
    json_path.write_text(json.dumps(_safe_json(json_payload), ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = output_dir / f"summary_3d_{timestamp_label}.csv"
    if combined_rows:
        pd.DataFrame(combined_rows).to_csv(csv_path, index=False)
    else:
        csv_path.write_text("", encoding="utf-8")

    txt_lines = [
        f"72h Marine Report ({local_ts.strftime('%Y-%m-%d %H:%M %Z')})",
        f"Alerts: {'None' if not ncm_alerts else ', '.join(ncm_alerts)}",
        "",
        "Route windows:",
    ]
    windows = list(route_windows)
    if not windows:
        txt_lines.append("  (none)")
    else:
        for item in windows:
            txt_lines.append(
                f"  - {item.get('label')}: {item.get('agi_decision')}/{item.get('das_decision')} (start {item.get('start')})"
            )

    txt_lines.append("")
    for location, rows in (("AGI", agi_rows), ("DAS", das_rows)):
        txt_lines.append(f"{location} dayparts:")
        if not rows:
            txt_lines.append("  (no data)")
            continue
        df = pd.DataFrame(rows)
        for _, row in df.iterrows():
            hs_value = row.get("hs_p90") if not pd.isna(row.get("hs_p90")) else row.get("hs_mean")
            wind_value = row.get("wind_p90_kt") if not pd.isna(row.get("wind_p90_kt")) else row.get("wind_mean_kt")
            if pd.isna(hs_value):
                summary_line = f"  - {row['day']} {row['daypart']}: {row.get('decision', 'N/A')}"
            else:
                hs_str = f"{hs_value:.2f} m" if hs_value is not None else "N/A"
                wind_str = f"{wind_value:.1f} kt" if wind_value is not None and not pd.isna(wind_value) else "N/A"
                summary_line = (
                    f"  - {row['day']} {row['daypart']}: {row.get('decision', 'N/A')} "
                    f"(Hs~{hs_str}, Wind~{wind_str})"
                )
            txt_lines.append(summary_line)
        txt_lines.append("")

    txt_path = output_dir / f"summary_3d_{timestamp_label}.txt"
    txt_path.write_text("\n".join(txt_lines), encoding="utf-8")

    return {"json": json_path, "csv": csv_path, "txt": txt_path}
