#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
map_leaflet.py — Leaflet 지도(WW3 Hs WMS + leaflet-velocity 바람) HTML 생성
Usage:
  python map_leaflet.py --geo out/wind_uv.geojson --out out/map_leaflet.html \
    --wms https://erddap.aoml.noaa.gov/hdb/erddap/wms/WaveWatch_2021/request \
    --layer WaveWatch_2021:hs --site AGI
"""
import json, argparse
from pathlib import Path

AGI = (24.843833, 53.655306)
DAS = (25.151300, 52.871700)

HTML_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Marine Viz — Leaflet</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
  html,body,#map{height:100%;margin:0}
  .legend{position:absolute;bottom:12px;left:12px;background:#fff;padding:8px 10px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.15);font:12px/1.4 system-ui,Segoe UI,Arial}
</style>
</head>
<body>
<div id="map"></div>
<div class="legend">
  <div><b>Layers</b></div>
  <div>• Hs (WW3 WMS)</div>
  <div>• Wind (leaflet-velocity)</div>
  <div>Units: Hs m, Wind kt</div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<!-- leaflet-velocity (jsDelivr CDN) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-velocity@2.1.4/src/css/leaflet-velocity.css"/>
<script src="https://cdn.jsdelivr.net/npm/leaflet-velocity@2.1.4/src/js/L.CanvasLayer.js"></script>
<script src="https://cdn.jsdelivr.net/npm/leaflet-velocity@2.1.4/src/js/L.VelocityLayer.js"></script>
<script src="https://cdn.jsdelivr.net/npm/leaflet-velocity@2.1.4/src/js/L.Control.Velocity.js"></script>
<script>
const SITE = %(site)s;
const CENTER = [%(lat).6f, %(lon).6f];
const WMS_URL = %(wms)s;
const WMS_LAYER = %(layer)s;

const map = L.map('map', { zoomControl: true }).setView(CENTER, 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
  maxZoom: 12, attribution:'© OpenStreetMap'
}).addTo(map);

// Hs (WW3) — WMS tile layer
const hs = L.tileLayer.wms(WMS_URL, {
  layers: WMS_LAYER, format: 'image/png', transparent: true, opacity: 0.65
}).addTo(map);

// Wind — leaflet-velocity (point u/v to raster-ish via plugin)
async function loadWind(){
  const res = await fetch(%(geojson_path)s);
  const gj = await res.json();
  // Convert point features to simple grid for velocity layer
  const data = [];
  for(const f of gj.features){
    const lon = f.geometry.coordinates[0];
    const lat = f.geometry.coordinates[1];
    const u = f.properties.u_ms;
    const v = f.properties.v_ms;
    data.push({lon, lat, u, v});
  }
  const velocityLayer = L.velocityLayer({
    // leaflet-velocity expects a grid; most forks accept an array of samples
    data: data,
    velocityScale: 0.01,
    maxVelocity: 30,
    displayValues: true,
    displayOptions: { velocityType: 'wind', speedUnit: 'kt' }
  });
  velocityLayer.addTo(map);
}
loadWind().catch(console.error);

// Markers
L.marker(CENTER).addTo(map).bindTooltip(SITE + " center");
</script>
</body></html>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", default="out/wind_uv.geojson")
    ap.add_argument("--out", default="out/map_leaflet.html")
    ap.add_argument("--wms", default="https://erddap.aoml.noaa.gov/hdb/erddap/wms/WaveWatch_2021/request")
    ap.add_argument("--layer", default="WaveWatch_2021:hs")
    ap.add_argument("--site", default="AGI", choices=["AGI","DAS"])
    args = ap.parse_args()

    center = AGI if args.site == "AGI" else DAS
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    html = HTML_TMPL.replace("%(site)s", json.dumps(args.site))
    html = html.replace("%(lat).6f", f"{center[0]:.6f}")
    html = html.replace("%(lon).6f", f"{center[1]:.6f}")
    html = html.replace("%(wms)s", json.dumps(args.wms))
    html = html.replace("%(layer)s", json.dumps(args.layer))
    html = html.replace("%(geojson_path)s", json.dumps(Path(args.geo).name))

    # Write HTML and copy GeoJSON next to it
    out_path = Path(args.out)
    out_path.write_text(html, encoding="utf-8")
    gj_src = Path(args.geo)
    if gj_src.exists():
        (out_path.parent / gj_src.name).write_text(gj_src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
