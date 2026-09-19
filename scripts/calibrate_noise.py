"""Calibrate background-noise strength: find sigma giving ~1-5 Hz spontaneous firing in the full model.

Adds an additive white-noise term to the membrane equation (Brian2 `xi`), which is the standard way
to put every neuron near threshold without adding 139k PoissonInput objects.
"""
import sys, os, time, json
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).parent / "repos" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO)); os.chdir(REPO)
import brian2
brian2.prefs.codegen.target = "numpy"
from brian2 import mV, ms, Hz, NeuronGroup, Synapses, SpikeMonitor, Network, defaultclock
import model as M

EQS_NOISE = """
dv/dt = (v_0 - v + g) / t_mbr + sigma * xi * t_mbr**-0.5 : volt (unless refractory)
dg/dt = -g / tau                                          : volt (unless refractory)
rfc                                                       : second
"""

def build(params, path_comp, path_con):
    df_comp = pd.read_csv(path_comp, index_col=0)
    df_con = pd.read_parquet(path_con)
    neu = NeuronGroup(N=len(df_comp), model=EQS_NOISE, method="euler",
                      threshold=params["eq_th"], reset=params["eq_rst"], refractory="rfc",
                      namespace=params, name="neu")
    neu.v = params["v_0"]; neu.g = 0; neu.rfc = params["t_rfc"]
    syn = Synapses(neu, neu, "w : volt", on_pre="g += w", delay=params["t_dly"], name="syn")
    syn.connect(i=df_con["Presynaptic_Index"].values, j=df_con["Postsynaptic_Index"].values)
    syn.w = df_con["Excitatory x Connectivity"].values * params["w_syn"]
    return neu, syn, SpikeMonitor(neu)

if __name__ == "__main__":
    sigmas = [float(s) for s in os.environ.get("SIGMAS", "1.5,2.5,3.5").split(",")]
    t_run = float(os.environ.get("T_MS", "300")) * ms
    res = []
    for s in sigmas:
        params = dict(M.default_params); params["sigma"] = s * mV
        t0 = time.time()
        neu, syn, mon = build(params, "./2023_03_23_completeness_630_final.csv",
                              "./2023_03_23_connectivity_630_final.parquet")
        net = Network(neu, syn, mon); net.run(t_run)
        n = len(neu); counts = np.bincount(mon.i[:], minlength=n)
        rate = counts / float(t_run / ms) * 1000
        row = dict(sigma_mV=s, mean_rate_Hz=float(rate.mean()), frac_active=float((counts > 0).mean()),
                   p50=float(np.percentile(rate, 50)), p90=float(np.percentile(rate, 90)),
                   p99=float(np.percentile(rate, 99)), max=float(rate.max()), wall_s=round(time.time() - t0))
        res.append(row); print(json.dumps(row), flush=True)
        del net, neu, syn, mon
    pd.DataFrame(res).to_csv("./results/noise_calibration.csv", index=False)
