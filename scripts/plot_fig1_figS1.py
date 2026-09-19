"""Fig 1: problem set-up (a schematic, b magnitude vs uniform random, c synapse mass per budget).
Fig S1: sigma calibration, trial variability, null-model distributions."""
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

A = pd.read_csv("results/phaseA/summary.csv"); A2 = pd.read_csv("results/phaseA2/summary.csv"); C = pd.read_csv("results/phaseC/summary.csv")
R, P, SD, F = ["sugar100__" + x for x in ("readout_ratio", "pearson_union", "readout_trial_sd", "readout_full")]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
OP = dict(mag=("#2a78d6", "o"), act=("#eb6834", "s"), randm=("#1baf7a", "D"), rand=("#eda100", "v"), shuf=("#e87ba4", "^"), dp=("#008300", "x"))
STATE = {0.0: ("#2a78d6", "o", "silent, σ = 0"), 3.0: ("#1baf7a", "D", "active, σ = 3.0"), 3.5: ("#eb6834", "s", "active, σ = 3.5")}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.titlecolor": INK, "axes.spines.top": False, "axes.spines.right": False})
def title(ax, t): ax.set_title(t, loc="left", fontsize=10, fontweight="bold")
def logx(ax):
    ax.set_xscale("log"); ax.invert_xaxis(); ax.grid(color=GRID, lw=.8); ax.set_axisbelow(True)
    ax.set_xticks([100, 30, 10, 3, 1, 0.3]); ax.set_xticklabels(["100", "30", "10", "3", "1", "0.3"]); ax.set_xlabel("edges retained (%)")

# --------------------------------------------------------------------------------------------- Fig 1
fig = plt.figure(figsize=(13, 7.0))
gs = fig.add_gridspec(2, 2, height_ratios=[0.8, 1.0], hspace=0.35, wspace=0.28)
ax_s = fig.add_subplot(gs[0, :]); ax_b = fig.add_subplot(gs[1, 0]); ax_c = fig.add_subplot(gs[1, 1])

# (a) schematic: five boxes left -> right
ax_s.set_xlim(0, 100); ax_s.set_ylim(0, 32); ax_s.axis("off"); title(ax_s, "a  Function-preserving sparsification of a validated whole-brain model")
boxes = [
    ("Connectome graph  G = (V, E, w)", "FlyWire v630\n127,400 neurons\n14.7 M weighted edges\nw = signed synapse count", "#eaf1fb"),
    ("Sparsification operator", "budget bₖ = |{ |w| > k }|\nk ∈ {1, 2, 3, 5, 10, 20, 31, 50}\nmagnitude · uniform random\nweight-prop. random\ndegree-preserving rewire\nweight shuffle · task-aware", "#fdeee6"),
    ("Whole-brain LIF model", "Shiu et al. 2024 (Brian2)\nsilent (σ = 0) or\nspontaneously active\n(σ = 3.0 / 3.5 mV)", "#e8f7f0"),
    ("Validated tasks", "sugar GRNs → MN9\n+ bitter GRNs → suppression\nJON-CE vs JON-F → aBN1\n(pathway specificity)", "#fff6e0"),
    ("Function metrics  G′ vs G", "readout ratio (behaviour)\nPearson r · Jaccard (neural)\nsuppression index\nspecificity", "#f3f0fa"),
]
w, gap, x0, y0, h = 17.6, 2.4, 0.8, 5.0, 24.0
for i, (head, body, fc) in enumerate(boxes):
    x = x0 + i * (w + gap)
    ax_s.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=INK2, lw=.9))
    ax_s.text(x + w / 2, y0 + h - 2.0, head, ha="center", va="top", fontsize=8.0, fontweight="bold", color=INK)
    ax_s.text(x + w / 2, y0 + h - 6.6, body, ha="center", va="top", fontsize=7.1, color=INK2, linespacing=1.4)
    if i < len(boxes) - 1:
        ax_s.add_patch(FancyArrowPatch((x + w + 0.5, y0 + h / 2), (x + w + gap - 0.5, y0 + h / 2), arrowstyle="-|>", mutation_scale=12, color=INK2, lw=1.0))
ax_s.text(50, 1.0, "Every operator is evaluated at the same edge budget, so differences reflect *which* edges are kept, not how many.",
          ha="center", va="bottom", fontsize=8, color=INK2, style="italic")

# (b) magnitude vs uniform random, sigma = 0
s0 = A[(A.noise == 0) & (A.k > 0)]
for m, lab in [("mag", "magnitude (|w| > k)"), ("rand", "uniform random, same budget")]:
    g = s0[s0.method == m].groupby("k").agg(fe=("frac_edges", "first"), r=(R, "mean"), lo=(R, "min"), hi=(R, "max")).reset_index().sort_values("k")
    col, mk = OP[m]
    if m == "rand": ax_b.fill_between(g.fe * 100, g.lo, g.hi, color=col, alpha=.18, lw=0)
    ax_b.plot(g.fe * 100, g.r, "-" if m == "mag" else "--", color=col, marker=mk, ms=5, mec="white", mew=.6, lw=1.8, label=lab)
    if m == "mag":
        for _, r in g.iterrows():
            ax_b.annotate(f"k={int(r.k)}", (r.fe * 100, r.r), textcoords="offset points", xytext=(4, 5), fontsize=7, color=INK2)
logx(ax_b); ax_b.axhline(1, ls="--", c=INK2, lw=.7); ax_b.axhline(0.8, ls=":", c=INK2, lw=.7); ax_b.set_ylim(-0.05, 1.2)
ax_b.set_ylabel("MN9 rate / full model"); title(ax_b, "b  Sugar → MN9, silent network: magnitude vs random"); ax_b.legend(fontsize=8, frameon=False, loc="center left")
ax_b.annotate("cliff k* ≈ 9.4", (6.1, 0.785), xytext=(2.2, 0.55), fontsize=8, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=.7))

# (c) synapse mass retained vs edges retained (Table 1)
g = s0[s0.method == "mag"].groupby("k").agg(fe=("frac_edges", "first"), fs=("frac_syn", "first")).reset_index().sort_values("k")
ax_c.plot(g.fe * 100, g.fs * 100, "-", color=OP["mag"][0], marker="o", ms=5, mec="white", mew=.6, lw=1.8, label="magnitude")
ax_c.plot([100, 0.3], [100, 0.3], "--", color=OP["rand"][0], lw=1.4, label="uniform random (mass = edges)")
for _, r in g.iterrows():
    ax_c.annotate(f"k={int(r.k)}", (r.fe * 100, r.fs * 100), textcoords="offset points", xytext=(4, -10), fontsize=7, color=INK2)
logx(ax_c); ax_c.set_yscale("log"); ax_c.set_yticks([100, 50, 20, 10, 5, 1]); ax_c.set_yticklabels(["100", "50", "20", "10", "5", "1"]); ax_c.set_ylim(0.8, 130)
from matplotlib.ticker import NullFormatter, NullLocator
ax_c.yaxis.set_minor_formatter(NullFormatter()); ax_c.yaxis.set_minor_locator(NullLocator())
ax_c.set_ylabel("synapse mass retained (%)"); title(ax_c, "c  Weak-synapse pruning keeps most synaptic mass"); ax_c.legend(fontsize=8, frameon=False, loc="lower left")
ax_c.annotate("k = 10: 6% of edges,\n41% of synapses", (6.1, 40.7), xytext=(1.6, 60), fontsize=8, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=.7))
fig.suptitle("How sparse can a validated fly-brain model be?", fontsize=11, x=0.02, ha="left", color=INK)
fig.savefig("results/fig1_setup.png", dpi=170, bbox_inches="tight"); print("saved results/fig1_setup.png")

# --------------------------------------------------------------------------------------------- Fig S1
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
# (a) sigma calibration (300 ms, no stimulus, full model)
cal = [json.loads(l) for l in open("noise_calib_log.txt", encoding="utf-8-sig") if l.strip()]
cal = pd.DataFrame(cal).sort_values("sigma_mV")
ax = axes[0]
ax.plot(cal.sigma_mV, cal.frac_active * 100, "-", color=STATE[3.5][0], marker="s", ms=6, mec="white", lw=1.8, label="neurons active (%)")
ax.plot(cal.sigma_mV, cal.mean_rate_Hz, "-", color=STATE[0.0][0], marker="o", ms=6, mec="white", lw=1.8, label="mean rate (Hz)")
ax.annotate("σ = 3.5: p99 = 77 Hz, max = 317 Hz\n(heavy-tailed spontaneous activity)", (3.5, 25.5), textcoords="offset points", xytext=(-8, 8), fontsize=7.5, color=INK2, ha="right")
ax.set_xlabel("membrane noise σ (mV)"); ax.set_ylabel("value (300 ms, full model, no stimulus)"); ax.set_xticks([1.5, 2.5, 3.0, 3.5]); ax.grid(color=GRID, lw=.8); ax.set_axisbelow(True)
ax.axvline(3.0, color=STATE[3.0][0], lw=.8, ls="--"); ax.axvline(3.5, color=STATE[3.5][0], lw=.8, ls="--")
ax.text(2.98, 14, "σ_low", color=STATE[3.0][0], fontsize=8, ha="right"); ax.text(3.48, 14, "σ_mid", color=STATE[3.5][0], fontsize=8, ha="right")
title(ax, "a  Spontaneous activity vs noise σ"); ax.legend(fontsize=8, frameon=False, loc="upper left"); ax.set_ylim(-1, 32)
ax.text(0.03, 0.55, "threshold 7 mV ≈ 2–3 × σ/√2:\nthe network switches on\nbetween σ = 2.5 and 3.5", ha="left", va="center", fontsize=7.5, color=INK2, transform=ax.transAxes)

# (b) trial-to-trial variability of the readout (magnitude pruning), CV = SD / mean of the full model
ax = axes[1]
for nz, src, n in [(0.0, A[A.noise == 0], 3), (3.0, A2[A2.noise == 3.0], 10), (3.5, A2[A2.noise == 3.5], 10)]:
    g = src[(src.method == "mag")].sort_values("k"); col, mk, lab = STATE[nz]
    x = np.where(g.k == 0, 100.0, g.frac_edges * 100)
    ax.plot(x, g[SD] / g[F], "-", color=col, marker=mk, ms=5, mec="white", mew=.6, lw=1.8, label=f"{lab} (trial {n})")
logx(ax); ax.set_xticks([100, 30, 10, 3, 1]); ax.set_xticklabels(["100\n(full)", "30", "10", "3", "1"]); ax.set_ylabel("trial SD of MN9 rate / full-model mean")
title(ax, "b  Trial variability of the readout (mag)"); ax.legend(fontsize=8, frameon=False, loc="upper left")

# (c) null-model distributions per seed, sugar sigma = 0, k = 2 / 5 / 10
ax = axes[2]
s0 = pd.concat([A[A.noise == 0], C[C.task == "sugar"]]); s0 = s0[s0.k.isin([2, 5, 10])]
ops = ["rand", "randm", "dp", "shuf"]; xs = {2: 0, 5: 1, 10: 2}
for j, m in enumerate(ops):
    g = s0[s0.method == m]; col, mk = OP[m]
    x = g.k.map(xs) + (j - 1.5) * 0.18
    ax.scatter(x, g[R], color=col, marker=mk, s=30, ec="white", lw=.5, zorder=3, label={"rand": "uniform random", "randm": "weight-prop. random", "dp": "degree-preserving rewire", "shuf": "weight shuffle"}[m])
for k, xi in xs.items():
    r = float(A[(A.noise == 0) & (A.method == "mag") & (A.k == k)][R].iloc[0])
    ax.hlines(r, xi - 0.42, xi + 0.42, color=OP["mag"][0], lw=1.6, zorder=2)
    ax.text(xi + 0.44, r, "mag", fontsize=7, color=OP["mag"][0], va="center")
ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["k = 2\n(32% edges)", "k = 5\n(14%)", "k = 10\n(6%)"]); ax.set_ylim(-0.05, 1.15); ax.grid(color=GRID, lw=.8, axis="y"); ax.set_axisbelow(True)
ax.set_ylabel("MN9 rate / full model, per seed"); title(ax, "c  Null models, sugar σ = 0, per seed"); ax.legend(fontsize=7.5, frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.45))
fig.suptitle("Supplementary: noise calibration, trial variability, and null-model spread", fontsize=11, x=0.02, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig("results/figS1_calibration.png", dpi=170); print("saved results/figS1_calibration.png")
