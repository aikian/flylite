"""Figure: task dependence of function-preserving sparsification (magnitude pruning), silent vs active state."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

A = pd.read_csv("results/phaseA/summary.csv"); B = pd.read_csv("results/phaseB/summary.csv")
A2 = pd.read_csv("results/phaseA2/summary.csv"); D = pd.read_csv("results/phaseD/summary.csv")
# sigma=3.5 curves use the trial-10 runs (sugar: Phase A2, bitter: Phase D); sigma=0 and groom stay trial 3
A = pd.concat([A[A.noise == 0], A2[A2.noise == 3.5]]); A = A[(A.method == "mag") & (A.k > 0)]
b = pd.concat([B[(B.task == "bitter") & (B.noise == 0)], D]); b = b[(b.method == "mag") & (b.k > 0)].copy()
b["SI_full"] = 1 - b["sugar100_bitter100__readout_full"] / b["sugar100__readout_full"]
b["SI"] = 1 - b["sugar100_bitter100__readout"] / b["sugar100__readout"].replace(0, np.nan)
b["norm"] = b["SI"] / b["SI_full"]
g = B[(B.task == "groom") & (B.method == "mag") & (B.k > 0)].copy()
g["spec_full"] = g["jonCE100__readout_full"] - g["jonF100__readout_full"]
g["spec"] = g["jonCE100__readout"] - g["jonF100__readout"]
g["norm"] = g["spec"] / g["spec_full"]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for ax, nz in zip(axes, [0.0, 3.5]):
    a = A[A.noise == nz].sort_values("k")
    ax.plot(a.frac_edges * 100, a["sugar100__readout_ratio"], "o-", c="C0", label="sugar → MN9 (excitatory feedforward)")
    bb = b[b.noise == nz].sort_values("k")
    ax.plot(bb.frac_edges * 100, bb.norm, "s-", c="C3", label="bitter suppression of MN9 (inhibition)")
    gg = g[g.noise == nz].sort_values("k")
    ax.plot(gg.frac_edges * 100, gg.norm, "^-", c="C2", label="JON-CE vs JON-F → aBN1 (pathway specificity)")
    ax.axhline(1, ls="--", c="gray", lw=.8); ax.axhline(0.8, ls=":", c="gray", lw=.8); ax.axhline(0, c="k", lw=.5)
    ax.set_xscale("log"); ax.invert_xaxis(); ax.grid(alpha=.3)
    ax.set_xlabel("edges retained (%)"); ax.set_title(f"{'silent' if nz == 0 else 'spontaneously active'} network (σ = {nz} mV)", fontsize=10)
    for _, r in a.iterrows():
        ax.annotate(f"k={int(r.k)}", (r.frac_edges * 100, r["sugar100__readout_ratio"]), textcoords="offset points", xytext=(3, 4), fontsize=7, color="C0")
axes[0].set_ylabel("function preserved (relative to full model)"); axes[0].set_ylim(-0.9, 2.3)
axes[0].legend(fontsize=8, loc="upper right")
fig.suptitle("Magnitude pruning: what survives depends on the task and on network state", fontsize=11)
fig.tight_layout(); fig.savefig("results/fig5_taskdep_v2.png", dpi=150); print("saved results/fig5_taskdep_v2.png")
