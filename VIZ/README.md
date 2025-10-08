# GIS Visualization Skeleton (Wind + Waves)

구성 파일
- `src/marine_ops/viz/adapter.py` — CSV → GeoJSON(u/v), Hs 메타
- `src/marine_ops/viz/map_leaflet.py` — Leaflet(WW3 Hs WMS + leaflet-velocity Wind)
- `src/marine_ops/viz/map_windy.py` — Windy Map Forecast 임베드(wind + waves)
- `src/marine_ops/viz/screenshot.py` — Playwright 스크린샷(HTML → PNG)

## Quickstart
```bash
# 0) 가상환경 + 의존성
pip install folium requests playwright

# 1) 데이터 어댑터 (입력 없으면 샘플 생성)
python src/marine_ops/viz/adapter.py --site AGI --out out/wind_uv.geojson

# 2A) Leaflet HTML 생성 (WW3 Hs + Wind)
python src/marine_ops/viz/map_leaflet.py --geo out/wind_uv.geojson --out out/map_leaflet.html

# 2B) Windy HTML 생성 (API 키 필요)
export WINDY_API_KEY=xxxx
python src/marine_ops/viz/map_windy.py --out out/map_windy.html

# 3) 스크린샷 (Playwright)
python -m playwright install chromium
python src/marine_ops/viz/screenshot.py --html out/map_leaflet.html --png out/map_leaflet.png
```

참고:
- Windy Map Forecast API 문서: https://api.windy.com/map-forecast/docs
- leaflet-velocity CDN: https://cdn.jsdelivr.net/npm/leaflet-velocity@2.1.4/
- ERDDAP WMS 사용법: https://www.ncei.noaa.gov/erddap/wms/documentation.html
- WW3 예시 데이터셋: https://erddap.aoml.noaa.gov/hdb/erddap/griddap/WaveWatch_2021.html
- Playwright Screenshot: https://playwright.dev/python/docs/screenshots
