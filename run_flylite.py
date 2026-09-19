"""FlyLite experiment runner - task-preserving compression of the Drosophila connectome (Shiu LIF teacher).

One command runs a full grid:  tasks x noise levels x pruning methods x budgets (k) x seeds x trials,
appends one row per variant to <out>/summary.csv and is resumable (already-finished variants are skipped).

Example (phase A, tonight):
  python run_flylite.py --tasks sugar --noise 0,2.5 --methods mag,rand,dp --ks 1,2,3,5,10,20,31,50 \
                        --seeds 0,1,2 --n-run 3 --out results/phaseA

Pruning methods (all produce an edge list with the SAME number of edges as mag_k, so budgets are matched):
  mag   keep edges with |synapses| > k                        (weak-synapse pruning)
  rand  random subset of edges                                (naive null)
  dp    mag_k edges, then postsynaptic targets permuted       (degree-preserving null: exact in/out degree kept)
  shuf  mag_k edges, weight magnitudes permuted among them    (position-preserving, magnitude-destroying null)
  act   top edges by |w| * (1 + presyn rate in full model)    (cheap task-aware saliency; uses TRAIN stimulus only)

Tasks (readouts from Shiu et al. 2024, all experimentally validated):
  sugar   sugar GRNs 100 Hz                      -> MN9 rate
  bitter  sugar 100 Hz + bitter 100 Hz           -> MN9 suppression index vs sugar alone
  water   water GRNs 140 Hz                      -> MN9 rate
  groom   JON-CE 100 Hz  (and JON-F 100 Hz)      -> aBN1 rate (CE strong / F weak = specificity)
"""
import argparse, json, os, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE / "repos" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))
import brian2
brian2.prefs.codegen.target = "numpy"
from brian2 import mV, ms, Hz, NeuronGroup, Synapses, SpikeMonitor, PoissonInput, Network
import model as M

IDS = json.load(open(HERE / "task_ids.json"))
PATH_COMP = REPO / "2023_03_23_completeness_630_final.csv"
PATH_CON = REPO / "2023_03_23_connectivity_630_final.parquet"

EQS_NOISE = """
dv/dt = (v_0 - v + g) / t_mbr + sigma * xi * t_mbr**-0.5 : volt (unless refractory)
dg/dt = -g / tau                                          : volt (unless refractory)
rfc                                                       : second
"""

# task -> list of (stim_sets) ; each stim set = dict(exc=[ids], r=Hz, exc2=[ids], r2=Hz, readout=id, name=str)
TASKS = {
    "sugar":  [dict(name="sugar100", exc=IDS["neu_sugar"], r=100, exc2=[], r2=0, readout=IDS["id_mn9"])],
    "bitter": [dict(name="sugar100", exc=IDS["neu_sugar"], r=100, exc2=[], r2=0, readout=IDS["id_mn9"]),
               dict(name="sugar100_bitter100", exc=IDS["neu_sugar"], r=100, exc2=IDS["neu_bitter"], r2=100, readout=IDS["id_mn9"])],
    "water":  [dict(name="water140", exc=IDS["neu_water"], r=140, exc2=[], r2=0, readout=IDS["id_mn9"])],
    "groom":  [dict(name="jonCE100", exc=IDS["neu_JON_CE"], r=100, exc2=[], r2=0, readout=IDS["id_aBN1"]),
               dict(name="jonF100", exc=IDS["neu_JON_F"], r=100, exc2=[], r2=0, readout=IDS["id_aBN1"])],
}


# ----------------------------------------------------------------------------- graph variants
def make_variant(con, method, k, seed, w_abs, act_rate_pre=None):
    """Return the edge DataFrame for (method, k, seed). All methods match mag_k's edge count."""
    n_full = len(con)
    keep_mag = w_abs > k
    n_keep = int(keep_mag.sum())
    rng = np.random.default_rng(1000 * seed + k)
    if method == "mag":
        return con[keep_mag]
    if method == "rand":
        idx = np.sort(rng.choice(n_full, size=n_keep, replace=False))
        return con.iloc[idx]
    if method == "randm":
        # synapse-mass-matched random: sample edges with probability ∝ |w| (without replacement),
        # so the retained synapse mass approximates mag_k's instead of the edge count only.
        p = w_abs / w_abs.sum()
        idx = np.sort(rng.choice(n_full, size=n_keep, replace=False, p=p))
        return con.iloc[idx]
    if method == "dp":
        d = con[keep_mag].copy()
        # permuting the postsynaptic column keeps every neuron's out-degree AND in-degree exactly;
        # weights stay with the presynaptic row, so Dale's-law sign is preserved.
        perm = rng.permutation(len(d))
        d["Postsynaptic_Index"] = d["Postsynaptic_Index"].values[perm]
        d["Postsynaptic_ID"] = d["Postsynaptic_ID"].values[perm]
        return d
    if method == "shuf":
        d = con[keep_mag].copy()
        mag = np.abs(d["Excitatory x Connectivity"].values)
        sign = np.sign(d["Excitatory x Connectivity"].values)
        d["Excitatory x Connectivity"] = sign * mag[rng.permutation(len(d))]
        return d
    if method == "act":
        assert act_rate_pre is not None, "act needs presynaptic rates from the full model"
        score = w_abs * (1.0 + act_rate_pre)
        idx = np.argpartition(-score, n_keep - 1)[:n_keep]
        return con.iloc[np.sort(idx)]
    raise ValueError(method)


# ----------------------------------------------------------------------------- simulation
def build_network(df_comp, df_con, params, noise_mV):
    params = dict(params)
    if noise_mV > 0:
        params["sigma"] = noise_mV * mV
        neu = NeuronGroup(N=len(df_comp), model=EQS_NOISE, method="euler", threshold=params["eq_th"],
                          reset=params["eq_rst"], refractory="rfc", namespace=params, name="neu")
    else:
        neu = NeuronGroup(N=len(df_comp), model=params["eqs"], method="linear", threshold=params["eq_th"],
                          reset=params["eq_rst"], refractory="rfc", namespace=params, name="neu")
    neu.v = params["v_0"]; neu.g = 0; neu.rfc = params["t_rfc"]
    syn = Synapses(neu, neu, "w : volt", on_pre="g += w", delay=params["t_dly"], name="syn")
    syn.connect(i=df_con["Presynaptic_Index"].values, j=df_con["Postsynaptic_Index"].values)
    syn.w = df_con["Excitatory x Connectivity"].values * params["w_syn"]
    return neu, syn


def run_stim(neu, syn, stim, flyid2i, params, n_run, t_run):
    """Build Poisson drives for one stimulus set, run n_run trials from the same stored state, return rates."""
    p = dict(params); p["r_poi"] = stim["r"] * Hz; p["r_poi2"] = stim["r2"] * Hz
    exc = [flyid2i[i] for i in stim["exc"] if i in flyid2i]
    exc2 = [flyid2i[i] for i in stim["exc2"] if i in flyid2i]
    pois, neu = M.poi(neu, exc, exc2, p)
    mon = SpikeMonitor(neu)
    net = Network(neu, syn, mon, *pois)
    net.store()
    n = len(neu); counts = np.zeros((n_run, n))
    for t in range(n_run):
        net.restore()
        net.run(t_run)
        counts[t] = np.bincount(mon.i[:], minlength=n)
    # undo poi's side effect (refractory=0 on stimulated neurons) so the next stimulus set starts clean
    for i in exc + exc2:
        neu[i].rfc = params["t_rfc"]
    rates = counts / float(t_run / ms) * 1000.0  # Hz, shape (n_run, n)
    return rates, np.array(exc + exc2)


# ----------------------------------------------------------------------------- metrics
def compare(rates_full, rates, stim_idx, readout_i):
    """rates_*: (n_run, n). Returns dict of preservation metrics (stimulated neurons excluded)."""
    rf, rp = rates_full.mean(0), rates.mean(0)
    mask = np.ones(len(rf), bool); mask[stim_idx] = False
    act_f, act_p = (rf > 0) & mask, (rp > 0) & mask
    union = act_f | act_p
    out = dict(
        readout_full=float(rf[readout_i]), readout=float(rp[readout_i]),
        readout_ratio=float(rp[readout_i] / rf[readout_i]) if rf[readout_i] > 0 else np.nan,
        readout_trial_sd=float(rates[:, readout_i].std()),
        n_active_full=int(act_f.sum()), n_active=int(act_p.sum()),
        jaccard_active=float((act_f & act_p).sum() / max(union.sum(), 1)),
        pearson_union=float(np.corrcoef(rf[union], rp[union])[0, 1]) if union.sum() > 2 else np.nan,
        pearson_fullactive=float(np.corrcoef(rf[act_f], rp[act_f])[0, 1]) if act_f.sum() > 2 else np.nan,
        mean_abs_rate_diff=float(np.abs(rf[union] - rp[union]).mean()) if union.sum() else np.nan,
    )
    return out


def append_row(summary_p, row):
    """Append one row, keeping a consistent column order across rows with different metric sets."""
    new = pd.DataFrame([row])
    if summary_p.exists():
        old = pd.read_csv(summary_p)
        new = pd.concat([old, new], ignore_index=True, sort=False)
    new.to_csv(summary_p, index=False)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="sugar")
    ap.add_argument("--noise", default="0")            # sigma in mV, comma list; 0 = original Shiu model
    ap.add_argument("--methods", default="mag,rand,dp")
    ap.add_argument("--ks", default="1,2,3,5,10,20,31,50")
    ap.add_argument("--seeds", default="0,1,2")        # used by rand/dp/shuf only
    ap.add_argument("--n-run", type=int, default=3)
    ap.add_argument("--t-ms", type=float, default=1000)
    ap.add_argument("--out", default="results/flylite")
    ap.add_argument("--save-rates", action="store_true", help="store per-neuron mean rates (npz) per variant")
    ap.add_argument("--connectome", default="630", choices=["630", "783"], help="FlyWire materialisation (Phase F robustness: 783)")
    ap.add_argument("--w-syn-scale", type=float, default=1.0, help="multiply the synaptic gain w_syn (Phase F robustness: 0.8 / 1.2)")
    a = ap.parse_args()

    out = HERE / a.out; out.mkdir(parents=True, exist_ok=True)
    summary_p = out / "summary.csv"
    done = set()
    if summary_p.exists():
        s = pd.read_csv(summary_p)
        done = set(zip(s.task, s.noise, s.method, s.k, s.seed))

    params = dict(M.default_params)
    params["w_syn"] = params["w_syn"] * a.w_syn_scale
    global PATH_COMP, PATH_CON
    if a.connectome == "783":
        PATH_COMP, PATH_CON = REPO / "Completeness_783.csv", REPO / "Connectivity_783.parquet"
    print(f">>> connectome {a.connectome}  w_syn x{a.w_syn_scale}", flush=True)
    t_run = a.t_ms * ms
    df_comp = pd.read_csv(PATH_COMP, index_col=0)
    flyid2i = {j: i for i, j in enumerate(df_comp.index)}
    con = pd.read_parquet(PATH_CON)
    w_abs = np.abs(con["Excitatory x Connectivity"].values)
    n_full, syn_full = len(con), float(w_abs.sum())

    tasks = a.tasks.split(","); noises = [float(x) for x in a.noise.split(",")]
    methods = a.methods.split(","); ks = [int(x) for x in a.ks.split(",")]
    seeds = [int(x) for x in a.seeds.split(",")]

    for task in tasks:
        stims = TASKS[task]
        for noise in noises:
            # ---- full model reference for this task/noise (k=0)
            ref_key = (task, noise, "mag", 0, 0)
            ref_file = out / f"ref_{task}_n{noise}.npz"
            if ref_file.exists():
                z = np.load(ref_file, allow_pickle=True)
                ref = {s["name"]: (z[s["name"]], z[s["name"] + "_stim"]) for s in stims}
            else:
                print(f">>> reference  task={task} noise={noise}", flush=True)
                t0 = time.time()
                ref = {}
                for s in stims:
                    # Brian2 refuses to re-add an already-simulated NeuronGroup to a new Network,
                    # so the graph is rebuilt for every stimulus set (~30 s each).
                    neu, syn = build_network(df_comp, con, params, noise)
                    rates, stim_idx = run_stim(neu, syn, s, flyid2i, params, a.n_run, t_run)
                    ref[s["name"]] = (rates, stim_idx)
                    del neu, syn
                np.savez_compressed(ref_file, **{k: v[0] for k, v in ref.items()},
                                    **{k + "_stim": v[1] for k, v in ref.items()})
                row = dict(task=task, noise=noise, method="mag", k=0, seed=0, n_edges=n_full, frac_edges=1.0,
                           frac_syn=1.0, wall_s=round(time.time() - t0))
                for s in stims:
                    r, si = ref[s["name"]]
                    m = compare(r, r, si, flyid2i[s["readout"]])
                    row.update({f"{s['name']}__{kk}": vv for kk, vv in m.items()})
                append_row(summary_p, row)
                print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
            # presynaptic rates from the TRAIN stimulus (first stim of the task) for the act method
            act_rate_pre = None
            if "act" in methods:
                r_train = ref[stims[0]["name"]][0].mean(0)
                act_rate_pre = r_train[con["Presynaptic_Index"].values]

            # ---- variants
            for k in ks:
                for method in methods:
                    for seed in (seeds if method in ("rand", "randm", "dp", "shuf") else [0]):
                        key = (task, noise, method, k, seed)
                        if key in done:
                            continue
                        t0 = time.time()
                        dfc = make_variant(con, method, k, seed, w_abs, act_rate_pre)
                        row = dict(task=task, noise=noise, method=method, k=k, seed=seed, n_edges=len(dfc),
                                   frac_edges=len(dfc) / n_full,
                                   frac_syn=float(np.abs(dfc["Excitatory x Connectivity"]).sum() / syn_full))
                        rates_store = {}
                        for s in stims:
                            neu, syn = build_network(df_comp, dfc, params, noise)  # rebuilt per stimulus (see above)
                            rates, stim_idx = run_stim(neu, syn, s, flyid2i, params, a.n_run, t_run)
                            del neu, syn
                            m = compare(ref[s["name"]][0], rates, stim_idx, flyid2i[s["readout"]])
                            row.update({f"{s['name']}__{kk}": vv for kk, vv in m.items()})
                            rates_store[s["name"]] = rates.mean(0)
                        if task == "bitter":
                            si_full = 1 - row["sugar100_bitter100__readout_full"] / max(row["sugar100__readout_full"], 1e-9)
                            si = 1 - row["sugar100_bitter100__readout"] / max(row["sugar100__readout"], 1e-9)
                            row["suppression_full"], row["suppression"] = float(si_full), float(si)
                        if task == "groom":
                            row["specificity_full"] = row["jonCE100__readout_full"] - row["jonF100__readout_full"]
                            row["specificity"] = row["jonCE100__readout"] - row["jonF100__readout"]
                        row["wall_s"] = round(time.time() - t0)
                        if a.save_rates:
                            np.savez_compressed(out / f"rates_{task}_n{noise}_{method}_k{k}_s{seed}.npz", **rates_store)
                        append_row(summary_p, row)
                        done.add(key)
                        brief = {kk: row[kk] for kk in ("task", "noise", "method", "k", "seed", "frac_edges", "wall_s")}
                        brief.update({kk: round(row[kk], 3) for kk in row if kk.endswith("readout_ratio") or kk.endswith("pearson_union")})
                        print(json.dumps(brief), flush=True)
    print("=== done ===", flush=True)


if __name__ == "__main__":
    main()
