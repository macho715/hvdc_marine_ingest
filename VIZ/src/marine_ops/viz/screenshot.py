#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
screenshot.py — Playwright로 HTML → PNG 캡처
Usage:
  python screenshot.py --html out/map_leaflet.html --png out/map_leaflet.png
"""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--png", required=True)
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=1000)
    args = ap.parse_args()

    html_path = Path(args.html).resolve()
    url = f"file://{html_path}"
    Path(args.png).parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=2
        )
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        page.screenshot(path=args.png, full_page=True)
        browser.close()

if __name__ == "__main__":
    main()
