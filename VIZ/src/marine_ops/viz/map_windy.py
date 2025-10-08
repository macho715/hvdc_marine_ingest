#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
map_windy.py — Windy Map Forecast 임베드 HTML 생성 (wind + waves)
Usage:
  WINDY_API_KEY=xxxx python map_windy.py --out out/map_windy.html --site AGI
참고: https://api.windy.com/map-forecast/docs
"""
import os, json, argparse
from pathlib import Path
AGI = (24.843833, 53.655306)
DAS = (25.151300, 52.871700)

HTML_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Marine Viz — Windy</title>
<style>html,body,#windy{height:100%;margin:0}</style>
<script src="https://api.windy.com/assets/map-forecast/libBoot.js"></script>
</head>
<body>
<div id="windy"></div>
<script>
const API_KEY = %(api_key)s;
const CENTER = [%(lat).6f, %(lon).6f];
const options = {
  key: API_KEY,
  lat: CENTER[0], lon: CENTER[1], zoom: 7,
  overlay: 'wind', // start with wind; waves can be toggled
  verbose: false
};
windyInit(options, (windyAPI) => {
  const { overlays, picker } = windyAPI;
  // Activate both wind particles and waves layer
  overlays.wind.setActive(true);
  overlays.waves.setActive(true);
  // Open picker at center to read values
  picker.open({ lat: CENTER[0], lon: CENTER[1] });
});
</script>
</body></html>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/map_windy.html")
    ap.add_argument("--site", default="AGI", choices=["AGI","DAS"])
    ap.add_argument("--api_key", default=os.getenv("WINDY_API_KEY",""))
    args = ap.parse_args()

    if not args.api_key:
        raise SystemExit("WINDY_API_KEY not set. export WINDY_API_KEY=...")

    center = AGI if args.site == "AGI" else DAS
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    html = HTML_TMPL % {
        "api_key": json.dumps(args.api_key),
        "lat": center[0], "lon": center[1],
    }
    Path(args.out).write_text(html, encoding="utf-8")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
