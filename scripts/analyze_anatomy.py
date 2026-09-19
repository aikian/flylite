"""What magnitude pruning removes: sign, cell class, and the sugar/bitter/grooming pathways.

Uses only the v630 edge table + FlyWire annotations (no simulation). Outputs results/anatomy/*.csv and a figure.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("results/anatomy"); OUT.mkdir(parents=True, exist_ok=True)
con = pd.read_parquet("repos/Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet")
w = con["Excitatory x Connectivity"].values; aw = np.abs(w); pre = con["Presynaptic_ID"].values; post = con["Postsynaptic_ID"].values
ann = pd.read_csv("repos/flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv", sep="\t", low_memory=False)
cls = ann.set_index("root_id")["super_class"].to_dict()
ctype = ann.set_index("root_id")["cell_type"].to_dict()
IDS = json.load(open("task_ids.json"))
KS = [1, 2, 3, 5, 10, 20, 31, 50]

# ---- 1. sign of what is removed
rows = []
for k in KS:
    rem = aw <= k
    rows.append(dict(k=k, frac_edges_removed=rem.mean(), frac_mass_removed=aw[rem].sum() / aw.sum(),
                     inh_share_removed=(w[rem] < 0).mean(), inh_share_kept=(w[~rem] < 0).mean(),
                     inh_mass_share_removed=aw[rem & (w < 0)].sum() / aw[rem].sum(),
                     inh_mass_share_kept=aw[~rem & (w < 0)].sum() / aw[~rem].sum()))
S = pd.DataFrame(rows); S.to_csv(OUT / "sign_by_k.csv", index=False)
print("=== sign composition (all edges: inh share = %.3f by count, %.3f by mass) ===" % ((w < 0).mean(), aw[w < 0].sum() / aw.sum()))
print(S.round(3).to_string(index=False))

# ---- 2. per-neuron inhibitory input fraction: does pruning shift E/I balance of individual neurons?
post_idx = con["Postsynaptic_Index"].values; n = post_idx.max() + 1
def ei(mask):
    e = np.bincount(post_idx[mask & (w > 0)], weights=aw[mask & (w > 0)], minlength=n)
    i = np.bincount(post_idx[mask & (w < 0)], weights=aw[mask & (w < 0)], minlength=n)
    return e, i
e0, i0 = ei(np.ones(len(w), bool)); tot0 = e0 + i0; has = tot0 > 0
rows = []
for k in KS:
    e, i = ei(aw > k); tot = e + i; ok = has & (tot > 0)
    ifrac0, ifrac = i0[ok] / tot0[ok], i[ok] / tot[ok]
    rows.append(dict(k=k, n_neurons_with_input=int(ok.sum()), median_inh_frac_full=np.median(ifrac0), median_inh_frac_pruned=np.median(ifrac),
                     frac_neurons_lost_all_inhibition=float(((i0[ok] > 0) & (i[ok] == 0)).mean()),
                     frac_neurons_lost_all_excitation=float(((e0[ok] > 0) & (e[ok] == 0)).mean())))
EI = pd.DataFrame(rows); EI.to_csv(OUT / "ei_balance_by_k.csv", index=False)
print("\n=== per-neuron E/I balance after pruning ===\n", EI.round(3).to_string(index=False))

# ---- 3. super-class of removed edges (by presynaptic class)
classes = sorted(set(cls.values()) | {"unknown"}); cid = {c: i for i, c in enumerate(classes)}; nc = len(classes)
pc = np.array([cid[cls.get(x, "unknown")] for x in pre], dtype=np.int32); qc = np.array([cid[cls.get(x, "unknown")] for x in post], dtype=np.int32)
pair = pc * nc + qc; all_cnt = np.bincount(pair, minlength=nc * nc)
rows = []
for k in [2, 5, 10]:
    rem_cnt = np.bincount(pair[aw <= k], minlength=nc * nc)
    for p in range(nc * nc):
        if all_cnt[p] > 0:
            rows.append(dict(k=k, pre_class=classes[p // nc], post_class=classes[p % nc], all=int(all_cnt[p]), removed=int(rem_cnt[p]), frac_removed=rem_cnt[p] / all_cnt[p]))
C = pd.DataFrame(rows); C.to_csv(OUT / "removed_by_class_pair.csv", index=False)
top = C[(C.k == 5) & (C["all"] > 50000)].sort_values("frac_removed", ascending=False)
print("\n=== k=5: fraction of edges removed by (pre class -> post class), pairs with >50k edges ===\n", top.head(15).round(3).to_string(index=False))

# ---- 4. the two grooming pathways: synapse-count distribution of direct and 2-hop edges from JON-CE vs JON-F to aBN1
def pathway_stats(src_ids, target, name):
    src = set(src_ids); d1 = con[con.Presynaptic_ID.isin(src)]
    direct = d1[d1.Postsynaptic_ID == target]
    hop1 = set(d1.Postsynaptic_ID); d2 = con[con.Presynaptic_ID.isin(hop1) & (con.Postsynaptic_ID == target)]
    out = dict(pathway=name, n_src=len(src), direct_edges=len(direct), direct_syn=int(np.abs(direct["Excitatory x Connectivity"]).sum()),
               first_hop_edges=len(d1), first_hop_median_syn=float(np.abs(d1["Excitatory x Connectivity"]).median()),
               first_hop_frac_le2=float((np.abs(d1["Excitatory x Connectivity"]) <= 2).mean()),
               first_hop_frac_le5=float((np.abs(d1["Excitatory x Connectivity"]) <= 5).mean()),
               n_intermediates=len(hop1), inter_to_target_edges=len(d2),
               inter_to_target_exc_syn=int(d2.loc[d2["Excitatory x Connectivity"] > 0, "Excitatory x Connectivity"].sum()),
               inter_to_target_inh_syn=int(-d2.loc[d2["Excitatory x Connectivity"] < 0, "Excitatory x Connectivity"].sum()),
               inter_to_target_frac_le5=float((np.abs(d2["Excitatory x Connectivity"]) <= 5).mean()))
    return out
P = pd.DataFrame([pathway_stats(IDS["neu_JON_CE"], IDS["id_aBN1"], "JON-CE -> aBN1"),
                  pathway_stats(IDS["neu_JON_F"], IDS["id_aBN1"], "JON-F -> aBN1"),
                  pathway_stats(IDS["neu_sugar"], IDS["id_mn9"], "sugar -> MN9"),
                  pathway_stats(IDS["neu_bitter"], IDS["id_mn9"], "bitter -> MN9")])
P.to_csv(OUT / "pathways.csv", index=False)
print("\n=== pathway anatomy (1st hop = edges out of the sensory set; 2nd hop = intermediates -> readout) ===\n", P.round(3).T.to_string())

# ---- figure
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
ax[0].plot(S.k, S.inh_mass_share_removed, "o-", label="removed edges"); ax[0].plot(S.k, S.inh_mass_share_kept, "s-", label="kept edges")
ax[0].axhline(aw[w < 0].sum() / aw.sum(), ls="--", c="gray", label="whole graph"); ax[0].set_xscale("log"); ax[0].set_xlabel("k"); ax[0].set_ylabel("inhibitory share of synapse mass"); ax[0].legend(fontsize=8); ax[0].set_title("Sign of pruned synapses", fontsize=10)
ax[1].plot(EI.k, EI.frac_neurons_lost_all_inhibition, "o-", c="C3", label="lost all inhibitory input"); ax[1].plot(EI.k, EI.frac_neurons_lost_all_excitation, "s-", c="C0", label="lost all excitatory input")
ax[1].set_xscale("log"); ax[1].set_xlabel("k"); ax[1].set_ylabel("fraction of neurons"); ax[1].legend(fontsize=8); ax[1].set_title("Neurons losing one input sign entirely", fontsize=10)
for name, c in [("JON-CE -> aBN1", "C2"), ("JON-F -> aBN1", "C1"), ("sugar -> MN9", "C0"), ("bitter -> MN9", "C3")]:
    ids = {"JON-CE -> aBN1": IDS["neu_JON_CE"], "JON-F -> aBN1": IDS["neu_JON_F"], "sugar -> MN9": IDS["neu_sugar"], "bitter -> MN9": IDS["neu_bitter"]}[name]
    d1 = np.abs(con[con.Presynaptic_ID.isin(set(ids))]["Excitatory x Connectivity"].values)
    xs = np.sort(d1); ax[2].plot(xs, 1 - np.arange(len(xs)) / len(xs), c=c, label=f"{name} (1st hop, n={len(xs)})")
ax[2].set_xscale("log"); ax[2].set_xlabel("synapses per edge"); ax[2].set_ylabel("fraction of edges ≥ x"); ax[2].legend(fontsize=7); ax[2].set_title("First-hop edge strength by pathway", fontsize=10)
for a in ax: a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(OUT / "fig_anatomy.png", dpi=150); print("\nfigure ->", OUT / "fig_anatomy.png")
