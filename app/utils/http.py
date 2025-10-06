# app/utils/http.py
import time
import httpx

def get_json(url: str, ua: str, timeout: int = 10):
    """HTTP GET JSON with 429/503 Retry-After compliance."""
    r = httpx.get(url, headers={"User-Agent": ua}, timeout=timeout)
    if r.status_code in (429, 503) and "Retry-After" in r.headers:
        try:
            ra = int(r.headers.get("Retry-After", "30"))
        except Exception:
            ra = 30
        time.sleep(max(1, ra))
        r = httpx.get(url, headers={"User-Agent": ua}, timeout=timeout)
    r.raise_for_status()
    return r.json()
