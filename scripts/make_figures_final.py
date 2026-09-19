"""Publication-size figures (two-column width 7.2 in, 7.5 pt type, 300 dpi PNG + PDF), one consistent style.
Fig 1 set-up · Fig 2 six operators · Fig 3 dissociation · Fig 4 network state · Fig 5 task dependence + task-aware transfer ·
Fig 6 anatomy · Fig S1 calibration/variability/nulls · Fig S3 class-pair survival.   usage: python make_figures_final.py"""
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import NullFormatter, NullLocator
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

OUT = Path("results/final"); OUT.mkdir(parents=True, exist_ok=True)
A = pd.read_csv("results/phaseA/summary.csv"); A2 = pd.read_csv("results/phaseA2/summary.csv"); B = pd.read_csv("results/phaseB/summary.csv")
C = pd.read_csv("results/phaseC/summary.csv"); D = pd.read_csv("results/phaseD/summary.csv")
R, P, J, N, SD, F = ["sugar100__" + x for x in ("readout_ratio", "pearson_union", "jaccard_active", "n_active", "readout_trial_sd", "readout_full")]

# ---- style: validated 6-slot categorical palette (light surface), neutral ink for all text
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
OP = dict(mag=("#2a78d6", "o", "-"), act=("#eb6834", "s", "-"), randm=("#1baf7a", "D", "-"),
          rand=("#eda100", "v", "--"), shuf=("#e87ba4", "^", "--"), dp=("#008300", "x", "--"))
OPNAME = dict(mag="magnitude (|w| > k)", act="task-aware", randm="weight-proportional random", rand="uniform random",
              shuf="weight shuffle", dp="degree-preserving rewire")
STATE = {0.0: ("#2a78d6", "o", "silent, σ = 0"), 3.0: ("#1baf7a", "D", "active, σ = 3.0 mV"), 3.5: ("#eb6834", "s", "active, σ = 3.5 mV")}
TASK = dict(sugar=("#2a78d6", "o", "sugar → MN9 (readout ratio)"), bitter=("#e34948", "s", "bitter suppression of MN9 (SI / SI_full)"),
            groom=("#008300", "^", "JON-CE vs JON-F → aBN1 (specificity / full)"))
plt.rcParams.update({"font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "lines.linewidth": 1.3, "lines.markersize": 3.5, "legend.frameon": False, "legend.handlelength": 2.0, "pdf.fonttype": 42})
MS, LW = 3.5, 1.3
W = 7.2  # two-column width (inches)

def panel(ax, letter, text=""):
    ax.set_title(f"{letter}  {text}" if text else letter, loc="left", fontweight="bold", pad=4)

def logx(ax, ticks=(100, 30, 10, 3, 1, 0.3)):
    ax.set_xscale("log"); ax.invert_xaxis(); ax.grid(color=GRID, lw=.5); ax.set_axisbelow(True)
    ax.set_xticks(list(ticks)); ax.set_xticklabels([f"{t:g}" for t in ticks]); ax.set_xlabel("edges retained (%)")
    ax.xaxis.set_minor_formatter(NullFormatter()); ax.xaxis.set_minor_locator(NullLocator())

def klabels(ax, x, y, ks, dx=3, dy=3, skip=(), color=INK2):
    for xi, yi, ki in zip(x, y, ks):
        if ki not in skip: ax.annotate(f"k={int(ki)}", (xi, yi), textcoords="offset points", xytext=(dx, dy), fontsize=6, color=color)

def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=300); fig.savefig(OUT / f"{name}.pdf"); plt.close(fig); print("saved", name)

def agg(df, col):
    return df.groupby("k").agg(fe=("frac_edges", "first"), fs=("frac_syn", "mean"), m=(col, "mean"), lo=(col, "min"), hi=(col, "max")).reset_index().sort_values("k")

# =============================================================================================== Fig 1
fig = plt.figure(figsize=(W, 4.6))
gs = fig.add_gridspec(2, 2, height_ratios=[0.62, 1.0], hspace=0.38, wspace=0.32, left=0.08, right=0.98, top=0.95, bottom=0.10)
ax_s = fig.add_subplot(gs[0, :]); ax_b = fig.add_subplot(gs[1, 0]); ax_c = fig.add_subplot(gs[1, 1])
ax_s.set_xlim(0, 100); ax_s.set_ylim(0, 30); ax_s.axis("off"); panel(ax_s, "a", "pipeline")
boxes = [("Connectome graph", "G = (V, E, w), FlyWire v630\n127,400 neurons\n14.7 M weighted edges\nw = signed synapse count", "#eaf1fb"),
         ("Sparsification operator", "budget bₖ = |{ |w| > k }|\nk ∈ {1, 2, 3, 5, 10,\n20, 31, 50}\n6 operators (Table 2)", "#fdeee6"),
         ("Whole-brain LIF model", "Shiu et al. 2024 (Brian2)\nsilent (σ = 0) or\nspontaneously active\n(σ = 3.0 / 3.5 mV)", "#e8f7f0"),
         ("Validated tasks", "sugar GRNs → MN9\n+ bitter GRNs → suppression\nJON-CE vs JON-F → aBN1\n(pathway specificity)", "#fff6e0"),
         ("Function metrics", "G′ vs G: readout ratio (behaviour)\nPearson r, Jaccard (neural)\nsuppression index\nspecificity", "#f3f0fa")]
bw, gap, x0, y0, bh = 18.0, 2.5, 0.0, 3.5, 24.5
for i, (head, body, fc) in enumerate(boxes):
    x = x0 + i * (bw + gap)
    ax_s.add_patch(FancyBboxPatch((x, y0), bw, bh, boxstyle="round,pad=0.3,rounding_size=1.0", fc=fc, ec=INK2, lw=.6))
    ax_s.text(x + bw / 2, y0 + bh - 1.8, head, ha="center", va="top", fontsize=6.6, fontweight="bold", color=INK)
    ax_s.text(x + bw / 2, y0 + bh - 7.2, body, ha="center", va="top", fontsize=6.0, color=INK2, linespacing=1.35)
    if i < len(boxes) - 1:
        ax_s.add_patch(FancyArrowPatch((x + bw + 0.3, y0 + bh / 2), (x + bw + gap - 0.3, y0 + bh / 2), arrowstyle="-|>", mutation_scale=8, color=INK2, lw=.8))
ax_s.text(50, 0.2, "all operators are compared at the same edge budget bₖ", ha="center", va="bottom", fontsize=6.3, color=INK2, style="italic")

s0 = A[(A.noise == 0) & (A.k > 0)]
for m in ["mag", "rand"]:
    g = agg(s0[s0.method == m], R); col, mk, ls = OP[m]
    if m == "rand": ax_b.fill_between(g.fe * 100, g.lo, g.hi, color=col, alpha=.18, lw=0)
    ax_b.plot(g.fe * 100, g.m, ls, color=col, marker=mk, mec="white", mew=.5, label=OPNAME[m] + (" (band: 3 seeds)" if m == "rand" else ""))
    if m == "mag": klabels(ax_b, g.fe * 100, g.m, g.k, skip=(2, 3, 5)); ax_b.annotate("k=5", (14.1, 0.951), textcoords="offset points", xytext=(3, -9), fontsize=6, color=INK2)
logx(ax_b); ax_b.axhline(1, ls="--", c=INK2, lw=.5); ax_b.axhline(0.8, ls=":", c=INK2, lw=.5); ax_b.set_ylim(-0.05, 1.2)
ax_b.set_ylabel("MN9 rate / full model"); panel(ax_b, "b", "sugar → MN9, silent network"); ax_b.legend(loc="upper right")
ax_b.annotate("k* ≈ 9.4", (6.1, 0.785), xytext=(2.3, 0.5), fontsize=6.5, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=.5))
g = agg(s0[s0.method == "mag"], R)
ax_c.plot(g.fe * 100, g.fs * 100, "-", color=OP["mag"][0], marker="o", mec="white", mew=.5, label="magnitude")
ax_c.plot([100, 0.3], [100, 0.3], "--", color=OP["rand"][0], label="uniform random (mass = edges)")
klabels(ax_c, g.fe * 100, g.fs * 100, g.k, dx=3, dy=-8, skip=(2, 3))
logx(ax_c); ax_c.set_yscale("log"); ax_c.set_yticks([100, 50, 20, 10, 5, 1]); ax_c.set_yticklabels(["100", "50", "20", "10", "5", "1"]); ax_c.set_ylim(0.8, 130)
ax_c.yaxis.set_minor_formatter(NullFormatter()); ax_c.yaxis.set_minor_locator(NullLocator())
ax_c.set_ylabel("synapse mass retained (%)"); panel(ax_c, "c", "mass retained per budget"); ax_c.legend(loc="lower left")
save(fig, "fig1")

# =============================================================================================== Fig 2
S = pd.concat([A[(A.noise == 0)], C[C.task == "sugar"]]); S = S[S.k > 0]
fig, axes = plt.subplots(2, 2, figsize=(W, 6.0)); (ax_r, ax_p), (ax_n, ax_m) = axes
for m in ["mag", "act", "randm", "rand", "shuf", "dp"]:
    col, mk, ls = OP[m]; stoch = m in ("rand", "randm", "shuf", "dp")
    for ax, col_ in [(ax_r, R), (ax_p, P), (ax_n, N)]:
        g = agg(S[S.method == m], col_); x = g.fe * 100
        if stoch: ax.fill_between(x, g.lo, g.hi, color=col, alpha=.18, lw=0)
        ax.plot(x, g.m, ls, color=col, marker=mk, mec="white", mew=.5, label=OPNAME[m])
    g = agg(S[S.method == m], R)
    if stoch: ax_m.fill_between(g.fs * 100, g.lo, g.hi, color=col, alpha=.18, lw=0)
    ax_m.plot(g.fs * 100, g.m, ls, color=col, marker=mk, mec="white", mew=.5)
g = agg(S[S.method == "mag"], R); klabels(ax_r, g.fe * 100, g.m, g.k, dx=3, dy=4, skip=(2, 3, 5)); ax_r.annotate("k=5", (14.1, 0.951), textcoords="offset points", xytext=(3, -9), fontsize=6, color=INK2)
for ax, yl, t in [(ax_r, "MN9 rate / full model", "behavioural readout"), (ax_p, "Pearson r (active union)", "population response"),
                  (ax_n, "active neurons (full model: 348–361)", "active population")]:
    logx(ax); ax.set_ylabel(yl)
panel(ax_r, "a", "behavioural readout"); panel(ax_p, "b", "population response"); panel(ax_n, "c", "active population"); panel(ax_m, "d", "readout vs synapse mass retained")
ax_r.axhline(1, ls="--", c=INK2, lw=.5); ax_r.axhline(0.8, ls=":", c=INK2, lw=.5); ax_r.set_ylim(-0.05, 1.25)
ax_p.axhline(0, c=INK2, lw=.5); ax_p.set_ylim(-0.35, 1.05)
ax_m.set_xscale("log"); ax_m.invert_xaxis(); ax_m.grid(color=GRID, lw=.5); ax_m.set_axisbelow(True)
ax_m.set_xticks([100, 50, 20, 10, 5]); ax_m.set_xticklabels(["100", "50", "20", "10", "5"]); ax_m.set_xlim(105, 3)
ax_m.xaxis.set_minor_formatter(NullFormatter()); ax_m.xaxis.set_minor_locator(NullLocator())
ax_m.set_xlabel("synapse mass retained (%)"); ax_m.set_ylabel("MN9 rate / full model"); ax_m.axhline(1, ls="--", c=INK2, lw=.5); ax_m.axhline(0.8, ls=":", c=INK2, lw=.5); ax_m.set_ylim(-0.05, 1.25)
ax_m.text(43, 0.30, "randm k=5", fontsize=6, color=INK2, ha="right", va="center"); ax_m.text(38, 0.76, "mag k=10", fontsize=6, color=INK2, ha="left", va="top")
ax_m.text(48, 0.12, "rand k=1", fontsize=6, color=INK2, ha="left", va="bottom"); ax_m.text(51, 0.905, "randm k=3", fontsize=6, color=INK2, ha="left", va="center")
ax_m.text(9.5, 1.08, "act k=50", fontsize=6, color=INK2, ha="left", va="bottom")
h, l = ax_r.get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.035), columnspacing=1.6)
fig.text(0.5, 0.005, "bands: min–max over seeds (rand, dp, shuf: 3 seeds; randm k = 3, 5: 5 seeds); deterministic operators: one run of 3 trials", fontsize=6, color=INK2, ha="center")
fig.tight_layout(rect=(0, 0.075, 1, 1)); save(fig, "fig2")

# =============================================================================================== Fig 3
s35 = A2[(A2.noise == 3.5) & (A2.k > 0)]
fig, axes = plt.subplots(1, 3, figsize=(W, 2.7))
ax = axes[0]
for m in ["mag", "act", "randm"]:
    g = S[S.method == m].groupby("k").agg(r=(R, "mean"), j=(J, "mean")).reset_index().sort_values("k"); col, mk, _ = OP[m]
    ax.plot(g.j, g.r, "-", color=col, lw=.9, alpha=.6); ax.scatter(g.j, g.r, color=col, marker=mk, s=16, ec="white", lw=.4, zorder=3, label={"mag": "magnitude", "act": "task-aware", "randm": "weight-prop. random"}[m])
    if m == "mag":
        for _, r in g.iterrows():
            if r.k >= 5: ax.annotate(f"k={int(r.k)}", (r.j, r.r), textcoords="offset points", xytext={5: (-18, -10), 10: (5, -3), 20: (4, -8)}.get(r.k, (4, 3)), fontsize=6, color=INK2)
    if m == "randm":
        for _, r in g.iterrows():
            if r.k in (3, 5): ax.annotate(f"randm k={int(r.k)}", (r.j, r.r), textcoords="offset points", xytext=(-5, 7), fontsize=6, color=INK2, ha="right")
ax.plot([0, 1], [0, 1], ls="--", c=INK2, lw=.5); ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.05, 1.15); ax.grid(color=GRID, lw=.5); ax.set_axisbelow(True)
ax.set_xlabel("active-set Jaccard vs full model"); ax.set_ylabel("MN9 rate / full model"); panel(ax, "a", "silent network (σ = 0)"); ax.legend(loc="upper left")
ax = axes[1]
for m in ["mag", "act"]:
    g = s35[s35.method == m].sort_values("k"); col, mk, _ = OP[m]
    ax.plot(g[P], g[R], "-", color=col, lw=.9, alpha=.6)
    ax.errorbar(g[P], g[R], yerr=g[SD] / np.sqrt(10) / g[F], fmt=mk, color=col, ms=MS, mec="white", mew=.4, capsize=1.5, lw=.6, zorder=3, label=OPNAME[m] + " ± SE")
    if m == "mag":
        for _, r in g.iterrows():
            if r.k in (5, 31): ax.annotate(f"k={int(r.k)}", (r[P], r[R]), textcoords="offset points", xytext=(4, 3), fontsize=6, color=INK2)
        ax.annotate("k = 1, 3, 10, 20", (0.97, 1.15), textcoords="offset points", xytext=(-34, 16), fontsize=6, color=INK2, ha="right", arrowprops=dict(arrowstyle="-", color=INK2, lw=.4))
g = s35[s35.method == "rand"]; ax.scatter(g[P], g[R], color=OP["rand"][0], marker="v", s=14, ec="white", lw=.4, zorder=3, label="uniform random, each seed")
ax.plot([0, 1], [0, 1], ls="--", c=INK2, lw=.5); ax.axhline(1, ls=":", c=INK2, lw=.5); ax.set_xlim(-0.05, 1.05); ax.set_ylim(-0.05, 2.7); ax.grid(color=GRID, lw=.5); ax.set_axisbelow(True)
ax.set_xlabel("Pearson r (active union)"); ax.set_ylabel("MN9 rate / full model"); panel(ax, "b", "active network (σ = 3.5, 10 trials)"); ax.legend(loc="upper left")
ax = axes[2]
for nz, src in [(0.0, A[A.noise == 0]), (3.0, A2[A2.noise == 3.0]), (3.5, A2[A2.noise == 3.5])]:
    g = src[(src.method == "mag") & (src.k > 0)].sort_values("k"); col, mk, lab = STATE[nz]
    ax.plot(g.frac_edges * 100, g[R] - g[P], "-", color=col, marker=mk, mec="white", mew=.5, label=f"σ = {nz:g}: readout − r")
g = A[(A.noise == 0) & (A.method == "mag") & (A.k > 0)].sort_values("k")
ax.plot(g.frac_edges * 100, g[R] - g[J], ":", color=STATE[0.0][0], marker="o", mfc="white", lw=1.0, label="σ = 0: readout − Jaccard")
ax.axhline(0, c=INK2, lw=.5); logx(ax); ax.set_ylabel("dissociation index"); panel(ax, "c", "dissociation index"); ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.0)); ax.set_ylim(-1.0, 0.85)
fig.tight_layout(); save(fig, "fig3")

# =============================================================================================== Fig 4
fig, axes = plt.subplots(2, 2, figsize=(W, 6.0)); (ax_r, ax_p), (ax_si, ax_rand) = axes
for nz, src, n in [(0.0, A[A.noise == 0], 3), (3.0, A2[A2.noise == 3.0], 10), (3.5, A2[A2.noise == 3.5], 10)]:
    g = src[(src.method == "mag") & (src.k > 0)].sort_values("k"); col, mk, lab = STATE[nz]; x = g.frac_edges * 100
    ax_r.errorbar(x, g[R], yerr=g[SD] / np.sqrt(n) / g[F], fmt="-", marker=mk, color=col, mec="white", mew=.5, capsize=1.5, lw=LW, label=f"{lab} ({n} trials)")
    ax_p.plot(x, g[P], "-", marker=mk, color=col, mec="white", mew=.5, label=lab)
logx(ax_r); logx(ax_p); ax_r.set_ylabel("MN9 rate / full model (± SE)"); ax_p.set_ylabel("Pearson r (active union)")
panel(ax_r, "a", "readout, magnitude pruning"); panel(ax_p, "b", "population response, magnitude pruning")
ax_r.axhline(1, ls="--", c=INK2, lw=.5); ax_r.axhline(0.8, ls=":", c=INK2, lw=.5); ax_r.set_ylim(-0.05, 2.0); ax_r.legend(loc="lower left")
ax_p.axhline(0, c=INK2, lw=.5); ax_p.set_ylim(-0.05, 1.05); ax_p.legend(loc="lower left")
for nz, src, n in [(0.0, B[(B.task == "bitter") & (B.noise == 0) & (B.method == "mag")], 3), (3.5, D[D.method == "mag"], 10)]:
    g = src.sort_values("k").copy(); col, mk, lab = STATE[nz]
    su, sb = g["sugar100__readout"], g["sugar100_bitter100__readout"]; si = 1 - sb / su.replace(0, np.nan)
    se_su, se_sb = g["sugar100__readout_trial_sd"] / np.sqrt(n), g["sugar100_bitter100__readout_trial_sd"] / np.sqrt(n)
    se_si = (sb / su) * np.sqrt((se_sb / sb.replace(0, np.nan)) ** 2 + (se_su / su.replace(0, np.nan)) ** 2)
    x = np.where(g.k == 0, 100.0, g.frac_edges * 100)
    ax_si.errorbar(x, si, yerr=se_si.fillna(0), fmt="-", marker=mk, color=col, mec="white", mew=.5, capsize=1.5, lw=LW, label=f"{lab} ({n} trials)")
    klabels(ax_si, x[g.k > 0], si[g.k > 0], g.k[g.k > 0], dy=4 if nz == 0 else -9)
ax_si.axhline(0, c=INK2, lw=.5); logx(ax_si, ticks=(100, 30, 10, 3, 1)); ax_si.set_xticklabels(["100\n(full)", "30", "10", "3", "1"])
ax_si.set_ylabel("suppression index  1 − MN9(sugar+bitter)/MN9(sugar)"); ax_si.set_ylim(-0.95, 1.1); panel(ax_si, "c", "bitter suppression by state"); ax_si.legend(loc="lower left")
rng = np.random.default_rng(0)
for nz, src in [(0.0, A[A.noise == 0]), (3.5, A2[A2.noise == 3.5])]:
    g = src[(src.method == "rand") & (src.k.isin([1, 2, 3, 5, 10]))]; col, mk, lab = STATE[nz]
    x = g.frac_edges * 100 * (1 + rng.uniform(-0.06, 0.06, len(g)))
    ax_rand.scatter(x, g[R], color=col, marker=mk, s=16, ec="white", lw=.4, zorder=3, label=f"{lab} (seeds {g.seed.min()}–{g.seed.max()})")
    med = g.groupby("frac_edges")[R].median().reset_index().sort_values("frac_edges"); ax_rand.plot(med.frac_edges * 100, med[R], "-", color=col, lw=.9, alpha=.5)
logx(ax_rand, ticks=(50, 30, 20, 10, 5)); ax_rand.set_xlim(60, 4.5); ax_rand.axhline(1, ls="--", c=INK2, lw=.5); ax_rand.set_ylim(-0.05, 1.18)
ax_rand.set_ylabel("MN9 rate / full model, per seed"); panel(ax_rand, "d", "uniform random, per seed"); ax_rand.legend(loc="center right")
for k, xx in [(1, 50.3), (2, 32.5), (3, 23.3), (5, 14.1), (10, 6.1)]: ax_rand.annotate(f"k={k}", (xx, 1.09), fontsize=6, color=INK2, ha="center")
fig.tight_layout(); save(fig, "fig4")

# =============================================================================================== Fig 5 (task dependence + task-aware transfer)
def bitter_si(df):
    d = df.copy(); d["SI_full"] = 1 - d["sugar100_bitter100__readout_full"] / d["sugar100__readout_full"]
    d["SI"] = 1 - d["sugar100_bitter100__readout"] / d["sugar100__readout"].replace(0, np.nan); return d
def groom_spec(df):
    d = df.copy(); d["spec_full"] = d["jonCE100__readout_full"] - d["jonF100__readout_full"]; d["spec"] = d["jonCE100__readout"] - d["jonF100__readout"]; return d
fig, axes = plt.subplots(2, 2, figsize=(W, 6.0)); (ax0, ax1), (ax2, ax3) = axes
for ax, nz in [(ax0, 0.0), (ax1, 3.5)]:
    sug = (A[A.noise == 0] if nz == 0 else A2[A2.noise == 3.5]); sug = sug[(sug.method == "mag") & (sug.k > 0)].sort_values("k")
    col, mk, lab = TASK["sugar"]; ax.plot(sug.frac_edges * 100, sug[R], "-", color=col, marker=mk, mec="white", mew=.5, label=lab)
    klabels(ax, sug.frac_edges * 100, sug[R], sug.k, dy=4, skip=(2, 3), color=INK2)
    bt = bitter_si(B[(B.task == "bitter") & (B.noise == 0) & (B.method == "mag") & (B.k > 0)] if nz == 0 else D[(D.method == "mag") & (D.k > 0)]).sort_values("k")
    col, mk, lab = TASK["bitter"]; ax.plot(bt.frac_edges * 100, bt.SI / bt.SI_full, "-", color=col, marker=mk, mec="white", mew=.5, label=lab)
    gr = groom_spec(B[(B.task == "groom") & (B.noise == nz) & (B.method == "mag") & (B.k > 0)]).sort_values("k")
    col, mk, lab = TASK["groom"]; ax.plot(gr.frac_edges * 100, gr.spec / gr.spec_full, "-", color=col, marker=mk, mec="white", mew=.5, label=lab)
    ax.axhline(1, ls="--", c=INK2, lw=.5); ax.axhline(0.8, ls=":", c=INK2, lw=.5); ax.axhline(0, c=INK2, lw=.5); logx(ax); ax.set_ylim(-0.9, 1.8)
    ax.set_ylabel("function preserved (relative to full model)")
panel(ax0, "a", "magnitude pruning, silent network (σ = 0)"); panel(ax1, "b", "magnitude pruning, active network (σ = 3.5)"); ax0.legend(loc="lower left")
# (c) held-out bitter suppression: magnitude vs task-aware, sigma 0 and 3.5
for nz, src_mag, src_act, ls, tag in [(0.0, B[(B.task == "bitter") & (B.noise == 0)], C[(C.task == "bitter") & (C.noise == 0)], "-", "σ = 0"),
                                     (3.5, D, C[(C.task == "bitter") & (C.noise == 3.5)], "--", "σ = 3.5")]:
    for src, m in [(src_mag, "mag"), (src_act, "act")]:
        g = bitter_si(src[(src.method == m) & (src.k > 0)]).sort_values("k"); col, mk, _ = OP[m]
        ax2.plot(g.frac_edges * 100, g.SI, ls, color=col, marker=mk, mec="white", mew=.5, label=f"{OPNAME[m].split(' (')[0]}, {tag}")
ax2.axhline(0, c=INK2, lw=.5); logx(ax2, ticks=(30, 10, 3, 1)); ax2.set_ylim(-0.7, 1.1); ax2.set_ylabel("suppression index (held-out bitter)"); panel(ax2, "c", "task-aware vs magnitude: bitter"); ax2.legend(loc="lower left")
ax2.text(0.98, 0.96, "task-aware trained on sugar only", ha="right", va="top", fontsize=6, color=INK2, transform=ax2.transAxes)
# (d) held-out groom specificity: magnitude vs task-aware
for nz, ls, tag in [(0.0, "-", "σ = 0"), (3.5, "--", "σ = 3.5")]:
    for src, m in [(B[(B.task == "groom") & (B.noise == nz)], "mag"), (C[(C.task == "groom") & (C.noise == nz)], "act")]:
        g = groom_spec(src[(src.method == m) & (src.k > 0)]).sort_values("k"); col, mk, _ = OP[m]
        ax3.plot(g.frac_edges * 100, g.spec / g.spec_full, ls, color=col, marker=mk, mec="white", mew=.5, label=f"{OPNAME[m].split(' (')[0]}, {tag}")
ax3.axhline(1, ls="--", c=INK2, lw=.5); ax3.axhline(0, c=INK2, lw=.5); logx(ax3, ticks=(30, 10, 3, 1)); ax3.set_ylim(-0.3, 1.9)
ax3.set_ylabel("specificity / full model (held-out JON-F)"); panel(ax3, "d", "task-aware vs magnitude: grooming"); ax3.legend(loc="center right", bbox_to_anchor=(1.0, 0.32))
ax3.text(0.02, 0.96, "task-aware trained on JON-CE only", ha="left", va="top", fontsize=6, color=INK2, transform=ax3.transAxes)
fig.tight_layout(); save(fig, "fig5")

# =============================================================================================== Fig 6 (anatomy, restyled)
sg = pd.read_csv("results/anatomy/sign_by_k.csv"); ei = pd.read_csv("results/anatomy/ei_balance_by_k.csv")
fe_of_k = {int(k): (1 - v) * 100 for k, v in zip(sg.k, sg.frac_edges_removed)}
fig, axes = plt.subplots(1, 3, figsize=(W, 2.7))
ax = axes[0]; x = sg.k.map(fe_of_k)
ax.plot(x, sg.inh_mass_share_kept, "-", color=OP["mag"][0], marker="o", mec="white", mew=.5, label="kept edges")
ax.plot(x, sg.inh_mass_share_removed, "--", color=OP["rand"][0], marker="v", mec="white", mew=.5, label="removed edges")
ax.axhline(0.404, ls=":", c=INK2, lw=.5); ax.text(0.5, 0.406, "whole graph 0.40", fontsize=6, color=INK2, ha="left", va="bottom")
klabels(ax, x, sg.inh_mass_share_kept, sg.k, dy=4, skip=(1, 2, 3, 5))
logx(ax, ticks=(100, 30, 10, 3, 1)); ax.set_ylim(0.38, 0.51); ax.set_ylabel("inhibitory share of synapse mass"); panel(ax, "a", "sign of kept vs removed mass"); ax.legend(loc="upper left")
ax = axes[1]; x = ei.k.map(fe_of_k)
ax.plot(x, ei.frac_neurons_lost_all_inhibition * 100, "-", color="#e34948", marker="o", mec="white", mew=.5, label="lost all inhibitory input")
ax.plot(x, ei.frac_neurons_lost_all_excitation * 100, "-", color=OP["mag"][0], marker="s", mec="white", mew=.5, label="lost all excitatory input")
klabels(ax, x, ei.frac_neurons_lost_all_excitation * 100, ei.k, dx=-16, dy=5, skip=(1, 2, 3, 31, 50))
logx(ax, ticks=(100, 30, 10, 3, 1)); ax.set_ylabel("neurons losing one input sign (%)"); panel(ax, "b", "neurons losing one input sign"); ax.legend(loc="upper left")
ax = axes[2]
IDS = json.load(open("task_ids.json"))
con = pd.read_parquet("repos/Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet", columns=["Presynaptic_ID", "Excitatory x Connectivity"])
for name, ids, col, ls in [("sugar → MN9", IDS["neu_sugar"], TASK["sugar"][0], "-"), ("bitter → MN9", IDS["neu_bitter"], TASK["bitter"][0], "-"),
                           ("JON-CE → aBN1", IDS["neu_JON_CE"], "#1baf7a", "--"), ("JON-F → aBN1", IDS["neu_JON_F"], "#eda100", "--")]:
    d1 = np.sort(np.abs(con[con.Presynaptic_ID.isin(set(ids))]["Excitatory x Connectivity"].values))
    ax.plot(d1, 1 - np.arange(len(d1)) / len(d1), ls, color=col, label=f"{name} (n = {len(d1):,})")
del con
ax.set_xscale("log"); ax.set_xticks([1, 3, 10, 30, 100]); ax.set_xticklabels(["1", "3", "10", "30", "100"]); ax.xaxis.set_minor_formatter(NullFormatter()); ax.xaxis.set_minor_locator(NullLocator())
ax.grid(color=GRID, lw=.5); ax.set_axisbelow(True); ax.set_xlabel("synapses per edge"); ax.set_ylabel("fraction of first-hop edges ≥ x"); panel(ax, "c", "first-hop edge strength by pathway"); ax.legend(loc="center right")
fig.tight_layout(); save(fig, "fig6")

# =============================================================================================== Fig S1
cal = pd.DataFrame([json.loads(l) for l in open("noise_calib_log.txt", encoding="utf-8-sig") if l.strip()]).sort_values("sigma_mV")
fig, axes = plt.subplots(2, 2, figsize=(W, 5.2)); (ax_a, ax_b), (ax_c, ax_d) = axes
ax_a.plot(cal.sigma_mV, cal.frac_active * 100, "-", color=STATE[3.5][0], marker="s", mec="white", mew=.5)
ax_a.set_ylabel("neurons active (%)"); ax_a.set_xlabel("membrane noise σ (mV)"); ax_a.set_xticks([1.5, 2.5, 3.0, 3.5]); ax_a.grid(color=GRID, lw=.5); ax_a.set_axisbelow(True)
ax_a.axvline(3.0, color=STATE[3.0][0], lw=.6, ls="--"); ax_a.axvline(3.5, color=STATE[3.5][0], lw=.6, ls="--"); panel(ax_a, "a", "spontaneous activity vs σ (300 ms, no stimulus)")
ax_a.text(2.98, 26.5, "σ_low", color=STATE[3.0][0], fontsize=6.5, ha="right", va="top"); ax_a.text(3.48, 26.5, "σ_mid", color=STATE[3.5][0], fontsize=6.5, ha="right", va="top"); ax_a.set_ylim(-1, 28)
ax_a2 = ax_a.inset_axes([0.12, 0.45, 0.4, 0.42])
ax_a2.plot(cal.sigma_mV, cal.mean_rate_Hz, "-", color=STATE[0.0][0], marker="o", ms=2.5, mec="white", mew=.4); ax_a2.set_title("mean rate (Hz)", fontsize=6, pad=2); ax_a2.tick_params(labelsize=5.5); ax_a2.set_xticks([1.5, 2.5, 3.5]); ax_a2.grid(color=GRID, lw=.4)
ax_a.text(0.52, 0.72, "at σ = 3.5:\np99 = 77 Hz, max = 317 Hz", ha="left", va="bottom", fontsize=6, color=INK2, transform=ax_a.transAxes)
for nz, src, n in [(0.0, A[A.noise == 0], 3), (3.0, A2[A2.noise == 3.0], 10), (3.5, A2[A2.noise == 3.5], 10)]:
    g = src[(src.method == "mag")].sort_values("k"); col, mk, lab = STATE[nz]; x = np.where(g.k == 0, 100.0, g.frac_edges * 100)
    ax_b.plot(x, g[SD] / g[F], "-", color=col, marker=mk, mec="white", mew=.5, label=f"{lab} ({n} trials)")
logx(ax_b, ticks=(100, 30, 10, 3, 1)); ax_b.set_xticklabels(["100\n(full)", "30", "10", "3", "1"]); ax_b.set_ylabel("trial SD of MN9 rate / full-model mean"); panel(ax_b, "b", "trial variability of the readout (magnitude)"); ax_b.legend(loc="upper left")
s0n = pd.concat([A[A.noise == 0], C[C.task == "sugar"]]); s0n = s0n[s0n.k.isin([2, 5, 10])]; xs = {2: 0, 5: 1, 10: 2}
for j, m in enumerate(["rand", "randm", "dp", "shuf"]):
    g = s0n[s0n.method == m]; col, mk, _ = OP[m]
    ax_c.scatter(g.k.map(xs) + (j - 1.5) * 0.18, g[R], color=col, marker=mk, s=14, ec="white", lw=.4, zorder=3, label={"rand": "uniform", "randm": "weight-prop.", "dp": "rewire", "shuf": "shuffle"}[m])
for k, xi in xs.items():
    r = float(A[(A.noise == 0) & (A.method == "mag") & (A.k == k)][R].iloc[0]); ax_c.hlines(r, xi - 0.42, xi + 0.42, color=OP["mag"][0], lw=1.2, zorder=2)
    ax_c.text(xi + 0.44, r, "mag", fontsize=6, color=OP["mag"][0], va="center")
ax_c.set_xticks([0, 1, 2]); ax_c.set_xticklabels(["k = 2 (32%)", "k = 5 (14%)", "k = 10 (6%)"]); ax_c.set_ylim(-0.05, 1.15); ax_c.grid(color=GRID, lw=.5, axis="y"); ax_c.set_axisbelow(True)
ax_c.set_ylabel("MN9 rate / full model, per seed"); panel(ax_c, "c", "null models, sugar σ = 0, every seed"); ax_c.legend(loc="center", bbox_to_anchor=(0.42, 0.6), handletextpad=0.3)
# (d) all seeds at sigma 3.5 for uniform random vs magnitude, absolute rates
g = A2[(A2.noise == 3.5) & (A2.method == "rand") & (A2.k.isin([1, 3, 10]))]; xs2 = {1: 0, 3: 1, 10: 2}
ax_d.scatter(g.k.map(xs2) + np.random.default_rng(1).uniform(-0.12, 0.12, len(g)), g[R] * g[F], color=OP["rand"][0], marker="v", s=14, ec="white", lw=.4, zorder=3, label="uniform random, per seed")
for k, xi in xs2.items():
    r = float(A2[(A2.noise == 3.5) & (A2.method == "mag") & (A2.k == k)]["sugar100__readout"].iloc[0]); ax_d.hlines(r, xi - 0.42, xi + 0.42, color=OP["mag"][0], lw=1.2, zorder=2); ax_d.text(xi + 0.44, r, "mag", fontsize=6, color=OP["mag"][0], va="center")
ref = float(A2[(A2.noise == 3.5) & (A2.k == 0)][F].iloc[0]); se = float(A2[(A2.noise == 3.5) & (A2.k == 0)][SD].iloc[0]) / np.sqrt(10)
ax_d.axhspan(ref - se, ref + se, color=INK2, alpha=.12, lw=0); ax_d.axhline(ref, c=INK2, lw=.6, ls="--"); ax_d.text(2.45, ref, "full model ± SE", fontsize=6, color=INK2, va="bottom", ha="right")
ax_d.set_xticks([0, 1, 2]); ax_d.set_xticklabels(["k = 1 (50%)", "k = 3 (23%)", "k = 10 (6%)"]); ax_d.grid(color=GRID, lw=.5, axis="y"); ax_d.set_axisbelow(True)
ax_d.set_ylabel("MN9 rate (Hz), 10 trials"); panel(ax_d, "d", "absolute rates, active network (σ = 3.5)"); ax_d.legend(loc="center left", bbox_to_anchor=(0.0, 0.45))
fig.tight_layout(); save(fig, "figS1")

# =============================================================================================== Fig S3 (class-pair survival at k = 10)
BLUES = LinearSegmentedColormap.from_list("blues", ["#f7f9fd", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
d = pd.read_csv("results/anatomy/removed_by_class_pair.csv"); d["kept"] = d["all"] - d["removed"]
order = ["sensory", "sensory_ascending", "ascending", "central", "visual_projection", "visual_centrifugal", "optic", "descending", "motor", "endocrine", "unknown"]
short = {"sensory": "sensory", "sensory_ascending": "sens.-asc.", "ascending": "ascending", "central": "central", "visual_projection": "vis. proj.",
         "visual_centrifugal": "vis. centrif.", "optic": "optic", "descending": "descending", "motor": "motor", "endocrine": "endocrine", "unknown": "unknown"}
x = d[d.k == 10].set_index(["pre_class", "post_class"]); tot = x.kept.sum()
kept_frac = pd.DataFrame(index=order, columns=order, dtype=float); share = kept_frac.copy(); n_all = kept_frac.copy()
for a in order:
    for b in order:
        if (a, b) in x.index:
            r = x.loc[(a, b)]; kept_frac.loc[a, b] = r.kept / r["all"]; share.loc[a, b] = r.kept / tot; n_all.loc[a, b] = r["all"]
fig, axes = plt.subplots(1, 2, figsize=(W, 3.5))
for ax, M, ttl, fmt in [(axes[0], kept_frac * 100, "edges surviving k = 10 (% of each pair)", "{:.0f}"), (axes[1], share * 100, "share of the surviving graph (%)", "{:.1f}")]:
    im = ax.imshow(M.values.astype(float), cmap=BLUES, vmin=0, vmax=25, aspect="auto")
    ax.set_xticks(range(len(order))); ax.set_xticklabels([short[c] for c in order], rotation=45, ha="right", fontsize=6)
    ax.set_yticks(range(len(order))); ax.set_yticklabels([short[c] for c in order], fontsize=6)
    ax.set_xlabel("postsynaptic super-class"); ax.set_ylabel("presynaptic super-class"); panel(ax, "a" if ax is axes[0] else "b", ttl)
    for i, a in enumerate(order):
        for j, b in enumerate(order):
            v = M.loc[a, b]
            if pd.notna(v) and n_all.loc[a, b] >= 200: ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=4.8, color="white" if v > 15 else INK)
    ax.set_xticks(np.arange(-.5, len(order), 1), minor=True); ax.set_yticks(np.arange(-.5, len(order), 1), minor=True); ax.grid(which="minor", color="white", lw=.8); ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=6); cb.set_label("%", fontsize=6.5, color=INK2)
fig.tight_layout(); save(fig, "figS3")
