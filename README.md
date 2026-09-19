# FlyLite — function-preserving sparsification of the *Drosophila* connectome

Code, pre-registered design, result tables and figures for

> *How sparse can a fly-brain model be? Connection strength, wiring placement, network state and task jointly determine function-preserving compression of the Drosophila connectome* (manuscript in preparation, 2026).

Everything here runs on a laptop CPU (Intel i3, 8 GB RAM) or a free Google Colab CPU runtime. One whole-brain 1 s trial takes ≈ 65 s (silent network) to ≈ 100–180 s (noisy network) with the Brian2 NumPy backend.

## What is measured

Take the FlyWire v630 connectome (127,400 neurons, 14.7 M weighted edges) as used by the validated leaky integrate-and-fire model of Shiu et al. (2024). Remove edges with one of six *sparsification operators* at the same edge budget `b_k = |{ |w| > k }|`, simulate three experimentally validated circuits in the reduced model, and compare with the full model:

| operator | keeps | destroys |
|---|---|---|
| `mag` | edges with more than *k* synapses | — |
| `rand` | uniform random subset of size `b_k` | magnitude information |
| `randm` | random subset of size `b_k`, sampled ∝ \|w\| without replacement | exact magnitude threshold |
| `dp` | `mag_k` edges with postsynaptic targets permuted (in/out-degree and Dale sign preserved) | wiring position |
| `shuf` | `mag_k` edge positions with magnitudes permuted (sign preserved) | magnitude |
| `act` | top `b_k` edges by \|w\|·(1 + presynaptic rate under the training stimulus) | — (task-aware) |

Tasks: sugar GRNs → MN9 (feeding), + bitter GRNs → suppression of MN9, JON-CE vs JON-F → aBN1 (grooming pathway specificity). Network states: silent (σ = 0) and spontaneously active (membrane noise σ = 3.0 / 3.5 mV). Metrics: behavioural readout ratio, population Pearson r and Jaccard over active neurons, suppression index, pathway specificity.

## Layout

```
run_flylite.py            experiment runner (resumable; one CSV row per task × noise × operator × k × seed)
task_ids.json             FlyWire IDs of stimulus and readout neurons (from Shiu et al. 2024)
scripts/                  analysis and figure scripts (see below)
results/phase*_summary.csv   every simulated condition (Phase A–D)
results/randm_overlap.csv    edge/mass overlap between randm_k and mag_k (Table S2)
results/*_by_k.csv, pathways.csv   anatomy of removed/retained edges (Fig 6)
figures/                  Fig 1–6, S1 as published
colab/                    notebook used for the Colab runs (Phase B/C)
docs/preregistered_design_v1.md   hypotheses H1–H6 and predictions fixed before Phase A (Korean)
```

## Reproduce

1. Clone the teacher model next to this repo and install its dependencies:
   ```
   git clone https://github.com/philshiu/Drosophila_brain_model repos/Drosophila_brain_model
   pip install brian2==2.10.1 numpy pandas pyarrow matplotlib
   ```
   The runner imports `model.py` and reads the v630 connectivity parquet from that repo.
2. Run a grid (this is Phase A; ≈ 9 h on a laptop):
   ```
   python run_flylite.py --tasks sugar --noise 0,3.5 --methods mag,rand,dp,act --ks 1,2,3,5,10,20,31,50 --seeds 0,1,2 --n-run 3 --out results/phaseA
   ```
   Re-running the same command resumes; finished conditions are skipped. `--tasks bitter,groom`, `--methods shuf,act,randm`, `--n-run 10` give Phases B–D (`scripts/run_phaseD.ps1` lists the exact Phase D commands).
3. Analysis and figures:
   ```
   python scripts/analyze_flylite.py results/phaseA          # cliff k*, hypothesis tables, quick figure
   python scripts/analyze_phaseC.py                          # six-operator aggregates + randm/mag overlap
   python scripts/plot_fig1_figS1.py; python scripts/plot_fig2_six.py; python scripts/plot_fig3_fig4.py; python scripts/plot_taskdep.py
   python scripts/check_numbers.py <draft.md>                # every number quoted in the manuscript vs the CSVs
   ```
   The scripts expect `results/<phase>/summary.csv`; copy or symlink the flat CSVs in `results/` accordingly.

## Summary-CSV columns

`task, noise, method, k, seed, n_edges, frac_edges, frac_syn, wall_s`, then per stimulus `<stim>__readout_full`, `__readout`, `__readout_ratio`, `__readout_trial_sd`, `__n_active_full`, `__n_active`, `__jaccard_active`, `__pearson_union`, `__pearson_fullactive`, `__mean_abs_rate_diff`; bitter rows add `suppression_full, suppression`, groom rows add `specificity_full, specificity`. Rows with `k = 0` are the full-model reference for that task/noise.

## Citing

Please cite the manuscript (bioRxiv preprint, DOI to be added; repository https://github.com/aikian/flylite) and Shiu et al. (2024) for the model, Dorkenwald et al. (2024) and Schlegel et al. (2024) for the connectome.

## License

MIT. The teacher model and connectome data keep their own licenses.
