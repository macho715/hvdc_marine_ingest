import sys
from pathlib import Path
import pandas as pd
from subprocess import run

DATA_DIR = Path("data")


def has_fresh_csv() -> bool:
    if not DATA_DIR.exists():
        return False
    files = sorted(DATA_DIR.glob("marine_*.csv")) + sorted(DATA_DIR.glob("marine_manual.csv"))
    for p in reversed(files):  # prefer latest
        try:
            df = pd.read_csv(p)
            if len(df.index) > 0:
                return True
        except Exception:
            continue
    return False


def main():
    if not has_fresh_csv():
        # ZERO path
        print("[orchestrator] No fresh CSV → ZERO report path")
        run([sys.executable, "ncm_zero_guard.py", "--tz", "Asia/Dubai"], check=True)
    else:
        # TODO: integrate normal Weather Vessel fusion/ERI here
        print("[orchestrator] Data present → normal report path (TODO)")
        run([sys.executable, "ncm_zero_guard.py", "--tz", "Asia/Dubai"], check=True)  # temp: still ZERO


if __name__ == "__main__":
    main()
