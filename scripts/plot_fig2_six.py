"""Fig 2 (v2): six sparsification operators on the sugar task, silent network (sigma = 0).
Phase A supplies mag/rand/dp/act, Phase C supplies shuf/randm. Bands = min-max over 3 seeds for stochastic operators."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

A = pd.read_csv("results/phaseA/summary.csv"); C = pd.read_csv("results/phaseC/summary.csv")
S = pd.concat([A[(A.task == "sugar") & (A.noise == 0)], C[C.task == "sugar"]]); S = S[S.k > 0]
R, P, N = "sugar100__readout_ratio", "sugar100__pearson_union", "sugar100__n_active"
g = S.groupby(["method", "k"]).agg(fe=("frac_edges", "first"), fs=("frac_syn", "mean"),
    r=(R, "mean"), r0=(R, "min"), r1=(R, "max"), p=(P, "mean"), p0=(P, "min"), p1=(P, "max"),
    n=(N, "mean"), n0=(N, "min"), n1=(N, "max")).reset_index()

# fixed categorical order (validated 6-slot palette, light surface); nulls dashed as secondary encoding
OPS = [("mag",   "magnitude (|w| > k)",            "#2a78d6", "o", "-"),
       ("act",   "task-aware (|w|(1+r_pre))",       "#eb6834", "s", "-"),
       ("randm", "random, weight-proportional",     "#1baf7a", "D", "-"),
       ("rand",  "random, uniform",                 "#eda100", "v", "--"),
       ("shuf",  "weight shuffle (position kept)",  "#e87ba4", "^", "--"),
       ("dp",    "degree-preserving rewire",        "#008300", "x", "--")]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.titlecolor": INK, "axes.spines.top": False, "axes.spines.right": False})

fig, axes = plt.subplots(2, 2, figsize=(10.5, 8))
(ax_r, ax_p), (ax_n, ax_m) = axes
def band(ax, x, lo, hi, color):
    ax.fill_between(x, lo, hi, color=color, alpha=.18, lw=0)
for m, lab, col, mk, ls in OPS:
    s = g[g.method == m].sort_values("k")
    x = s.fe * 100
    for ax, y, lo, hi in [(ax_r, s.r, s.r0, s.r1), (ax_p, s.p, s.p0, s.p1), (ax_n, s.n, s.n0, s.n1)]:
        if m in ("rand", "randm", "shuf", "dp"): band(ax, x, lo, hi, col)
        ax.plot(x, y, ls, color=col, marker=mk, ms=5, lw=1.8, label=lab, mec="white", mew=.6)
    if m in ("rand", "randm", "shuf", "dp"): band(ax_m, s.fs * 100, s.r0, s.r1, col)
    ax_m.plot(s.fs * 100, s.r, ls, color=col, marker=mk, ms=5, lw=1.8, mec="white", mew=.6)

# k annotations on the magnitude curve (panel a)
mg = g[g.method == "mag"].sort_values("k")
for _, r in mg.iterrows():
    ax_r.annotate(f"k={int(r.k)}", (r.fe * 100, r.r), textcoords="offset points", xytext=(4, 5), fontsize=7, color=INK2)

for ax, yl, ttl in [(ax_r, "MN9 rate / full model", "a  Behavioural readout"), (ax_p, "Pearson r, active union", "b  Population response"),
                    (ax_n, "active neurons (full: 348–361)", "c  Active population"), (ax_m, "MN9 rate / full model", "d  Readout vs synapse mass retained")]:
    ax.set_xscale("log"); ax.invert_xaxis(); ax.grid(color=GRID, lw=.8); ax.set_axisbelow(True)
    ax.set_ylabel(yl); ax.set_title(ttl, loc="left", fontsize=10, fontweight="bold")
    ax.set_xlabel("edges retained (%)" if ax is not ax_m else "synapse mass retained (%)")
    ax.set_xticks([100, 30, 10, 3, 1, 0.3]); ax.set_xticklabels(["100", "30", "10", "3", "1", "0.3"])
for ax in (ax_r, ax_m):
    ax.axhline(1, ls="--", c=INK2, lw=.7); ax.axhline(0.8, ls=":", c=INK2, lw=.7); ax.set_ylim(-0.05, 1.25)
ax_p.axhline(0, c=INK2, lw=.5); ax_p.set_ylim(-0.35, 1.05)
ax_m.set_xticks([100, 50, 20, 10, 5]); ax_m.set_xticklabels(["100", "50", "20", "10", "5"]); ax_m.set_xlim(105, 3)

# selective direct labels (panel a and d)
ax_r.text(0.45, 1.08, "task-aware", color=INK2, fontsize=8, ha="right", va="bottom")
ax_r.text(2.6, 0.05, "weight\nshuffle", color=INK2, fontsize=8, ha="right", va="bottom")
ax_r.text(52, 0.13, "uniform random", color=INK2, fontsize=8, ha="left", va="bottom")
ax_r.text(9.2, 0.38, "weight-\nproportional\nrandom", color=INK2, fontsize=8, ha="left", va="center")
ax_m.text(43, 0.30, "randm k=5", color=INK2, fontsize=8, ha="right", va="center")
ax_m.text(38, 0.76, "mag k=10", color=INK2, fontsize=8, ha="left", va="top")
ax_m.text(48, 0.12, "rand k=1", color=INK2, fontsize=8, ha="left", va="bottom")
ax_m.text(51, 0.905, "randm k=3", color=INK2, fontsize=8, ha="left", va="center")
ax_m.text(9.5, 1.08, "act k=50", color=INK2, fontsize=8, ha="left", va="bottom")

handles = [Line2D([], [], color=c, marker=mk, ls=ls, ms=5, lw=1.8, mec="white", mew=.6, label=l) for _, l, c, mk, ls in OPS]
ax_r.legend(handles=handles, fontsize=7.5, loc="center right", bbox_to_anchor=(1.0, 0.52), frameon=False, labelcolor=INK)
fig.suptitle("Sugar → MN9, silent network (σ = 0): what each operator keeps decides what survives", fontsize=11, x=0.02, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig("results/fig2_sugar_six.png", dpi=170); print("saved results/fig2_sugar_six.png")
