"""Fig 6 supplement: which super-class pairs survive weak-synapse pruning at k = 10 (the sugar cliff).
Input: results/anatomy/removed_by_class_pair.csv (analyze_anatomy.py)."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

INK, INK2 = "#0b0b0b", "#52514e"
BLUES = LinearSegmentedColormap.from_list("blues", ["#f7f9fd", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
plt.rcParams.update({"font.size": 9, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK})
d = pd.read_csv("results/anatomy/removed_by_class_pair.csv"); d["kept"] = d["all"] - d["removed"]
order = ["sensory", "sensory_ascending", "ascending", "central", "visual_projection", "visual_centrifugal", "optic", "descending", "motor", "endocrine", "unknown"]
short = {"sensory": "sensory", "sensory_ascending": "sens.-asc.", "ascending": "ascending", "central": "central", "visual_projection": "vis. proj.",
         "visual_centrifugal": "vis. centrif.", "optic": "optic", "descending": "descending", "motor": "motor", "endocrine": "endocrine", "unknown": "unknown"}
K = 10
x = d[d.k == K].set_index(["pre_class", "post_class"])
kept_frac = pd.DataFrame(index=order, columns=order, dtype=float); share = kept_frac.copy(); n_all = kept_frac.copy()
tot_kept = x.kept.sum()
for a in order:
    for b in order:
        if (a, b) in x.index:
            r = x.loc[(a, b)]; kept_frac.loc[a, b] = r.kept / r["all"]; share.loc[a, b] = r.kept / tot_kept; n_all.loc[a, b] = r["all"]

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.6))
for ax, M, ttl, fmt, vmax in [(axes[0], kept_frac * 100, f"a  Edges surviving k = {K} (% of each pair)", "{:.0f}", 25),
                              (axes[1], share * 100, f"b  Composition of the surviving graph (% of all kept edges)", "{:.1f}", 25)]:
    im = ax.imshow(M.values.astype(float), cmap=BLUES, vmin=0, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(order))); ax.set_xticklabels([short[c] for c in order], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(order))); ax.set_yticklabels([short[c] for c in order], fontsize=8)
    ax.set_xlabel("postsynaptic super-class"); ax.set_ylabel("presynaptic super-class"); ax.set_title(ttl, loc="left", fontsize=10, fontweight="bold")
    for i, a in enumerate(order):
        for j, b in enumerate(order):
            v = M.loc[a, b]
            if pd.notna(v) and n_all.loc[a, b] >= 200:
                ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=6.5, color="white" if v > vmax * 0.6 else INK)
    ax.set_xticks(np.arange(-.5, len(order), 1), minor=True); ax.set_yticks(np.arange(-.5, len(order), 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.2); ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02); cb.set_label("%", color=INK2)
fig.suptitle(f"What remains at the cliff (magnitude pruning, k = {K}, 6.1% of edges): edges onto motor and descending neurons are retained 2–3× more often than central→central", fontsize=10, x=0.02, ha="left", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig("results/fig6b_classpairs.png", dpi=170); print("saved results/fig6b_classpairs.png")
# numbers for the text
print("kept pct: central->central %.1f, central->motor %.1f, central->descending %.1f, ascending->motor %.1f, descending->motor %.1f, sensory->central %.1f" % (
    kept_frac.loc["central", "central"] * 100, kept_frac.loc["central", "motor"] * 100, kept_frac.loc["central", "descending"] * 100,
    kept_frac.loc["ascending", "motor"] * 100, kept_frac.loc["descending", "motor"] * 100, kept_frac.loc["sensory", "central"] * 100))
print("share pct: central->central %.1f, optic->optic %.1f" % (share.loc["central", "central"] * 100, share.loc["optic", "optic"] * 100))
