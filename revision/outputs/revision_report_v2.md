# Revision report: shortened IEEE Access version (v2)

**Deliverables**

| Item | File |
|---|---|
| Revised manuscript (LaTeX) | `paper/main_access_v2.tex` with `paper/sections_v2/*.tex` |
| Revised manuscript (PDF) | `paper/main_access_v2.pdf` |
| Supplement (LaTeX) | `paper/supplement/supplement_v2.tex` |
| Supplement (PDF) | `paper/supplement/supplement_v2.pdf` |
| Fig. 1, workflow | `paper/figs/v2_workflow.pdf` (source `paper/figs_src/v2_workflow_tikz.tex`) |
| Fig. 2, E-DDQN architecture | `paper/figs/v2_eddqn.pdf` (source `paper/figs_src/v2_eddqn_tikz.tex`) |
| Fig. 3, evaluation protocol | `paper/figs/v2_protocol.pdf` (source `paper/figs_src/v2_protocol_tikz.tex`) |
| Unresolved issues | `outputs/unresolved_issues_v2.md` |

**The original is untouched.** `paper/main_access.tex`, `paper/sections/` and `paper/supplement/supplement.tex` and their PDFs are unchanged. `paper/build.sh` builds both versions.

**Length**

| | Original | v2 |
|---|---|---|
| Pages | 21 | **15** |
| Body text | ≈14,400 words | ≈7,100 words |

Both page counts include the references and the author biographies. Two full-width figures and one settings table were added. Seven tables and one figure moved to the supplement.

**What did not change**

- No result, number, test, model, split or conclusion.
- All 55 references are still cited.
- The abstract is identical to the full-length version; at about 245 words it is already within the IEEE Access limit of 250.

## 1. Audit findings that guided the revision

| Finding in the original | Action in v2 |
|---|---|
| Methods (5,200 words) explained the pipeline three times: overview paragraph, Fig. 1, step-by-step prose. Settings were scattered across Methods and Setup. | Methods and Setup merged into one section (III). The pipeline is shown once (Fig. 1) and the settings once (Table 1). |
| Fig. 1 showed a 10-box chain without E-DDQN internals or the protocol. | Three figures: workflow (Fig. 1), E-DDQN architecture (Fig. 2), evaluation protocol (Fig. 3). |
| The score-scale discussion was one 600-word paragraph. | Cut to about 130 words with all ranges kept; details in Supp. S5.12. |
| Results repeated table values in the text: operating rules, matched points, optimism, perturbation AUC, reward ratio. | Text reports patterns only; five tables moved to Supp. S9.3–S9.7. |
| Caveats were repeated in Results, Discussion and Conclusion (sign-flip vs bootstrap, "not evidence of robustness", search-draw qualifiers). | Each caveat is stated once in full and then referenced briefly. |
| Introduction and Related Work restated background on VR, cybersickness and leakage. | Shortened by 35% and 57%. The gap table moved to Supp. Table S5 (Sec. S9.2). All citations kept. |

## 2. Section-by-section changes

**I. Introduction (1,004 → 652 words)**
- Background compressed.
- RQ3 is labelled a secondary feature-space stress test.
- The contributions keep every qualifier: not significant against DQN; not firmly established against RF; "suggests … contributes"; matched number of configurations, not coverage.

**II. Related Work (818 → 353 words + supplement table)**
- Organised in three themes (detection and its evaluation, threats, RL for cost-sensitive detection), plus one gap paragraph.
- Contradictory evidence kept: the TruVR 70/30 split and the earlier 96.88 % result (the latter in the Introduction).

**III. Methods and Experimental Setup (5,881 → 3,078 words)**
- Organised by stage, matching Fig. 1.
- Every equation is kept: reward, Q-decomposition, margin, regrets, implied probability, Double-DQN target, unweighting.
- Algorithm 1 is kept.
- New Table 1 lists every setting, checked against `configs/protocol.json` by the consistency check.
- Protocol, primary vs sensitivity inference and post-hoc provenance are each stated once.
- The E-DDQN components were verified against `src/eddqn/agents.py`. One reviewer-found detail was added: all five selected E-DDQN networks use layer normalization, so the batch-norm statistics copy was inactive in the reported runs.

**IV. Results (4,315 → 1,810 words)**
Kept in the main text:
- split-protocol effect (Table 2);
- main comparison (Table 3), with seed mean and seed ensemble labelled;
- exposure-time baselines (Fig. 4);
- paired tests (Table 4), with the primary vs sensitivity outcome;
- cost curves (Fig. 5);
- event level;
- diagnosis of E-DDQN, split into the pre-specified search-draw experiment (rules R1–R3 defined) and exploratory diagnostics;
- ablation (Table 5);
- stress test;
- SHAP summary.

**V. Discussion (1,646 → 912 words)**
- Organised as: what the results support (RQ1–RQ3), whether E-DDQN is RL, the safety objective, limitations (i)–(x), implications.
- New limitation (ix): threshold transfer between single-model OOF scores and averaged test scores (see the unresolved-issues list).

**VI. Conclusion (437 → 270 words)**
- Each number is labelled by aggregation. "Post hoc" and "Holm-adjusted" are restored.

## 3. Figures and tables

| Item (original numbering) | Decision |
|---|---|
| Fig. 1 pipeline | Redesigned: 10 implemented stages in three lanes (data construction / development / held-out evaluation), a firewall note, the dashed held-out path, and post-hoc analyses marked †. |
| Fig. 2 (new) | E-DDQN architecture: training lane (session stream, ε-greedy action, reward table, replay with optional full-information, class-balanced minibatch, dueling online net, Polyak target, Double-DQN target, Huber loss, update schedule, validation checkpoint) and inference lane (state, checkpointed nets, ΔQ → p̂, threshold, alarm). Every element was verified against the code. |
| Fig. 3 (new) | Protocol: outer/inner group folds; per-split fitting; search → final training → thresholds; single test evaluation (per seed and ensemble); repeat over folds; comparison (post-hoc parts marked). |
| Table I notation | Moved to Supp. S9.1; terms are defined in the text. |
| Table II gaps | Moved to Supp. Table S5 (Sec. S9.2). |
| Algorithm 1 | Kept, condensed. |
| Tables III leakage, IV main, VIII paired, XI ablation | Kept. |
| Table V operating rules, VI matched points, IX optimism, X ratio, XII perturbation AUC | Moved to Supp. S9.3–S9.7. The text keeps the key numbers. |
| ROC figure, cost-curve figure | Kept. |
| SHAP figure | Moved to Supp. S9.8; the text keeps the top features. |
| New Table 1 settings | Added; consolidates Sections III-E/F and IV of the original. |

## 4. Quality control

**Build.** All five PDFs build without errors, overfull content boxes or undefined references.

**`scripts/08_consistency_check.py`: 1,454 checks pass, 0 failures.** New v2 guards check:
- forbidden overstatements;
- required qualifiers in every section (not firmly established, stress test, not participant independence, suggestive diagnosis, no benefit of the reward);
- all equation, figure, table and algorithm labels present;
- Table 1 against `protocol.json`;
- the cross-figure reference (Fig. 1 → Fig. 2);
- every cited supplement section exists;
- page count;
- approximate-zone p-value caveats in v2 paragraphs;
- stale numbers of the earlier version in the v2 PDFs.

**Independent critical review.** A separate agent compared v2 with the original, the code and the macros. Its 7 must-fix and 13 should-fix findings were all addressed:
- post-hoc analyses marked in Figs. 1 and 3 and in Table 1;
- the provenance sentence restored;
- the search-draw experiment separated from the exploratory diagnostics, and an unsupported causal phrase removed;
- the draw range correctly attributed to all draws, including draw 1;
- the threshold step moved after final training in Fig. 1;
- Fig. 3 now describes both the per-seed and the ensemble scoring;
- the D0 description, the buffer size with full information, the seed description, the coverage caveat, "point estimates", "post hoc", the robustness check without E-DDQN, the retraining-variability caveat, the Time+game HGB result, and unadjusted-p labels restored;
- within-fold ROC-AUC, selection optimism, R1–R3 and draw 1 defined before use.

Most optional findings were also applied. Two optional details were left out on purpose: the D1 tie rule in the figure, and the ROC false-positive rate at 95 % recall, which is now in Supp. S9.4.
