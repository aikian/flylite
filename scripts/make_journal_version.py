"""Derive the Network Neuroscience submission version from the preprint manuscript.

Changes: abstract <= 200 words, Author Summary <= 125 words, Technical Terms list, APA author-year citations and
reference list, statements (author contributions / funding / competing interests / data availability).
Input  : FlyLite_manuscript_EN_v1.md      Output: FlyLite_manuscript_EN_NetNeuro_v1.md
"""
import re

SRC, OUT = "FlyLite_manuscript_EN_v1.md", "FlyLite_manuscript_EN_NetNeuro_v1.md"
s = open(SRC, encoding="utf-8").read()

ABSTRACT = """Whole-brain connectomes are used as wiring diagrams for spiking simulations and as priors for artificial networks, usually after an ad hoc synapse-count threshold whose functional cost has never been measured. We define *function-preserving sparsification*—removing edges under a fixed budget while preserving validated behaviour and population responses—and study it in the leaky integrate-and-fire whole-brain model of Shiu et al. (2024). Six operators (weak-synapse pruning, uniform and weight-proportional random removal, degree-preserving rewiring, weight shuffling, a task-aware criterion) were compared at identical edge budgets across three validated circuits, silent and active network states, and multiple seeds. Weak-synapse pruning preserves 79% of feeding output with 6% of edges (cliff at k\\* ≈ 9 synapses), whereas random, degree-preserving and weight-shuffled controls abolish output and weight-proportional sampling survives only while it retains the strong-edge set: function resides in the conjunction of placement and strength, not in degree statistics or synaptic mass. The cliff is task-dependent—grooming specificity collapses below k = 2 through disinhibition—and state-dependent: in the active state output over-excites and bitter suppression is lost from k = 5. A task-aware criterion preserves its training stimulus at 0.4% of edges but loses held-out inhibition first: what must be kept depends on task and state."""

SUMMARY = """Neuroscientists have a map of every neuron and connection in the fruit-fly brain, and modellers use it—as a circuit to simulate or as a wiring diagram inside artificial networks. Almost every study first discards weak connections without checking what that does to the behaviours the model reproduces. We asked how much of the connectome a validated brain simulation can lose before it stops working, and what decides which connections matter. The answer is not simply "keep the strong ones": random, rewired or strength-shuffled connections destroy behaviour; a grooming circuit that must tell two sensory pathways apart fails earlier than a feeding circuit; and in a spontaneously active brain, inhibition goes first. The results give principled grounds for the thresholds connectome models use."""

TERMS = """## Technical Terms

- **Connectome:** the complete map of an organism's neurons and the synaptic connections between them.
- **Sparsification:** removing connections from a network while keeping a chosen property—here, validated function.
- **Edge budget:** the number of connections retained, held fixed so that different removal rules can be compared fairly.
- **Magnitude (weak-synapse) pruning:** keeping only connections with more than k synapses, the threshold rule most connectome models apply.
- **Null model:** a control that removes the same number of connections while destroying one specific property (placement, strength or their ordering).
- **Functional cliff (k\\*):** the budget at which the model's validated output first falls below 80% of the full model.
- **Suppression index:** the fraction by which bitter input reduces sugar-evoked motor output; 1 means complete inhibition.
- **Spontaneously active state:** a regime with membrane noise in which neurons fire without stimulation, unlike the silent resting state."""

STATEMENTS = """## Author Contributions

D.A. conceived the study, wrote the pre-registered design, implemented the software, ran the simulations, analysed the data, produced the figures and wrote the manuscript.

## Funding Information

This work received no external funding.

## Competing Interests

The author declares no competing interests.

## Data and Code Availability

A preprint of this manuscript is available at https://doi.org/10.64898/2026.09.19.752860. All code, result tables, figure sources and the pre-registered design are available at https://github.com/aikian/flylite (MIT licence). The reference model and connectome data are from https://github.com/philshiu/Drosophila_brain_model."""

REFS = """## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the author used Claude Opus 5 (Anthropic), through the Claude Code command-line interface, to draft and edit the text of this manuscript, to write the simulation, analysis and figure-generation scripts released with it, and to cross-check the reported numbers against the result tables. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.

## References

Berg, S., Beckett, I. R., Costa, M., Schlegel, P., et al. (2026). Sexual dimorphism in the complete *Drosophila* male central nervous system connectome. *Cell*, in press. Preprint: bioRxiv. https://doi.org/10.1101/2025.10.09.680999
Dhiman, N. (2026). Topological sensitivity in connectome-constrained neural networks. *arXiv*, 2604.04033.
Dorkenwald, S., Matsliah, A., Sterling, A. R., et al. (2024). Neuronal wiring diagram of an adult brain. *Nature*, *634*, 124–138. https://doi.org/10.1038/s41586-024-07558-y
Jin, Z., Zhu, Y., Zhang, C., & Sui, Y. (2026). Whole-brain connectomic graph model enables whole-body locomotion control in fruit fly. *arXiv*, 2602.17997.
Lappalainen, J. K., Tschopp, F. D., Prakhya, S., et al. (2024). Connectome-constrained networks predict neural activity across the fly visual system. *Nature*, *634*, 1132–1140. https://doi.org/10.1038/s41586-024-07939-3
Pospisil, D. A., Aragon, M. J., Dorkenwald, S., et al. (2024). The fly connectome reveals a path to the effectome. *Nature*, *634*, 201–209. https://doi.org/10.1038/s41586-024-07982-0
Schlegel, P., Yin, Y., Bates, A. S., et al. (2024). Whole-brain annotation and multi-connectome cell typing of *Drosophila*. *Nature*, *634*, 139–152. https://doi.org/10.1038/s41586-024-07686-5
Shiu, P. K., Sterne, G. R., Spiller, N., Franconville, R., et al. (2024). A *Drosophila* computational brain model reveals sensorimotor processing. *Nature*, *634*, 210–219. https://doi.org/10.1038/s41586-024-07763-9
Stimberg, M., Brette, R., & Goodman, D. F. M. (2019). Brian 2, an intuitive and efficient neural simulator. *eLife*, *8*, e47314. https://doi.org/10.7554/eLife.47314
Wang, B., & Chen, J. (2026). FLYNN: Robust neural network for robot navigation using fly brain topology. *arXiv*, 2607.00025.
Wang, F., Theilman, B. H., Rothganger, F., Severa, W., Vineyard, C. M., & Aimone, J. B. (2025). Neuromorphic simulation of *Drosophila melanogaster* brain connectome on Loihi 2. *arXiv*, 2508.16792.

`[Before submission: expand "et al." in the reference list to the full author lists (APA 7 lists up to 20 authors) using the DOI records.]`"""

def section(text, start, end):
    i = text.index(start); j = text.index(end, i + len(start)); return i, j

# ---- header note
s = s.replace("> English manuscript v1 (2026-09-19)", "> Journal version for *Network Neuroscience* (derived from the bioRxiv preprint https://doi.org/10.64898/2026.09.19.752860)", 1)

# ---- abstract, keywords, author summary, technical terms
i, j = section(s, "## Abstract", "**Keywords:**"); s = s[:i] + "## Abstract\n\n" + ABSTRACT + "\n\n" + s[j:]
i, j = section(s, "## Author summary", "---"); s = s[:i] + "## Author Summary\n\n" + SUMMARY + "\n\n" + TERMS + "\n\n" + s[j:]

# ---- APA in-text citations (explicit, so the phrasing reads naturally)
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
assert not re.search(r"\[\d+(,\s*\d+)*\]", s), re.findall(r"\[\d+(?:,\s*\d+)*\][^\n]{0,40}", s)

# ---- reference list + statements
i = s.index("## References"); s = s[:i] + STATEMENTS + "\n\n" + REFS + "\n"
open(OUT, "w", encoding="utf-8", newline="\n").write(s)

def words(a, b):
    i, j = section(s, a, b); return len(re.sub(r"[#*`$|]", "", s[i:j]).split())
print("abstract", words("## Abstract", "**Keywords:**"))
print("author summary", words("## Author Summary", "## Technical Terms"))
print("intro", words("## 1. Introduction", "## 2. Results"), "results", words("## 2. Results", "## 3. Discussion"),
      "discussion", words("## 3. Discussion", "## 4. Methods"), "methods", words("## 4. Methods", "## Figure legends"))
print("wrote", OUT)
