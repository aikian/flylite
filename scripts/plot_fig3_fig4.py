"""Fig 3: behaviour vs neural-response dissociation.  Fig 4: network-state axis (sigma 0 / 3.0 / 3.5).
Data: Phase A (sigma 0, trial 3), Phase A2 (sigma 3.0/3.5, trial 10), Phase B (bitter sigma 0, trial 3), Phase D (bitter sigma 3.5, trial 10)."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

A = pd.read_csv("results/phaseA/summary.csv"); A2 = pd.read_csv("results/phaseA2/summary.csv")
B = pd.read_csv("results/phaseB/summary.csv"); C = pd.read_csv("results/phaseC/summary.csv"); D = pd.read_csv("results/phaseD/summary.csv")
R, P, J, N, SD, F = ["sugar100__" + x for x in ("readout_ratio", "pearson_union", "jaccard_active", "n_active", "readout_trial_sd", "readout_full")]

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
OP = dict(mag=("#2a78d6", "o"), act=("#eb6834", "s"), randm=("#1baf7a", "D"), rand=("#eda100", "v"))   # same slots as Fig 2
STATE = {0.0: ("#2a78d6", "o", "silent, σ = 0"), 3.0: ("#1baf7a", "D", "active, σ = 3.0"), 3.5: ("#eb6834", "s", "active, σ = 3.5")}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.titlecolor": INK, "axes.spines.top": False, "axes.spines.right": False})

def logx(ax):
    ax.set_xscale("log"); ax.invert_xaxis(); ax.grid(color=GRID, lw=.8); ax.set_axisbelow(True)
    ax.set_xticks([100, 30, 10, 3, 1, 0.3]); ax.set_xticklabels(["100", "30", "10", "3", "1", "0.3"]); ax.set_xlabel("edges retained (%)")

def title(ax, t): ax.set_title(t, loc="left", fontsize=10, fontweight="bold")

# --------------------------------------------------------------------------------------------- Fig 3
s0 = pd.concat([A[(A.noise == 0)], C[C.task == "sugar"]]); s0 = s0[s0.k > 0]
s35 = A2[(A2.noise == 3.5) & (A2.k > 0)]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.3))
ax = axes[0]
for m in ["mag", "act", "randm"]:
    g = s0[s0.method == m].groupby("k").agg(r=(R, "mean"), j=(J, "mean")).reset_index().sort_values("k")
    col, mk = OP[m]
    ax.plot(g.j, g.r, "-", color=col, lw=1.2, alpha=.6)
    ax.scatter(g.j, g.r, color=col, marker=mk, s=34, ec="white", lw=.6, zorder=3, label=m)
    if m == "mag":
        for _, r in g.iterrows():
            if r.k >= 3: ax.annotate(f"k={int(r.k)}", (r.j, r.r), textcoords="offset points", xytext={3: (6, 2), 5: (-24, -12), 20: (5, -10)}.get(r.k, (5, 4)), fontsize=7, color=INK2)
    if m == "randm":
        for _, r in g.iterrows():
            if r.k in (3, 5): ax.annotate(f"randm k={int(r.k)}", (r.j, r.r), textcoords="offset points", xytext=(-6, 6), fontsize=7, color=INK2, ha="right")
ax.plot([0, 1], [0, 1], ls="--", c=INK2, lw=.7); ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.05, 1.15)
ax.set_xlabel("active-set overlap with full model (Jaccard)"); ax.set_ylabel("behavioural readout (MN9 / full)")
title(ax, "a  Silent network (σ = 0)"); ax.grid(color=GRID, lw=.8); ax.set_axisbelow(True)
ax.legend(handles=[Line2D([], [], color=OP[m][0], marker=OP[m][1], ls="", ms=6, mec="white", label=l) for m, l in
                   [("mag", "magnitude"), ("act", "task-aware"), ("randm", "weight-proportional random")]], fontsize=8, loc="center left", frameon=False)
ax.text(0.03, 0.97, "above diagonal: behaviour holds\nwhile the active set changes", ha="left", va="top", fontsize=7.5, color=INK2, transform=ax.transAxes)
ax.text(0.98, 0.04, "below diagonal:\nbehaviour lost first", ha="right", va="bottom", fontsize=7.5, color=INK2, transform=ax.transAxes)

ax = axes[1]
for m in ["mag", "act"]:
    g = s35[s35.method == m].sort_values("k"); col, mk = OP[m]
    ax.plot(g[P], g[R], "-", color=col, lw=1.2, alpha=.6)
    ax.errorbar(g[P], g[R], yerr=g[SD] / np.sqrt(10) / g[F], fmt=mk, color=col, ms=6, mec="white", mew=.6, capsize=2, lw=.8, zorder=3)
    if m == "mag":
        for _, r in g.iterrows():
            ax.annotate(f"k={int(r.k)}", (r[P], r[R]), textcoords="offset points", xytext=(5, 9) if r.k == 1 else (5, -11) if r.k == 3 else (5, 4), fontsize=7, color=INK2)
g = s35[s35.method == "rand"]
ax.scatter(g[P], g[R], color=OP["rand"][0], marker="v", s=30, ec="white", lw=.6, zorder=3, alpha=.9)
ax.annotate("uniform random\n(each seed)", (g[P].mean(), 0.55), fontsize=7.5, color=INK2, ha="center")
ax.plot([0, 1], [0, 1], ls="--", c=INK2, lw=.7); ax.axhline(1, ls=":", c=INK2, lw=.7)
ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 2.35)
ax.set_xlabel("population response (Pearson r, active union)"); ax.set_ylabel("behavioural readout (MN9 / full)")
title(ax, "b  Active network (σ = 3.5, trial 10)"); ax.grid(color=GRID, lw=.8); ax.set_axisbelow(True)
ax.legend(handles=[Line2D([], [], color=OP[m][0], marker=OP[m][1], ls="", ms=6, mec="white", label=l) for m, l in
                   [("mag", "magnitude ± SE"), ("act", "task-aware ± SE"), ("rand", "uniform random, per seed")]], fontsize=8, loc="upper left", frameon=False)

ax = axes[2]
for nz, src, n in [(0.0, A[(A.noise == 0)], 3), (3.0, A2[A2.noise == 3.0], 10), (3.5, A2[A2.noise == 3.5], 10)]:
    g = src[(src.method == "mag") & (src.k > 0)].sort_values("k"); col, mk, lab = STATE[nz]
    ax.plot(g.frac_edges * 100, g[R] - g[P], "-", color=col, marker=mk, ms=5, mec="white", mew=.6, lw=1.8, label=lab)
g = A[(A.noise == 0) & (A.method == "mag") & (A.k > 0)].sort_values("k")
ax.plot(g.frac_edges * 100, g[R] - g[J], ":", color=STATE[0.0][0], marker="o", ms=4, mfc="white", lw=1.4, label="silent, σ = 0 (readout − Jaccard)")
ax.axhline(0, c=INK2, lw=.7); logx(ax); ax.set_ylabel("dissociation index  (readout ratio − neural similarity)")
title(ax, "c  Magnitude pruning: dissociation vs budget"); ax.legend(fontsize=7.5, frameon=False, loc="upper left")
ax.text(0.03, 0.04, "> 0: behaviour outlives neural response\n< 0: behaviour lost first", ha="left", va="bottom", fontsize=7.5, color=INK2, transform=ax.transAxes)
fig.suptitle("Behavioural output and population response dissociate under sparsification", fontsize=11, x=0.02, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig("results/fig3_dissociation.png", dpi=170); print("saved results/fig3_dissociation.png")

# --------------------------------------------------------------------------------------------- Fig 4
fig, axes = plt.subplots(2, 2, figsize=(10.5, 8))
(ax_r, ax_p), (ax_si, ax_rand) = axes
for nz, src, n in [(0.0, A[A.noise == 0], 3), (3.0, A2[A2.noise == 3.0], 10), (3.5, A2[A2.noise == 3.5], 10)]:
    g = src[(src.method == "mag") & (src.k > 0)].sort_values("k"); col, mk, lab = STATE[nz]
    x = g.frac_edges * 100
    ax_r.errorbar(x, g[R], yerr=g[SD] / np.sqrt(n) / g[F], fmt="-", marker=mk, color=col, ms=5, mec="white", mew=.6, lw=1.8, capsize=2, label=lab)
    ax_p.plot(x, g[P], "-", marker=mk, color=col, ms=5, mec="white", mew=.6, lw=1.8, label=lab)
for ax, yl, t in [(ax_r, "MN9 rate / full model (± SE over trials)", "a  Readout: no earlier cliff, but over-excitation"),
                  (ax_p, "Pearson r, active union", "b  Population response: graded decline in every state")]:
    logx(ax); ax.set_ylabel(yl); title(ax, t)
ax_r.axhline(1, ls="--", c=INK2, lw=.7); ax_r.axhline(0.8, ls=":", c=INK2, lw=.7); ax_r.set_ylim(-0.05, 2.0); ax_r.legend(fontsize=8, frameon=False, loc="lower left")
ax_p.axhline(0, c=INK2, lw=.5); ax_p.set_ylim(-0.05, 1.05)

# bitter suppression index by state (sigma 0: Phase B trial 3; sigma 3.5: Phase D trial 10), with SE of each rate
for nz, src, n in [(0.0, B[(B.task == "bitter") & (B.noise == 0) & (B.method == "mag")], 3), (3.5, D[D.method == "mag"], 10)]:
    g = src.sort_values("k").copy(); col, mk, lab = STATE[nz]
    su, sb = g["sugar100__readout"], g["sugar100_bitter100__readout"]
    si = 1 - sb / su.replace(0, np.nan)
    se_su, se_sb = g["sugar100__readout_trial_sd"] / np.sqrt(n), g["sugar100_bitter100__readout_trial_sd"] / np.sqrt(n)
    se_si = (sb / su) * np.sqrt((se_sb / sb.replace(0, np.nan)) ** 2 + (se_su / su.replace(0, np.nan)) ** 2)   # delta method
    x = np.where(g.k == 0, 100.0, g.frac_edges * 100)
    ax_si.errorbar(x, si, yerr=se_si.fillna(0), fmt="-", marker=mk, color=col, ms=5, mec="white", mew=.6, lw=1.8, capsize=2, label=lab + (" (trial 3)" if nz == 0 else " (trial 10)"))
    for xi, yi, ki in zip(x, si, g.k):
        if ki > 0: ax_si.annotate(f"k={int(ki)}", (xi, yi), textcoords="offset points", xytext=(4, 4 if nz == 0 else -10), fontsize=7, color=INK2)
ax_si.axhline(0, c=INK2, lw=.7); logx(ax_si); ax_si.set_xticks([100, 30, 10, 3, 1]); ax_si.set_xticklabels(["100\n(full)", "30", "10", "3", "1"])
ax_si.set_ylabel("bitter suppression index  1 − MN9(sugar+bitter)/MN9(sugar)"); ax_si.set_ylim(-0.95, 1.1)
title(ax_si, "c  Inhibition is lost first in the active state"); ax_si.legend(fontsize=8, frameon=False, loc="lower left")
ax_si.text(0.55, 0.06, "< 0: bitter now *increases* MN9", ha="center", va="bottom", fontsize=7.5, color=INK2, transform=ax_si.transAxes)

# uniform random per seed, silent vs active: all-or-nothing in the active state
rng = np.random.default_rng(0)
for nz, src in [(0.0, A[A.noise == 0]), (3.5, A2[A2.noise == 3.5])]:
    g = src[(src.method == "rand") & (src.k.isin([1, 2, 3, 5, 10]))]; col, mk, lab = STATE[nz]
    x = g.frac_edges * 100 * (1 + rng.uniform(-0.06, 0.06, len(g)))   # slight jitter so seeds don't overlap
    ax_rand.scatter(x, g[R], color=col, marker=mk, s=34, ec="white", lw=.6, zorder=3, label=lab + f" (seeds {g.seed.min()}–{g.seed.max()})")
    med = g.groupby("frac_edges")[R].median().reset_index().sort_values("frac_edges")
    ax_rand.plot(med.frac_edges * 100, med[R], "-", color=col, lw=1.2, alpha=.5)
logx(ax_rand); ax_rand.set_xticks([50, 30, 20, 10, 5]); ax_rand.set_xticklabels(["50", "30", "20", "10", "5"]); ax_rand.set_xlim(60, 4.5)
from matplotlib.ticker import NullFormatter, NullLocator
ax_rand.xaxis.set_minor_formatter(NullFormatter()); ax_rand.xaxis.set_minor_locator(NullLocator())
ax_rand.axhline(1, ls="--", c=INK2, lw=.7); ax_rand.set_ylim(-0.05, 1.15); ax_rand.set_ylabel("MN9 rate / full model, per seed")
title(ax_rand, "d  Uniform random: all-or-nothing in the active state"); ax_rand.legend(fontsize=8, frameon=False, loc="center right")
for k, xx in [(1, 50.3), (2, 32.5), (3, 23.3), (5, 14.1), (10, 6.1)]:
    ax_rand.annotate(f"k={k}", (xx, 1.08), fontsize=7, color=INK2, ha="center")
fig.suptitle("Network state changes how sparsification fails, not how much can be removed", fontsize=11, x=0.02, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig("results/fig4_state.png", dpi=170); print("saved results/fig4_state.png")
