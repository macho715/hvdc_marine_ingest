#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adapter.py — Open-Meteo(바람) + Marine(파고) 동시 호출 → u/v + Hs GeoJSON
Usage:
  python adapter.py --out out/wind_uv.geojson --site AGI --hours 72 --radius_km 30
옵션:
  --lat/--lon 직접 좌표 지정 가능. 기본은 AGI.
"""
import argparse, json, math, os
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import requests

AGI = (24.843833, 53.655306)
DAS = (25.151300, 52.871700)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"          # wind
MARINE_URL   = "https://marine-api.open-meteo.com/v1/marine"      # waves

def to_uv(speed_ms: float, dir_deg: float):
    rad = math.radians(dir_deg)
    u = -speed_ms * math.sin(rad)   # 동(+)/서(-)
    v = -speed_ms * math.cos(rad)   # 북(+)/남(-)
    return u, v

def fetch_openmeteo(lat, lon, hours):
    """wind_speed_10m, wind_direction_10m — hourly 시계열"""
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "forecast_days": 7, "timezone": "UTC"
    }
    r = requests.get(FORECAST_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def fetch_marine(lat, lon, hours):
    """marine: wave_height, wave_direction, wave_period — hourly 시계열"""
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "wave_height,wave_direction,wave_period",
        "forecast_days": 7, "timezone": "UTC"
    }
    r = requests.get(MARINE_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def nearest_index(iso_list, target_iso):
    # iso_list: ["2025-10-08T12:00", ...] 형태(분까지) → 끝에 'Z' 붙여 조정
    tgt = datetime.fromisoformat(target_iso.replace("Z","")).replace(tzinfo=timezone.utc)
    best_i, best_dt = 0, None
    for i, s in enumerate(iso_list):
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
        if best_dt is None or abs((dt - tgt).total_seconds()) < abs((best_dt - tgt).total_seconds()):
            best_i, best_dt = i, dt
    return best_i

def radial_points(center, radius_km=30.0, rings=6, step_deg=20):
    lat0, lon0 = center
    pts = []
    ring_step = max(1, int(rings))
    for i in range(1, ring_step+1):
        r_km = radius_km * (i / ring_step)
        for deg in range(0, 360, step_deg):
            rad = math.radians(deg)
            dlat = (r_km/111.0) * math.cos(rad)
            dlon = (r_km/(111.0*math.cos(math.radians(lat0)))) * math.sin(rad)
            pts.append((round(lat0+dlat,6), round(lon0+dlon,6)))
    return pts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/wind_uv.geojson")
    ap.add_argument("--site", default="AGI", choices=["AGI","DAS"])
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--hours", type=int, default=72)
    ap.add_argument("--radius_km", type=float, default=30.0)
    ap.add_argument("--rings", type=int, default=6)
    ap.add_argument("--step_deg", type=int, default=20)
    ap.add_argument("--time", default=None, help="ISO8601(UTC) 선택 시각. 미지정 시 현재시각(H) 라운드")
    args = ap.parse_args()

    center = (args.lat, args.lon) if (args.lat and args.lon) else (AGI if args.site=="AGI" else DAS)
    # 선택 시각: 현재 UTC의 정시
    if args.time:
        target_iso = args.time if args.time.endswith("Z") else args.time + "Z"
    else:
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        target_iso = now.isoformat(timespec="seconds")+"Z"

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_wind   = ex.submit(fetch_openmeteo, center[0], center[1], args.hours)
        f_marine = ex.submit(fetch_marine,   center[0], center[1], args.hours)
        wind_json   = f_wind.result()
        marine_json = f_marine.result()

    # 시계열 정렬(가장 가까운 시각)
    wt = [t.replace(":00Z","").replace("Z","") if t.endswith("Z") else t for t in wind_json["hourly"]["time"]]
    mt = [t.replace(":00Z","").replace("Z","") if t.endswith("Z") else t for t in marine_json["hourly"]["time"]]
    i_w = nearest_index(wt, target_iso)
    i_m = nearest_index(mt, target_iso)

    ws  = float(wind_json["hourly"]["wind_speed_10m"][i_w])
    wd  = float(wind_json["hourly"]["wind_direction_10m"][i_w])
    hs  = float(marine_json["hourly"]["wave_height"][i_m])
    wvD = float(marine_json["hourly"]["wave_direction"][i_m])
    wvP = float(marine_json["hourly"]["wave_period"][i_m])

    u, v = to_uv(ws, wd)

    # 지도용 포인트들(동심원 샘플). 모든 포인트에 동일 시각 값 주입(격자 계산은 다음 단계에서 확장)
    samples = radial_points(center, radius_km=args.radius_km, rings=args.rings, step_deg=args.step_deg)
    feats = []
    for (lat, lon) in samples:
        feats.append({
            "type":"Feature",
            "geometry":{"type":"Point","coordinates":[lon, lat]},
            "properties":{
                "time": target_iso,
                "wind_speed_ms": round(ws,2), "wind_dir_deg": round(wd,1),
                "u_ms": round(u,3), "v_ms": round(v,3),
                "wave_height_m": round(hs,2), "wave_dir_deg": round(wvD,1), "wave_period_s": round(wvP,1)
            }
        })

    gj = {"type":"FeatureCollection","features":feats}
    meta = {
        "center":{"lat":center[0],"lon":center[1]}, "site": args.site, "time_used": target_iso,
        "sources":{"wind": FORECAST_URL, "marine": MARINE_URL}, "count": len(feats)
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    Path(args.out).with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out} ({len(feats)} pts) @ {target_iso}")

if __name__ == "__main__":
    main()
