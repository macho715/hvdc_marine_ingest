# KR: 저장한 HTML(snapshot.html)에서 <table> 파싱 → data/marine_manual.csv
# EN: Parse saved HTML page into CSV for downstream embedding

from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

html_file = "snapshot.html"
with open(html_file, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

frames = []
for t in soup.find_all("table"):
    try:
        for df in pd.read_html(str(t)):
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
            frames.append(df)
    except Exception:
        pass

if not frames:
    raise SystemExit("No <table> found in snapshot.html")

out = pd.concat(frames, ignore_index=True)
Path("data").mkdir(exist_ok=True)
out.to_csv("data/marine_manual.csv", index=False)
print("saved: data/marine_manual.csv")
