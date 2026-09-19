"""Analyze a run_flylite.py summary.csv: hypothesis tables (H1 cliff, H2 state, H3 nulls, H6 task-aware) + figures.

usage: python analyze_flylite.py results/phaseA [--stim sugar100]
"""
import sys, argparse
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--stim", default="sugar100"); ap.add_argument("--thr", type=float, default=0.8)
a = ap.parse_args()
out = Path(a.out); df = pd.read_csv(out / "summary.csv")
R, C, A = f"{a.stim}__readout_ratio", f"{a.stim}__pearson_union", f"{a.stim}__n_active"
df = df[df[R].notna()]

# ---- aggregate over seeds (mean, sd, n)
g = df.groupby(["task", "noise", "method", "k"]).agg(
    frac_edges=("frac_edges", "first"), frac_syn=("frac_syn", "first"),
    ratio=(R, "mean"), ratio_sd=(R, "std"), corr=(C, "mean"), corr_sd=(C, "std"),
    n_active=(A, "mean"), n=(R, "size")).reset_index()
g.to_csv(out / "agg.csv", index=False)

def cliff(sub, thr):
    """First k (log-interpolated) where readout ratio drops below thr; None if never."""
    sub = sub.sort_values("k")
    ks, r = sub.k.values.astype(float), sub.ratio.values
    below = np.where(r < thr)[0]
    if len(below) == 0: return np.nan
    i = below[0]
    if i == 0: return ks[0]
    k0, k1, r0, r1 = ks[i-1], ks[i], r[i-1], r[i]
    return float(np.exp(np.log(k0) + (thr - r0) / (r1 - r0) * (np.log(k1) - np.log(k0)))) if r1 != r0 else k1

print("=== H1/H2: cliff k* (readout ratio < %.2f) per task/noise/method ===" % a.thr)
rows = []
for (t, nz, m), sub in g.groupby(["task", "noise", "method"]):
    sub = sub[sub.k > 0]
    rows.append(dict(task=t, noise=nz, method=m, k_star=cliff(sub, a.thr),
                     ratio_at_k10=float(sub.loc[sub.k == 10, "ratio"].mean()) if (sub.k == 10).any() else np.nan,
                     corr_at_k10=float(sub.loc[sub.k == 10, "corr"].mean()) if (sub.k == 10).any() else np.nan))
H = pd.DataFrame(rows); print(H.round(3).to_string(index=False)); H.to_csv(out / "hyp_cliff.csv", index=False)

print("\n=== H3/H6: at each k, method vs mag (ratio, corr). dp/rand/shuf ~ 0 => wiring position needed; act > mag => task-aware wins ===")
piv_r = g.pivot_table(index=["task", "noise", "k"], columns="method", values="ratio")
piv_c = g.pivot_table(index=["task", "noise", "k"], columns="method", values="corr")
print("readout ratio:\n", piv_r.round(2).to_string()); print("\npearson (union, stim excluded):\n", piv_c.round(2).to_string())

print("\n=== H5: behaviour vs neural dissociation (mag only): ratio - corr ===")
mg = g[g.method == "mag"].copy(); mg["ratio_minus_corr"] = mg.ratio - mg["corr"]
print(mg[["task", "noise", "k", "frac_edges", "ratio", "corr", "n_active", "ratio_minus_corr"]].round(3).to_string(index=False))

# ---- figures: one panel row per noise level
noises = sorted(g.noise.unique()); methods = [m for m in ["mag", "act", "shuf", "dp", "rand"] if m in g.method.unique()]
col = dict(mag="C0", act="C2", shuf="C1", dp="C4", rand="C3")
fig, axes = plt.subplots(len(noises), 3, figsize=(14, 4 * len(noises)), squeeze=False)
for i, nz in enumerate(noises):
    for m in methods:
        s = g[(g.noise == nz) & (g.method == m) & (g.k > 0)].sort_values("k")
        if s.empty: continue
        x = s.frac_edges * 100
        axes[i, 0].errorbar(x, s.ratio, yerr=s.ratio_sd.fillna(0), fmt="o-", color=col[m], label=m, capsize=2)
        axes[i, 1].errorbar(x, s["corr"], yerr=s.corr_sd.fillna(0), fmt="o-", color=col[m], label=m, capsize=2)
        axes[i, 2].plot(x, s.n_active, "o-", color=col[m], label=m)
    for j, (yl, ttl) in enumerate([("readout / full", "Behavioural readout"), ("Pearson r (active union)", "Neural response"), ("# active neurons", "Active population")]):
        ax = axes[i, j]; ax.set_xscale("log"); ax.invert_xaxis(); ax.grid(alpha=.3)
        ax.set_xlabel("edges retained (%)"); ax.set_ylabel(yl); ax.set_title(f"{ttl} — noise σ={nz} mV", fontsize=10)
    axes[i, 0].axhline(1, ls="--", c="gray", lw=.8); axes[i, 0].axhline(a.thr, ls=":", c="gray", lw=.8); axes[i, 0].legend(fontsize=8)
fig.suptitle(f"FlyLite {out.name}: {a.stim} — Shiu LIF teacher, FlyWire v630", fontsize=11); fig.tight_layout()
fig.savefig(out / f"fig_{a.stim}.png", dpi=150); print("\nfigure ->", out / f"fig_{a.stim}.png")
