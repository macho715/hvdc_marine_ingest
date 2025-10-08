#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
map_leaflet.py — INLINE GeoJSON + 임시 화살표(leaflet polyline), WW3 Hs WMS 오버레이
Usage:
  python map_leaflet.py --geo out/wind_uv.geojson --out out/map_leaflet.html \
    --wms https://erddap.aoml.noaa.gov/hdb/erddap/wms/WaveWatch_2021/request \
    --layer WaveWatch_2021:whgt --site AGI
"""
import json, argparse, math
from pathlib import Path
from datetime import datetime

AGI = (24.843833, 53.655306)
DAS = (25.151300, 52.871700)

HTML_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Marine Viz — Leaflet (inline JSON + arrows)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html,body,#map{height:100%%;margin:0}
  .legend{position:absolute;bottom:12px;left:12px;background:#fff;padding:8px 10px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15);font:12px/1.4 system-ui,Segoe UI,Arial}
</style>
</head>
<body>
<div id="map"></div>

<!-- 인라인 GeoJSON (CORS 우회) -->
<script id="wind-data" type="application/json">
__WIND_GEOJSON__
</script>

<div class="legend">
  <div><b>Layers</b></div>
  <div>• Hs (WW3 WMS: <code>%(layer)s</code>)</div>
  <div>• Wind vectors (arrows from u/v)</div>
  <div>Units: Hs m, Wind kt</div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const SITE   = %(site)s;
const CENTER = [%(lat).6f, %(lon).6f];
const WMS_URL   = %(wms)s;
const WMS_LAYER = %(layer_json)s;

const map = L.map('map', { zoomControl: true }).setView(CENTER, 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom: 12, attribution:'© OpenStreetMap'
}).addTo(map);

// 1) 파고(Hs) — WW3(ERDDAP) WMS
const hs = L.tileLayer.wms(WMS_URL, {
  layers: WMS_LAYER, format: 'image/png', transparent: true, opacity: 0.65
}).addTo(map);

// 2) 바람 벡터 — 인라인 GeoJSON에서 u,v로 화살표 그리기
const gj = JSON.parse(document.getElementById('wind-data').textContent || "{}");

// 간단 화살표 드로잉: 시작점(lat,lon) → u/v를 deg 보정해 끝점까지 폴리라인
// 참고: 1°위도 ≈ 111km, 경도는 위도에 따라 111km*cos(lat)
const RAD = Math.PI/180;
const K = 0.015; // 화살 길이 스케일(보기 좋은 정도로 조정)

function drawArrows(geojson){
  if(!geojson || !geojson.features){ return; }
  for(const f of geojson.features){
    const lon = f.geometry.coordinates[0];
    const lat = f.geometry.coordinates[1];
    const u_ms = Number(f.properties.u_ms) || 0;  // 동서(+동, -서)
    const v_ms = Number(f.properties.v_ms) || 0;  // 남북(+북, -남)

    const dlat = K * v_ms;                        // 단순 스케일 (시각화용)
    const dlon = K * u_ms / Math.cos(lat*RAD);    // 경도 축소 보정
    const lat2 = lat + dlat;
    const lon2 = lon + dlon;

    // 본체
    L.polyline([[lat, lon], [lat2, lon2]], {
      color:'#0a84ff', weight:1.5, opacity:0.9
    }).addTo(map);

    // 간단 화살촉(끝점 근처 보조선)
    const backLat = lat2 - 0.3*dlat, backLon = lon2 - 0.3*dlon;
    const orthoLat = -dlon, orthoLon = dlat; // 직교 벡터
    const tip1 = [backLat + 0.15*orthoLat, backLon + 0.15*orthoLon];
    const tip2 = [backLat - 0.15*orthoLat, backLon - 0.15*orthoLon];
    L.polyline([[tip1[0], tip1[1]], [lat2, lon2], [tip2[0], tip2[1]]], {
      color:'#0a84ff', weight:1.2, opacity:0.9
    }).addTo(map);
  }
}
drawArrows(gj);

// 중심 마커
L.marker(CENTER).addTo(map).bindTooltip(SITE + " center");
</script>
</body></html>
"""

def _fallback_geojson(center):
    """입력이 없을 때 샘플 u/v 포인트 생성(남서풍 느낌)"""
    lat0, lon0 = center
    feats = []
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    for i in range(1, 7):
        for deg in range(0, 360, 30):
            r_km = i * 6.0
            rad = math.radians(deg)
            dlat = (r_km/111.0)*math.cos(rad)
            dlon = (r_km/(111.0*math.cos(math.radians(lat0))))*math.sin(rad)
            lat = lat0 + dlat; lon = lon0 + dlon
            spd = 8.0 * max(0.25, 1.0 - i/8.0)         # m/s
            wdir = (225 + deg) % 360                   # 바람이 불어오는 방향
            u = -spd * math.sin(math.radians(wdir))    # u/v 변환
            v = -spd * math.cos(math.radians(wdir))
            feats.append({
                "type":"Feature",
                "geometry":{"type":"Point","coordinates":[round(lon,6), round(lat,6)]},
                "properties":{
                    "time": now, "wind_speed_ms": round(spd,2), "wind_dir_deg": round(wdir,1),
                    "u_ms": round(u,3), "v_ms": round(v,3)
                }
            })
    return {"type":"FeatureCollection","features":feats}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", default="out/wind_uv.geojson")
    ap.add_argument("--out", default="out/map_leaflet.html")
    ap.add_argument("--wms", default="https://erddap.aoml.noaa.gov/hdb/erddap/wms/WaveWatch_2021/request")
    ap.add_argument("--layer", default="WaveWatch_2021:whgt")  # WW3: 유의파고 변수 예시
    ap.add_argument("--site", default="AGI", choices=["AGI","DAS"])
    args = ap.parse_args()

    center = AGI if args.site == "AGI" else DAS
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # GeoJSON 로드(없으면 샘플 생성)
    gj_path = Path(args.geo)
    if gj_path.exists():
        gj_text = gj_path.read_text(encoding="utf-8")
    else:
        gj_text = json.dumps(_fallback_geojson(center), ensure_ascii=False)

    html = HTML_TMPL % {
        "site": json.dumps(args.site),
        "lat": center[0], "lon": center[1],
        "wms": json.dumps(args.wms),
        "layer": args.layer,
        "layer_json": json.dumps(args.layer),
    }
    # 인라인 주입
    html = html.replace("__WIND_GEOJSON__", gj_text)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
