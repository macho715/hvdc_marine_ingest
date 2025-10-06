# src/marine_ops/connectors/worldtides.py
import httpx
WT = "https://www.worldtides.info/api/v3"
def fetch_worldtides_heights(lat:float, lon:float, key:str, hours:int=72):
    """Return tide heights (30-min resolution where available)."""
    params = {"heights":"", "lat":lat, "lon":lon, "key":key, "duration":hours}
    r = httpx.get(WT, params=params, timeout=20)
    r.raise_for_status()
    return r.json()
