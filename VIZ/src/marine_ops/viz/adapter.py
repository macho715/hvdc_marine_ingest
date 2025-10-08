#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adapter.py — GIS 어댑터 (wind_speed/dir → u/v GeoJSON, Hs 메타)
Usage:
  python adapter.py --wind in/wind.csv --out out/wind_uv.geojson --site AGI
입력 CSV 형식(예시):
  lat,lon,time_iso,wind_speed_ms,wind_dir_deg,wave_height_m
설명:
  - 풍향은 "바람이 불어오는 방향"(기상학 표준, °: 0=북, 90=동).
  - u/v 변환: u = -speed * sin(dir_rad), v = -speed * cos(dir_rad)
  - 입력이 없으면 AGI 주변 샘플 격자를 생성합니다.
"""
import csv, json, math, argparse, os
from pathlib import Path
from datetime import datetime

AGI = (24.843833, 53.655306)
DAS = (25.151300, 52.871700)

def to_uv(speed_ms: float, dir_deg: float):
    import math
    rad = math.radians(dir_deg)
    u = -speed_ms * math.sin(rad)
    v = -speed_ms * math.cos(rad)
    return u, v

def fallback_grid(center, rings=8, step_km=6.0, base_speed=8.0):
    lat0, lon0 = center
    rows = []
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for i in range(1, rings+1):
        r_km = i*step_km
        for deg in range(0, 360, 15):
            rad = math.radians(deg)
            dlat = (r_km/111.0)*math.cos(rad)
            dlon = (r_km/(111.0*math.cos(math.radians(lat0))))*math.sin(rad)
            lat = lat0 + dlat; lon = lon0 + dlon
            spd = base_speed * max(0.2, 1.0 - i/(rings+1))
            wdir = (225 + deg) % 360  # 남서풍 느낌
            hs = 0.6 + 0.02*i
            rows.append({
                "lat": round(lat, 6), "lon": round(lon, 6), "time_iso": now,
                "wind_speed_ms": round(spd, 2), "wind_dir_deg": round(wdir, 1),
                "wave_height_m": round(hs, 2)
            })
    return rows

def read_csv_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        dr = csv.DictReader(f)
        for r in dr:
            try:
                rows.append({
                    "lat": float(r["lat"]), "lon": float(r["lon"]),
                    "time_iso": r.get("time_iso",""),
                    "wind_speed_ms": float(r.get("wind_speed_ms", 0.0)),
                    "wind_dir_deg": float(r.get("wind_dir_deg", 0.0)),
                    "wave_height_m": float(r.get("wave_height_m", 0.0)),
                })
            except Exception:
                continue
    return rows

def to_geojson(rows):
    feats = []
    for r in rows:
        u, v = to_uv(r["wind_speed_ms"], r["wind_dir_deg"])
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "time": r["time_iso"],
                "wind_speed_ms": r["wind_speed_ms"],
                "wind_dir_deg": r["wind_dir_deg"],
                "u_ms": round(u, 3), "v_ms": round(v, 3),
                "wave_height_m": r["wave_height_m"]
            }
        })
    return {"type": "FeatureCollection", "features": feats}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wind", default="", help="입력 wind CSV (없으면 샘플 생성)")
    ap.add_argument("--out", default="out/wind_uv.geojson")
    ap.add_argument("--site", default="AGI", choices=["AGI","DAS"])
    ap.add_argument("--hs_wms", default="https://erddap.aoml.noaa.gov/hdb/erddap/wms/WaveWatch_2021/request")
    ap.add_argument("--hs_layer", default="WaveWatch_2021:hs")
    args = ap.parse_args()

    center = AGI if args.site == "AGI" else DAS
    if args.wind and os.path.exists(args.wind):
        rows = read_csv_rows(args.wind)
    else:
        rows = fallback_grid(center)

    gj = to_geojson(rows)
    meta = {
        "site": args.site,
        "center": {"lat": center[0], "lon": center[1]},
        "hs_wms": args.hs_wms, "hs_layer": args.hs_layer,
        "count": len(gj["features"])
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)
    with open(Path(args.out).with_suffix(".meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Wrote {args.out} ({meta['count']} pts)")

if __name__ == "__main__":
    main()
