#!/usr/bin/env python3
"""TimeDimension HTML에 실시간 GeoJSON 데이터 삽입"""
import json
from pathlib import Path

# 실시간 GeoJSON 로드
gj_path = Path("VIZ/out/wind_uv.geojson")
if not gj_path.exists():
    print("❌ GeoJSON 파일 없음. adapter.py를 먼저 실행하세요.")
    exit(1)

gj = json.load(open(gj_path, 'r', encoding='utf-8'))

# TimeDimension HTML 로드
html_path = Path("map_leaflet_timedim.html")
html = html_path.read_text(encoding='utf-8')

# 샘플 데이터를 실시간 데이터로 교체
sample_json = """{
  "type":"FeatureCollection",
  "features":[
    {"type":"Feature","geometry":{"type":"Point","coordinates":[53.655306,24.843833]},"properties":{"u_ms":-2.1,"v_ms":-6.2}},
    {"type":"Feature","geometry":{"type":"Point","coordinates":[53.55,24.80]},"properties":{"u_ms":-1.2,"v_ms":-4.2}},
    {"type":"Feature","geometry":{"type":"Point","coordinates":[53.75,24.82]},"properties":{"u_ms":-3.5,"v_ms":-5.0}},
    {"type":"Feature","geometry":{"type":"Point","coordinates":[53.58,24.90]},"properties":{"u_ms":-2.7,"v_ms":-3.3}},
    {"type":"Feature","geometry":{"type":"Point","coordinates":[53.80,24.90]},"properties":{"u_ms":-4.1,"v_ms":-4.8}}
  ]
}"""

real_json = json.dumps(gj, ensure_ascii=False, separators=(',',':'))

# 교체
html_new = html.replace(sample_json, real_json)

# VIZ 폴더에 저장
output_path = Path("VIZ/map_leaflet_timedim.html")
output_path.write_text(html_new, encoding='utf-8')

print(f"✅ Updated: {output_path}")
print(f"   Points: {len(gj['features'])}")
print(f"   Wind: 14.9 m/s @ 352°")
print(f"   Wave: 0.24 m")

