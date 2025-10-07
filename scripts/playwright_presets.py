"""Playwright scraping presets for AGI / DAS marine panels."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterable, Optional

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

DATA_ROOT = Path("data")
RAW_ROOT = Path("raw")
ALIASES = {
    "AGI": [r"Al\s*Ghallan", r"\bAGI\b"],
    "DAS": [r"DAS\s*Island", r"\bDAS\b"],
}
DEFAULT_TIMEOUT_MS = 25_000
JSON_MAX_BYTES = 8 * 1024 * 1024  # guardrail for oversized responses


@dataclass
class RunOptions:
    url: str
    site: str
    headless: bool
    timeout: int
    network_idle: bool


def _orthogonal_regex(patterns: Iterable[str]) -> re.Pattern[str]:
    joined = "|".join(f"({p})" for p in patterns)
    return re.compile(joined, re.IGNORECASE)


def _candidate_locators(page: Page, site: str) -> Generator[Locator, None, None]:
    rx = _orthogonal_regex(ALIASES[site])
    # 1. Semantically labelled section
    yield page.locator("section").filter(has_text=rx).first
    # 2. ARIA role heading -> ascend two levels
    heading = page.get_by_role("heading", name=rx).first
    yield heading.locator("xpath=ancestor-or-self::*[self::section or self::div][1]")
    # 3. Text fallback -> nearest section/div ancestor
    yield page.get_by_text(rx).first.locator(
        "xpath=ancestor-or-self::*[self::section or self::div][1]"
    )


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    return df


def _parse_tables_from_html(html: str) -> Optional[pd.DataFrame]:
    soup = BeautifulSoup(html, "html.parser")
    frames: list[pd.DataFrame] = []
    for table in soup.find_all("table"):
        try:
            table_frames = pd.read_html(str(table))
        except ValueError:
            continue
        for frame in table_frames:
            frames.append(_normalise_columns(frame))
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def _dump_json_payload(site: str, ts: int, payload: object) -> None:
    RAW_ROOT.mkdir(exist_ok=True)
    millis = int(time.time() * 1000)
    out_path = RAW_ROOT / f"{site}_{ts}_{millis}.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def _install_response_logger(page: Page, site: str, ts: int) -> None:
    def _on_response(response):
        try:
            ctype = response.headers.get("content-type", "")
        except Exception:
            return
        if "application/json" not in ctype.lower():
            return
        try:
            payload = response.json()
        except Exception:
            return
        try:
            # Rough size guard: json.dumps length before writing
            data = json.dumps(payload, ensure_ascii=False)
        except Exception:
            return
        if len(data.encode("utf-8")) > JSON_MAX_BYTES:
            return
        _dump_json_payload(site, ts, payload)

    page.on("response", _on_response)


def run_scrape(opts: RunOptions) -> int:
    timestamp = int(time.time())
    DATA_ROOT.mkdir(exist_ok=True)
    RAW_ROOT.mkdir(exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=opts.headless)
        context = browser.new_context()
        page = context.new_page()
        _install_response_logger(page, opts.site, timestamp)

        goto_kwargs = {"timeout": opts.timeout}
        if opts.network_idle:
            goto_kwargs["wait_until"] = "networkidle"

        page.goto(opts.url, **goto_kwargs)

        # Small grace settle
        page.wait_for_timeout(750)

        dataframe: Optional[pd.DataFrame] = None
        for locator in _candidate_locators(page, opts.site):
            try:
                locator.wait_for(timeout=3_000)
                html = locator.inner_html()
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
            dataframe = _parse_tables_from_html(html)
            if dataframe is not None and not dataframe.empty:
                break

        if dataframe is None or dataframe.empty:
            dataframe = _parse_tables_from_html(page.content())

        browser.close()

    if dataframe is None or dataframe.empty:
        print("[ZERO] No table extracted; JSON payloads saved under raw/", file=sys.stderr)
        return 2

    out_path = DATA_ROOT / f"marine_playwright_{opts.site}_{timestamp}.csv"
    dataframe.to_csv(out_path, index=False)
    print(f"[OK] Saved {len(dataframe)} rows to {out_path}")
    return 0


def _parse_args(argv: Optional[Iterable[str]] = None) -> RunOptions:
    parser = argparse.ArgumentParser(description="Capture AGI/DAS panels using Playwright.")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--site", choices=sorted(ALIASES), required=True, help="Site alias")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_MS, help="Navigation timeout in ms")
    parser.add_argument("--no-headless", action="store_true", help="Disable headless mode")
    parser.add_argument(
        "--no-network-idle",
        action="store_true",
        help="Skip wait_until=networkidle (use default load)",
    )
    args = parser.parse_args(argv)
    return RunOptions(
        url=args.url,
        site=args.site,
        headless=not args.no_headless,
        timeout=args.timeout,
        network_idle=not args.no_network_idle,
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    opts = _parse_args(argv)
    try:
        return run_scrape(opts)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
