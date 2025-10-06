import json, math, random, numpy as np, pandas as pd, matplotlib.pyplot as plt
from pathlib import Path
from operability_forecast import Gate, operability_for_day, decision_from_probs, speed_effective, eta_hours

OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(exist_ok=True)

random.seed(42); np.random.seed(42)

def synth_ensemble(mu_hs, sd_hs, mu_w, sd_w, n=30):
    hs = np.random.normal(mu_hs, sd_hs, size=n).clip(0.1, None).tolist()
    w  = np.random.normal(mu_w, sd_w, size=n).clip(0.1, None).tolist()
    return hs, w

base_gate = Gate()
records = []; by_day_summary = []
for d in range(1,8):
    hs_by_hour = {}; w_by_hour  = {}
    for h in range(0,24):
        mu_hs = 0.8 + 0.05*d + 0.02*math.sin(h/3.0)
        sd_hs = 0.20 + 0.02*d
        mu_w  = 14.0 + 0.5*d + 0.5*math.cos(h/4.0)
        sd_w  = 3.0 + 0.3*d
        hs_ens, w_ens = synth_ensemble(mu_hs, sd_hs, mu_w, sd_w, n=30)
        hs_by_hour[h] = hs_ens; w_by_hour[h]  = w_ens
    out = operability_for_day(d, hs_by_hour, w_by_hour, base_gate)
    day_label = f"D+{d}"
    for dp, probs in out["by_daypart"].items():
        decision = decision_from_probs(probs)
        records.append({"day": day_label, "daypart": dp, **probs, "decision": decision})
    pgo_min = min([r["P_go"] for r in records if r["day"]==day_label])
    by_day_summary.append({"day": day_label, "P_go_min": pgo_min})

df = pd.DataFrame.from_records(records)
df.to_csv(OUT / "operability_forecast.csv", index=False)
with open(OUT / "operability_forecast.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

Hs_mid = 0.9
v_eff  = speed_effective(8.0, Hs_mid)
eta_h  = eta_hours(44.0, v_eff, buffer_min=45)
with open(OUT / "eta_demo.json","w",encoding="utf-8") as f:
    json.dump({"route":"MW4→AGI","Hs_mid_demo":Hs_mid,"v_eff_kt":round(v_eff,2),"eta_h":eta_h}, f, indent=2)

plt.figure()
plt.plot([x["day"] for x in by_day_summary], [x["P_go_min"] for x in by_day_summary], marker="o")
plt.title("Conservative P(Go) by Day (Min across Dayparts)")
plt.xlabel("Lead Day"); plt.ylabel("P(Go)"); plt.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig(OUT / "prob_go_3to7d.png", dpi=150); plt.close()
print("Demo forecast written to outputs/.")
