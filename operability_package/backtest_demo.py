import json, math, random, numpy as np, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
from operability_forecast import Gate, prob_go_from_ensembles

OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(exist_ok=True)

random.seed(7); np.random.seed(7)
N = 60; rows = []; brier_items = []; gate = Gate()

def gen_case(day_idx:int):
    hs_true = np.random.normal(0.9 + 0.05*day_idx, 0.25 + 0.03*day_idx)
    w_true  = np.random.normal(15 + 0.6*day_idx,   3.5 + 0.4*day_idx)
    hs_ens  = np.random.normal(hs_true+0.05, 0.30 + 0.03*day_idx, size=30).clip(0.05,None)
    w_ens   = np.random.normal(w_true+0.5,   3.8  + 0.3*day_idx,  size=30).clip(0.5,None)
    return float(hs_true), float(w_true), hs_ens.tolist(), w_ens.tolist()

def is_go(hs:float, w:float, g:Gate)->int:
    return 1 if (hs<=g.hs_go and w<=g.wind_go) else 0

for i in range(N):
    d = np.random.randint(1,8)
    hs_true, w_true, hs_ens, w_ens = gen_case(d)
    p = prob_go_from_ensembles(hs_ens, w_ens, gate)
    y = is_go(hs_true, w_true, gate)
    rows.append({"day":f"D+{d}","hs_true":hs_true,"w_true":w_true,"P_go":p["P_go"],"y_go":y})
    brier_items.append((p["P_go"], y))

import pandas as pd
df = pd.DataFrame(rows); df.to_csv(OUT / "backtest_cases.csv", index=False)
brier = float(np.mean([(p - y)**2 for p,y in brier_items]))

bins = np.linspace(0,1,11)
df["bin"] = np.digitize(df["P_go"], bins) - 1
rel = df.groupby("bin").agg(P_hat=("P_go","mean"), obs=("y_go","mean"), n=("y_go","size")).reset_index()
rel = rel.dropna()

plt.figure(); plt.plot([0,1],[0,1], linestyle="--"); plt.scatter(rel["P_hat"], rel["obs"])
plt.title("Reliability Diagram (Go event)"); plt.xlabel("Forecast probability"); plt.ylabel("Observed frequency")
plt.grid(True, alpha=0.3); plt.tight_layout(); plt.savefig(OUT / "reliability_diagram.png", dpi=150); plt.close()

err = np.abs(np.random.normal(0.12, 0.05, size=80))
plt.figure(); plt.hist(err, bins=15); plt.title("ETA MAPE Proxy Distribution")
plt.xlabel("MAPE"); plt.ylabel("count"); plt.tight_layout(); plt.savefig(OUT / "eta_mape_hist.png", dpi=150); plt.close()

with open(OUT / "backtest_metrics.json","w",encoding="utf-8") as f:
    json.dump({"brier_go": brier,
               "reliability_points": rel.to_dict(orient="records")}, f, indent=2)
print("Backtest demo written to outputs/.")
