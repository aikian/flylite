"""Cross-check the numbers quoted in the Korean draft against the summary CSVs.

Each entry: (label, value computed from CSVs, literal string that must appear in the draft).
Prints OK / MISSING so a reviewer-proof draft never drifts from the data.  usage: python check_numbers.py [draft.md]
"""
import re, sys
import numpy as np, pandas as pd

draft = open(sys.argv[1] if len(sys.argv) > 1 else "FlyLite_논문초안_국문_v4.md", encoding="utf-8").read()
EN = draft.lstrip().startswith("# How sparse")  # English manuscript uses different literal phrasings for a few multi-value checks
A = pd.read_csv("results/phaseA/summary.csv"); A2 = pd.read_csv("results/phaseA2/summary.csv"); B = pd.read_csv("results/phaseB/summary.csv")
C = pd.read_csv("results/phaseC/summary.csv"); D = pd.read_csv("results/phaseD/summary.csv")
R, P, J, N = ["sugar100__" + x for x in ("readout_ratio", "pearson_union", "jaccard_active", "n_active")]

def one(df, **kw):
    d = df
    for k, v in kw.items(): d = d[d[k] == v]
    assert len(d) == 1, (kw, len(d))
    return d.iloc[0]

def seeds(df, col, **kw):
    d = df
    for k, v in kw.items(): d = d[d[k] == v]
    return d.sort_values("seed")[col].values

checks = []
def add(label, value, literal): checks.append((label, value, literal))

# --- H1 magnitude, sugar sigma 0 (Phase A)
m = {k: one(A, noise=0.0, method="mag", k=k) for k in [1, 2, 3, 5, 10, 20, 31, 50]}
add("mag k=1 ratio", m[1][R], "1.04"); add("mag k=5 ratio", m[5][R], "0.95"); add("mag k=10 ratio", m[10][R], "0.79")
add("mag k=20 ratio", m[20][R], "0.11"); add("mag k=31 ratio", m[31][R], "0.09")
add("mag k=10 corr", m[10][P], "0.82"); add("mag k=5 jaccard", m[5][J], "0.83"); add("mag k=10 jaccard", m[10][J], "0.68")
add("mag k=10 n_active", m[10][N], "269"); add("mag k=20 n_active", m[20][N], "132")
# cliff (log interpolation between k=5 and k=10 at 0.8)
k0, k1, r0, r1 = 5, 10, m[5][R], m[10][R]
kstar = np.exp(np.log(k0) + (0.8 - r0) / (r1 - r0) * (np.log(k1) - np.log(k0)))
add("cliff k*", kstar, "9.4")

# --- H3 nulls
add("rand k=1 min", seeds(A, R, noise=0.0, method="rand", k=1).min(), "0.02"); add("rand k=1 max", seeds(A, R, noise=0.0, method="rand", k=1).max(), "0.12")
dpc = A[(A.noise == 0) & (A.method == "dp")][P]; add("dp corr min", dpc.min(), "−0.2"); add("dp corr max", dpc.max(), "−0.1")
sh = C[(C.task == "sugar") & (C.method == "shuf")]
add("sugar shuf k<=10 max ratio", sh[sh.k <= 10][R].max(), "0.00"); add("sugar shuf k=31 min", sh[sh.k == 31][R].min(), "0.01"); add("sugar shuf k=31 max", sh[sh.k == 31][R].max(), "0.19")
add("sugar shuf n_active min", sh[sh.k <= 10][N].min(), "50–83"); add("sugar shuf n_active max", sh[sh.k <= 10][N].max(), "83")
rm = C[(C.task == "sugar") & (C.method == "randm")]
for k, lit in [(1, "0.96–1.01"), (2, "0.93–1.00")]:
    v = rm[rm.k == k][R]; add(f"randm k={k} range", (v.min(), v.max()), lit)
add("randm k=3 mean", rm[rm.k == 3][R].mean(), "0.86"); add("randm k=3 min", rm[rm.k == 3][R].min(), "0.64"); add("randm k=3 max", rm[rm.k == 3][R].max(), "0.97")
add("randm k=5 mean", rm[rm.k == 5][R].mean(), "0.34"); add("randm k=5 seeds", tuple(np.round(seeds(C, R, task="sugar", method="randm", k=5), 2)), "0.18, 0.20, 0.67, 0.26 and 0.40" if EN else "0.18, 0.20, 0.67, 0.26, 0.40")
add("randm k=10 max", rm[rm.k == 10][R].max(), "0.03")
add("randm k=5 mass", rm[rm.k == 5].frac_syn.mean() * 100, "41%"); add("randm k=10 mass", rm[rm.k == 10].frac_syn.mean() * 100, "24%")

# --- H6 act, sigma 0
a = {k: one(A, noise=0.0, method="act", k=k) for k in [50]}; add("act k=50 ratio", a[50][R], "1.06"); add("act k=50 corr", a[50][P], "0.997"); add("act k=50 jaccard", a[50][J], "0.92")
bt = C[(C.task == "bitter") & (C.noise == 0) & (C.method == "act")].sort_values("k")
si_act = 1 - bt["sugar100_bitter100__readout"] / bt["sugar100__readout"]
add("act bitter SI k=10", si_act.iloc[2], "0.76"); add("act bitter SI k=31", si_act.iloc[3], "−0.06")

# --- H4 bitter sigma 0 (Phase B), groom
bm = B[(B.task == "bitter") & (B.noise == 0) & (B.method == "mag")].sort_values("k")
si = 1 - bm["sugar100_bitter100__readout"] / bm["sugar100__readout"]
add("bitter SI sigma0 k=2,5,10", tuple(np.round(si.values[1:4], 2)), "0.96, 0.87, 0.93"); add("bitter SI sigma0 k=31", si.values[4], "0.32")
gm = B[(B.task == "groom") & (B.noise == 0) & (B.method == "mag")].sort_values("k")
add("groom CE ratio k=2,5,10", tuple(np.round(gm[gm.k > 0]["jonCE100__readout_ratio"].values[:3], 2)), "0.73 already at k = 2, 0.23 at k = 5 and 0.03 at k = 10" if EN else "0.73, k = 5에서 0.23, k = 10에서 0.03")
add("groom spec k=2", gm[gm.k > 0].specificity.values[0], "14.7"); add("groom spec k=5", gm[gm.k > 0].specificity.values[1], "−2.7")

# --- H2 state: bitter sigma 3.5 trial 10 (Phase D), sugar A2
dm = D[D.method == "mag"].sort_values("k"); si_d = 1 - dm["sugar100_bitter100__readout"] / dm["sugar100__readout"]
add("bitter SI sigma3.5 (D) k=0,2,5,10,31", tuple(np.round(si_d.values, 2)), "0.83 (full) to 0.91 at k = 2, **0.72 at k = 5, 0.40 at k = 10 and −0.61 at k = 31**" if EN else "0.83 → k = 2에서 0.91 → **k = 5에서 0.72 → k = 10에서 0.40 → k = 31에서 −0.61")
add("D sugar+bitter Hz", tuple(np.round(dm["sugar100_bitter100__readout"].values, 1)), "5.9 ± 2.9 Hz (full, mean ± SE) to 3.5 ± 0.7, 15.1 ± 7.3, 31.0 ± 11.1 and 48.1 ± 10.7" if EN else "5.9 ± 2.9(원본, 평균 ± SE) → 3.5 ± 0.7 → 15.1 ± 7.3 → 31.0 ± 11.1 → 48.1 ± 10.7")
add("D sugar Hz", tuple(np.round(dm["sugar100__readout"].values, 1)), "34.8, 40.2, 53.5, 51.5 and 29.9" if EN else "34.8 → 40.2 → 53.5 → 51.5 → 29.9")
r1 = seeds(A2, R, noise=3.5, method="rand", k=1); add("A2 rand k=1 seeds", tuple(np.round(r1, 2)), "0.96, 0.39, 0.82, 0.02 and 0.10" if EN else "0.96, 0.39, 0.82, 0.02, 0.10")
r3 = seeds(A2, R, noise=3.5, method="rand", k=3); add("A2 rand k=3 seeds", tuple(np.round(r3, 2)), "0.13, 0.08, 1.02, 0.02 and 0.28" if EN else "0.13, 0.08, 1.02, 0.02, 0.28")
add("A2 rand k=1 median", np.median(r1), "0.39"); add("A2 rand k=3 median", np.median(r3), "0.13")
mm = {k: one(A2, noise=3.5, method="mag", k=k) for k in [1, 3, 5, 10, 20, 31]}
add("A2 mag k=1,3,5,10 ratio", tuple(np.round([mm[k][R] for k in [1, 3, 5, 10]], 2)), "1.03, 1.03, 1.59, 1.23")
add("A2 mag corr k=10", mm[10][P], "0.88"); add("A2 mag corr k=31", mm[31][P], "0.70")
add("A2 ref sugar Hz", one(A2, noise=3.5, method="mag", k=0)["sugar100__readout_full"], "37.0")

# --- Phase F robustness (sugar sigma 0, mag k=5,10,20): v783, gain 0.8x, 1.2x
PF = {n: pd.read_csv(f"results/{d}/summary.csv") for n, d in [("783", "phaseF_783"), ("w08", "phaseF_w08"), ("w12", "phaseF_w12")]}
def fref(n): return float(PF[n][PF[n].k == 0]["sugar100__readout_full"].iloc[0])
def fr(n, k): return float(PF[n][PF[n].k == k][R].iloc[0])
def fc(n, k): return float(PF[n][PF[n].k == k][P].iloc[0])
add("F ref 783", fref("783"), "65.0 Hz"); add("F ref w08", fref("w08"), "35.7 Hz"); add("F ref w12", fref("w12"), "81.0 Hz")
add("F 783 k5,10,20", (round(fr("783", 5), 2), round(fr("783", 10), 2), round(fr("783", 20), 2)), "0.71 at k = 5, 0.70 at k = 10 and 0.06 at k = 20" if EN else "0.71, 0.70, 0.06")
add("F 783 corr", (round(fc("783", 5), 2), round(fc("783", 10), 2), round(fc("783", 20), 2)), "0.94, 0.81, 0.60")
add("F w08 k5,k10", (round(fr("w08", 5), 2), round(fr("w08", 10), 2)), "0.22 at k = 5 and 0.06 at k = 10" if EN else "이미 0.22, k = 10에서 0.06")
add("F w12 k5,10,20", (round(fr("w12", 5), 2), round(fr("w12", 10), 2), round(fr("w12", 20), 2)), "0.87, 0.97 and 0.56" if EN else "0.87, 0.97, 0.56")
add("F w08 corr k10", fc("w08", 10), "0.86")

# --- report
bad = 0
for label, value, literal in checks:
    ok = literal in draft
    bad += (not ok)
    v = value if not isinstance(value, (float, np.floating)) else round(float(value), 3)
    print(f"{'OK     ' if ok else 'MISSING'}  {label:38s} data={v}  text='{literal}'")
print(f"\n{len(checks) - bad}/{len(checks)} literals found in draft")
