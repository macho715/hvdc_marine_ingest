#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
map_leaflet.py — Inline GeoJSON + 화살표 + WW3 WMS(time=ISO or 'current')
Usage:
  python map_leaflet.py --geo out/wind_uv.geojson --out out/map_leaflet.html \
    --wms https://erddap.aoml.noaa.gov/hdb/erddap/wms/WaveWatch_2021/request \
    --layer WaveWatch_2021:whgt --site AGI --time current
"""
import json, argparse
from pathlib import Path
from datetime import datetime, timezone

AGI = (24.843833, 53.655306)
DAS = (25.151300, 52.871700)

HTML_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Marine Viz — Leaflet (inline JSON + arrows + WMS time)</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html,body,#map{height:100%%;margin:0}
  .legend{position:absolute;bottom:12px;left:12px;background:#fff;padding:8px 10px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15);font:12px/1.4 system-ui,Segoe UI,Arial}
  code{background:#f6f8fa;padding:0 4px;border-radius:4px}
</style>
</head>
<body>
<div id="map"></div>

<!-- 인라인 GeoJSON (CORS 無) -->
<script id="wind-data" type="application/json">
__WIND_GEOJSON__
</script>

<div class="legend">
  <div><b>Layers</b></div>
  <div>• Hs (WMS: <code>%(layer)s</code>)</div>
  <div>• Wind vectors (u/v arrows)</div>
  <div>time: <code>%(time_str)s</code> · Units: Hs m, Wind kt</div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/esri-leaflet/dist/esri-leaflet.js"></script>
<script>
const SITE   = %(site)s;
const CENTER = [%(lat).6f, %(lon).6f];
const WMS_URL   = %(wms)s;
const WMS_LAYER = %(layer_json)s;
const WMS_TIME  = %(wms_time)s; // 'current' or ISO8601

const map = L.map('map', { zoomControl: true }).setView(CENTER, 7);

// 1) Ocean Base (우선) - Esri World Ocean Base
L.esri.basemapLayer('Oceans').addTo(map);

// 2) OSM (보조) - 필요 시 토글
const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom: 12, attribution:'© OpenStreetMap'
});

// Hs (WW3) — WMS tile layer with time + 컬러스케일 강화
const hs = L.tileLayer.wms(WMS_URL, {
  layers: WMS_LAYER, 
  format: 'image/png', 
  transparent: true, 
  opacity: 0.70,
  time: WMS_TIME,
  COLORSCALERANGE: '0,2.5',          // 걸프 평시 가독 범위
  NUMCOLORBANDS: 40,
  PALETTE: 'rainbow'
}).addTo(map);

// Wind arrows — 픽셀 기반 벡터 (줌 안정)
const gj = JSON.parse(document.getElementById('wind-data').textContent || "{}");

function drawArrows(gj){
  if(!gj || !gj.features){return;}
  // 이전 벡터 지우기
  if (window._windLayer) { map.removeLayer(window._windLayer); }
  window._windLayer = L.layerGroup().addTo(map);

  const RAD = Math.PI/180;
  const MIN = 6, MAX = 28;          // 화살 최소/최대 길이(px)
  const PX_PER_KT = 0.9;            // 1 kt 당 픽셀 스케일 (필요시 0.6~1.2 조정)

  for (const f of gj.features){
    const lon = f.geometry.coordinates[0], lat = f.geometry.coordinates[1];
    const u = Number(f.properties.u_ms) || 0;     // +동/-서
    const v = Number(f.properties.v_ms) || 0;     // +북/-남
    const spd_ms = Math.hypot(u, v);
    if (spd_ms < 0.1) continue;

    const spd_kt = spd_ms * 1.94384;
    let Lpx = Math.min(MAX, Math.max(MIN, PX_PER_KT * spd_kt));

    // 픽셀 벡터: x는 동(+), y는 남(+) 주의 → Leaflet 화면좌표는 y가 아래로 증가
    const unitX =  u / spd_ms;
    const unitY = -v / spd_ms;      // 북(+)면 화면 y는 감소하므로 부호 반전
    const start = map.latLngToLayerPoint([lat, lon]);
    const end   = L.point(start.x + Lpx*unitX, start.y + Lpx*unitY);
    const endLL = map.layerPointToLatLng(end);

    // 색상 맵 (kt)
    const col = spd_kt < 10 ? '#5B9BD5' : (spd_kt < 20 ? '#1F77B4' : '#0A3D91');

    L.polyline([[lat, lon], endLL], {color: col, weight: 1.7, opacity: 0.9})
      .addTo(window._windLayer);

    // 간단 화살촉
    const back = L.point(start.x + 0.7*(end.x - start.x), start.y + 0.7*(end.y - start.y));
    const ortho = L.point(-(end.y - start.y), (end.x - start.x)); // 직교 벡터
    const tip1  = map.layerPointToLatLng(L.point(back.x + 0.12*ortho.x, back.y + 0.12*ortho.y));
    const tip2  = map.layerPointToLatLng(L.point(back.x - 0.12*ortho.x, back.y - 0.12*ortho.y));
    L.polyline([tip1, endLL, tip2], {color: col, weight: 1.1, opacity: 0.9})
      .addTo(window._windLayer);
  }
}

drawArrows(gj);

// 줌/이동 시 길이 재계산(픽셀 기준 유지)
function rerender() { drawArrows(gj); }
map.on('zoomend moveend', rerender);

// center marker
L.marker(CENTER).addTo(map).bindTooltip(SITE + " center");
</script>
</body></html>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", default="out/wind_uv.geojson")
    ap.add_argument("--out", default="out/map_leaflet.html")
    ap.add_argument("--wms", default="https://erddap.aoml.noaa.gov/hdb/erddap/wms/WaveWatch_2021/request")
    ap.add_argument("--layer", default="WaveWatch_2021:whgt")
    ap.add_argument("--site", default="AGI", choices=["AGI","DAS"])
    ap.add_argument("--time", default=None, help="'current' 또는 ISO8601(UTC, 예: 2025-10-08T12:00:00Z)")
    args = ap.parse_args()

    center = AGI if args.site=="AGI" else DAS
    out_path = Path(args.out); out_path.parent.mkdir(parents=True, exist_ok=True)

    # time 문자열 준비
    if args.time:
        wms_time = args.time
        time_str = args.time
    else:
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        time_str = now.isoformat(timespec="seconds")+"Z"
        wms_time = time_str

    gj_text = Path(args.geo).read_text(encoding="utf-8") if Path(args.geo).exists() else json.dumps({"type":"FeatureCollection","features":[]})
    html = HTML_TMPL % {
        "site": json.dumps(args.site),
        "lat": center[0], "lon": center[1],
        "wms": json.dumps(args.wms),
        "layer": args.layer, "layer_json": json.dumps(args.layer),
        "wms_time": json.dumps(wms_time), "time_str": time_str
    }
    html = html.replace("__WIND_GEOJSON__", gj_text)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out} (time={wms_time})")

if __name__ == "__main__":
    main()
