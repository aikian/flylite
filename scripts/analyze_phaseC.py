"""Phase C analysis: sugar shuf/randm (sigma=0) + groom/bitter shuf/act; randm-vs-mag edge overlap from the real connectivity.

usage: python analyze_phaseC.py            (writes results/phaseC/agg_*.csv, randm_overlap.csv)
"""
import numpy as np, pandas as pd
from pathlib import Path
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 300)
R = Path("results")
A = pd.read_csv(R / "phaseA/summary.csv"); B = pd.read_csv(R / "phaseB/summary.csv"); C = pd.read_csv(R / "phaseC/summary.csv")

def agg(df, stim):
    r, c, j, n = [f"{stim}__{x}" for x in ("readout_ratio", "pearson_union", "jaccard_active", "n_active")]
    g = df.groupby(["task", "noise", "method", "k"]).agg(
        frac_edges=("frac_edges", "first"), frac_syn=("frac_syn", "mean"),
        ratio=(r, "mean"), ratio_min=(r, "min"), ratio_max=(r, "max"),
        corr=(c, "mean"), corr_min=(c, "min"), corr_max=(c, "max"),
        jacc=(j, "mean"), n_active=(n, "mean"), n_active_min=(n, "min"), n_active_max=(n, "max"), n=(r, "size")).reset_index()
    return g

# ---- sugar sigma=0: all six operators (A: mag/rand/dp/act, C: shuf/randm)
S = pd.concat([A[(A.task == "sugar") & (A.noise == 0)], C[(C.task == "sugar")]])
gs = agg(S[S.k > 0], "sugar100")
print("=== sugar σ=0, six operators: readout ratio mean [min–max] / corr / n_active ===")
print(gs[["method", "k", "frac_edges", "frac_syn", "ratio", "ratio_min", "ratio_max", "corr", "corr_min", "corr_max", "jacc", "n_active", "n"]].round(3).to_string(index=False))
gs.to_csv(R / "phaseC/agg_sugar_six.csv", index=False)

# ---- groom: shuf/act both sigma (C) vs mag/dp (B)
G = pd.concat([B[B.task == "groom"], C[C.task == "groom"]])
G = G[G.k > 0].copy()
G["spec"] = G["jonCE100__readout"] - G["jonF100__readout"]; G["spec_full"] = G["jonCE100__readout_full"] - G["jonF100__readout_full"]
gg = G.groupby(["noise", "method", "k"]).agg(ce=("jonCE100__readout_ratio", "mean"), ce_min=("jonCE100__readout_ratio", "min"), ce_max=("jonCE100__readout_ratio", "max"),
    f_hz=("jonF100__readout", "mean"), f_min=("jonF100__readout", "min"), f_max=("jonF100__readout", "max"),
    spec=("spec", "mean"), spec_min=("spec", "min"), spec_max=("spec", "max"), spec_full=("spec_full", "first"),
    corr=("jonCE100__pearson_union", "mean"), corr_min=("jonCE100__pearson_union", "min"), corr_max=("jonCE100__pearson_union", "max"), n=("spec", "size")).reset_index()
print("\n=== groom: CE ratio, F Hz, specificity (full in spec_full) ===")
print(gg.round(2).to_string(index=False)); gg.to_csv(R / "phaseC/agg_groom.csv", index=False)

# ---- bitter: shuf/act (C) vs mag/dp (B)
Bt = pd.concat([B[B.task == "bitter"], C[C.task == "bitter"]]); Bt = Bt[Bt.k > 0].copy()
Bt["SI_full"] = 1 - Bt["sugar100_bitter100__readout_full"] / Bt["sugar100__readout_full"]
Bt["SI"] = 1 - Bt["sugar100_bitter100__readout"] / Bt["sugar100__readout"].replace(0, np.nan)
gb = Bt.groupby(["noise", "method", "k"]).agg(sugar=("sugar100__readout_ratio", "mean"), sugar_min=("sugar100__readout_ratio", "min"), sugar_max=("sugar100__readout_ratio", "max"),
    sb_hz=("sugar100_bitter100__readout", "mean"), SI=("SI", "mean"), SI_min=("SI", "min"), SI_max=("SI", "max"), SI_full=("SI_full", "first"),
    corr=("sugar100__pearson_union", "mean"), n_active=("sugar100__n_active", "mean"), n=("SI", "size")).reset_index()
print("\n=== bitter: sugar ratio, sugar+bitter Hz, SI ===")
print(gb.round(2).to_string(index=False)); gb.to_csv(R / "phaseC/agg_bitter.csv", index=False)

# ---- randm vs mag: reproduce the exact sampled edge sets and measure overlap with mag_k (same rng as run_flylite.make_variant)
con = pd.read_parquet("repos/Drosophila_brain_model/2023_03_23_connectivity_630_final.parquet", columns=["Excitatory x Connectivity"])
w = np.abs(con["Excitatory x Connectivity"].values.astype(np.float64)); del con
W = w.sum(); n_full = len(w); p = w / W
rows = []
for k in [1, 2, 3, 5, 10]:
    keep_mag = w > k; n_keep = int(keep_mag.sum()); mass_mag = w[keep_mag].sum() / W
    for seed in [0, 1, 2]:
        rng = np.random.default_rng(1000 * seed + k)
        idx = rng.choice(n_full, size=n_keep, replace=False, p=p)
        sel = np.zeros(n_full, bool); sel[idx] = True
        inter = sel & keep_mag
        rows.append(dict(k=k, seed=seed, n_keep=n_keep, frac_edges=n_keep / n_full, mass_mag=mass_mag, mass_randm=w[sel].sum() / W,
                         overlap_frac_of_mag=inter.sum() / n_keep,               # share of mag_k edges that randm also keeps
                         mass_overlap_frac_of_mag=w[inter].sum() / w[keep_mag].sum(),  # share of mag_k's synapse mass that randm keeps
                         weak_edges_in_randm=(sel & ~keep_mag).sum() / n_keep,    # share of randm edges that are <= k (weak)
                         strong_kept_ge31=(sel & (w > 31)).sum() / max((w > 31).sum(), 1),  # share of >31-syn edges retained
                         strong_kept_gt10=(sel & (w > 10)).sum() / max((w > 10).sum(), 1)))
ov = pd.DataFrame(rows); print("\n=== randm_k vs mag_k edge/mass overlap ===")
print(ov.groupby("k").mean(numeric_only=True).drop(columns="seed").round(3).to_string()); ov.to_csv(R / "phaseC/randm_overlap.csv", index=False)
