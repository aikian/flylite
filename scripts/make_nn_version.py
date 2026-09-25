"""Derive the Neural Networks (Elsevier) submission version from the preprint manuscript.

Differences from the preprint: Highlights (<= 85 characters each), no Author Summary, an Introduction paragraph and a
Discussion paragraph connecting the work to the artificial-network pruning literature, Elsevier declarations
(CRediT / competing interest / funding / data availability), APA author-year citations and reference list.
Input  : FlyLite_manuscript_EN_v1.md      Output: FlyLite_manuscript_EN_NeuralNetworks_v1.md
"""
import re

SRC, OUT = "FlyLite_manuscript_EN_v1.md", "FlyLite_manuscript_EN_NeuralNetworks_v1.md"
DOI = "10.64898/2026.09.19.752860"
s = open(SRC, encoding="utf-8").read()

HIGHLIGHTS = [
    "Weak-synapse pruning keeps 79% of a validated fly behaviour with 6% of edges",
    "Random, rewired and weight-shuffled controls at the same budget abolish output",
    "Function needs wiring placement and strength together, not synaptic mass",
    "The cliff is task-dependent: grooming pathway specificity fails first",
    "In an active network inhibition is lost first and the readout over-excites",
]
for h in HIGHLIGHTS:
    assert len(h) <= 85, (len(h), h)

ABSTRACT = """Whole-brain connectomes are used as wiring diagrams for spiking simulations and as priors for artificial networks, usually after an ad hoc synapse-count threshold whose functional cost has never been measured. We define *function-preserving sparsification*—removing edges under a fixed budget while preserving validated behaviour and population responses—and study it in the leaky integrate-and-fire whole-brain model of Shiu et al. (2024). Six operators (weak-synapse pruning, uniform and weight-proportional random removal, degree-preserving rewiring, weight shuffling, a task-aware criterion) were compared at identical edge budgets across three validated circuits, silent and active network states, and multiple seeds. Weak-synapse pruning preserves 79% of feeding output with 6% of edges (cliff at k\\* ≈ 9 synapses), whereas random, degree-preserving and weight-shuffled controls abolish output and weight-proportional sampling survives only while it retains the strong-edge set: function resides in the conjunction of placement and strength, not in degree statistics or synaptic mass. The cliff is task-dependent—grooming specificity collapses below k = 2 through disinhibition—and state-dependent: in the active state output over-excites and bitter suppression is lost from k = 5. A task-aware criterion preserves its training stimulus at 0.4% of edges but loses held-out inhibition first: what must be kept depends on task and state."""

INTRO_ANN = """**A parallel problem in artificial networks.** Removing parameters from a trained artificial network is an old problem: second-derivative saliency (LeCun et al., 1989), magnitude pruning with retraining (Han et al., 2015), and the finding that sparse subnetworks trained from their original initialisation can match the dense network (Frankle & Carbin, 2019). A meta-analysis of 81 papers identified the central weakness of that literature as the absence of standardised benchmarks and controls, which makes competing pruning rules hard to compare (Blalock et al., 2020). The connectome setting differs in two ways that make it informative for both fields. First, the network is not trained: weights are fixed measurements, so a removed edge cannot be compensated by retraining and the contribution of wiring is isolated rather than confounded with learning. Second, the target of preservation is not one accuracy number but a set of experimentally validated input–output behaviours together with the population response that produces them, so a rule can be scored on several axes at once. What follows supplies for a connectome what Blalock et al. asked for in artificial networks: a fixed budget, one teacher, matched null models and several preserved quantities."""

DISC_ANN = """**Implications for pruning artificial networks.** Magnitude pruning is the default rule in artificial-network compression (Han et al., 2015), and these results suggest why a rule of that family eventually fails. What survives is not the set of large weights as such, but the intersection of large weights with particular wiring positions: weight-proportional random sampling retains most of the synaptic mass and still collapses at the budget where it begins to miss individual strong edges (§2.3). If this carries over to trained networks—which our fixed model cannot establish, only motivate—then rules that retain strong weights in expectation rather than deterministically (stochastic sparsification, thresholding after quantisation) should be at a disadvantage at equal budget, and the weight-proportional control used here measures the size of that disadvantage in a setting where retraining cannot mask it. The dissociation of §2.7 adds a second caution: a compressed network that matches its teacher on the task metric may already differ in internal representation, which matters whenever the compressed model is reused for another task (§2.4) or interpreted as a model of the computation rather than as a controller."""

STATEMENTS = """## CRediT authorship contribution statement

**Donggyu An:** Conceptualization, Methodology, Software, Formal analysis, Investigation, Data curation, Visualization, Writing – original draft, Writing – review & editing.

## Declaration of competing interest

The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Funding

This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.

## Data availability

All code, result tables, figure sources and the pre-registered design are publicly available at https://github.com/aikian/flylite (MIT licence). The reference model and connectome data are available at https://github.com/philshiu/Drosophila_brain_model. A preprint of this manuscript is available at https://doi.org/%s.""" % DOI

REFS = """## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the author used Claude Opus 5 (Anthropic), through the Claude Code command-line interface, to draft and edit the text of this manuscript, to write the simulation, analysis and figure-generation scripts released with it, and to cross-check the reported numbers against the result tables. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

## References

Berg, S., Beckett, I. R., Costa, M., Schlegel, P., et al. (2026). Sexual dimorphism in the complete *Drosophila* male central nervous system connectome. *Cell*, in press. Preprint: bioRxiv. https://doi.org/10.1101/2025.10.09.680999
Blalock, D., Gonzalez Ortiz, J. J., Frankle, J., & Guttag, J. (2020). What is the state of neural network pruning? *Proceedings of Machine Learning and Systems (MLSys)*, 2, 129–146.
Dhiman, N. (2026). Topological sensitivity in connectome-constrained neural networks. *arXiv*, 2604.04033.
Dorkenwald, S., Matsliah, A., Sterling, A. R., et al. (2024). Neuronal wiring diagram of an adult brain. *Nature*, *634*, 124–138. https://doi.org/10.1038/s41586-024-07558-y
Frankle, J., & Carbin, M. (2019). The lottery ticket hypothesis: Finding sparse, trainable neural networks. *International Conference on Learning Representations (ICLR)*.
Han, S., Pool, J., Tran, J., & Dally, W. J. (2015). Learning both weights and connections for efficient neural networks. *Advances in Neural Information Processing Systems (NeurIPS)*, 28, 1135–1143.
Jin, Z., Zhu, Y., Zhang, C., & Sui, Y. (2026). Whole-brain connectomic graph model enables whole-body locomotion control in fruit fly. *arXiv*, 2602.17997.
Lappalainen, J. K., Tschopp, F. D., Prakhya, S., et al. (2024). Connectome-constrained networks predict neural activity across the fly visual system. *Nature*, *634*, 1132–1140. https://doi.org/10.1038/s41586-024-07939-3
LeCun, Y., Denker, J. S., & Solla, S. A. (1989). Optimal brain damage. *Advances in Neural Information Processing Systems (NeurIPS)*, 2, 598–605.
Pospisil, D. A., Aragon, M. J., Dorkenwald, S., et al. (2024). The fly connectome reveals a path to the effectome. *Nature*, *634*, 201–209. https://doi.org/10.1038/s41586-024-07982-0
Schlegel, P., Yin, Y., Bates, A. S., et al. (2024). Whole-brain annotation and multi-connectome cell typing of *Drosophila*. *Nature*, *634*, 139–152. https://doi.org/10.1038/s41586-024-07686-5
Shiu, P. K., Sterne, G. R., Spiller, N., Franconville, R., et al. (2024). A *Drosophila* computational brain model reveals sensorimotor processing. *Nature*, *634*, 210–219. https://doi.org/10.1038/s41586-024-07763-9
Stimberg, M., Brette, R., & Goodman, D. F. M. (2019). Brian 2, an intuitive and efficient neural simulator. *eLife*, *8*, e47314. https://doi.org/10.7554/eLife.47314
Wang, B., & Chen, J. (2026). FLYNN: Robust neural network for robot navigation using fly brain topology. *arXiv*, 2607.00025.
Wang, F., Theilman, B. H., Rothganger, F., Severa, W., Vineyard, C. M., & Aimone, J. B. (2025). Neuromorphic simulation of *Drosophila melanogaster* brain connectome on Loihi 2. *arXiv*, 2508.16792.

`[Before submission: expand "et al." to the full author lists (APA 7 lists up to 20 authors) from the DOI records.]`"""

def cut(text, start, end):
    i = text.index(start); return i, text.index(end, i + len(start))

# ---- header note
i = s.index("> English manuscript v1"); j = s.index("\n", i)
s = s[:i] + f"> Submission version for *Neural Networks* (Elsevier). Preprint: https://doi.org/{DOI}. Every number is cross-checked against the result tables by `scripts/check_numbers.py`." + s[j:]

# ---- highlights + abstract (replacing abstract) ; drop the Author summary section
i, j = cut(s, "## Abstract", "**Keywords:**")
hl = "## Highlights\n\n" + "\n".join(f"- {h}" for h in HIGHLIGHTS) + "\n\n## Abstract\n\n" + ABSTRACT + "\n\n"
s = s[:i] + hl + s[j:]
i, j = cut(s, "## Author summary", "---")
s = s[:i] + s[j:]

# ---- ANN framing: Introduction paragraph before "Why the answer is not obvious", Discussion paragraph before Limitations
anchor = "**Why the answer is not obvious.**"
assert anchor in s; s = s.replace(anchor, INTRO_ANN + "\n\n" + anchor, 1)
anchor = "**Limitations.**"
assert anchor in s; s = s.replace(anchor, DISC_ANN + "\n\n" + anchor, 1)

# ---- APA in-text citations
rep = [
 ("between neuron pairs [1,2].", "between neuron pairs (Dorkenwald et al., 2024; Schlegel et al., 2024)."),
 ("Shiu et al. built a whole-brain leaky integrate-and-fire (LIF) model constrained only by the connectome and predicted neurotransmitter signs, and confirmed 91% of 164 predictions about sensorimotor circuits experimentally [3].",
  "Shiu et al. (2024) built a whole-brain leaky integrate-and-fire (LIF) model constrained only by the connectome and predicted neurotransmitter signs, and confirmed 91% of 164 predictions about sensorimotor circuits experimentally."),
 ("Lappalainen et al. showed that a connectome-constrained network with only a few hundred free parameters predicts neural responses across the fly visual system [4].",
  "Lappalainen et al. (2024) showed that a connectome-constrained network with only a few hundred free parameters predicts neural responses across the fly visual system."),
 ("(FLYNN) [5]", "(FLYNN; Wang & Chen, 2026)"), ("(FlyGM) [6]", "(FlyGM; Jin et al., 2026)"),
 ("mapped onto neuromorphic hardware [7].", "mapped onto neuromorphic hardware (Wang et al., 2025)."),
 ("and Pospisil et al. apply the same threshold before linear analysis [8]", "and Pospisil et al. (2024) apply the same threshold before linear analysis"),
 ("are preserved above 90% [2]—", "are preserved above 90% (Schlegel et al., 2024)—"),
 ("Dhiman showed that the reported advantage of connectome topology in trained networks disappears when initialisation is shared and a degree-preserving null model is used [9],",
  "Dhiman (2026) showed that the reported advantage of connectome topology in trained networks disappears when initialisation is shared and a degree-preserving null model is used,"),
 ("even against the same degree-preserving control [6].", "even against the same degree-preserving control (Jin et al., 2026)."),
 ("The degree sequence (the null of Dhiman [9]),", "The degree sequence (the null of Dhiman, 2026),"),
 ("that report only output rates [7] can pass", "that report only output rates (Wang et al., 2025) can pass"),
 ("the male central nervous system connectome [11] motivates", "the male central nervous system connectome (Berg et al., 2026) motivates"),
 ("Simulations use Brian2 (v2.10) [10] with", "Simulations use Brian2 (v2.10; Stimberg et al., 2019) with"),
]
for a, b in rep:
    assert a in s, a[:60]; s = s.replace(a, b)
assert not re.search(r"\[\d+(,\s*\d+)*\]", s)

# ---- statements + references replace the old reference section
i = s.index("## References"); s = s[:i] + STATEMENTS + "\n\n" + REFS + "\n"
open(OUT, "w", encoding="utf-8", newline="\n").write(s)

def words(a, b):
    i, j = cut(s, a, b); return len(re.sub(r"[#*`$|]", "", s[i:j]).split())
print("highlights", [len(h) for h in HIGHLIGHTS])
print("abstract", words("## Abstract", "**Keywords:**"))
print("intro", words("## 1. Introduction", "## 2. Results"), "discussion", words("## 3. Discussion", "## 4. Methods"))
print("total", len(re.sub(r"[#*`$|]", "", s).split()), "->", OUT)
