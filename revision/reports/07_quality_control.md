<!-- generated from reports/templates/07_quality_control_template.md by scripts/09_render_docs.py; do not edit -->
# Final quality-control report

Every row links a reviewer concern to the code change, the experiment, the manuscript revision and the verification that was actually run. Numbers come from the same macro file as the manuscript.

## A. Automated verification status

| Check | Result |
|---|---|
| Agent / metric unit tests (`scripts/00_sanity_tests.py`) | 22/22 pass |
| Leakage assertions (`scripts/02_preprocessing_audit.py`): feature causality, train-only fitting, zero session/group/profile/duplicate overlap | pass (script asserts) |
| Independent recomputation of confusion matrices, metrics and McNemar tables with scikit-learn/statsmodels vs. manuscript macros (`scripts/08_consistency_check.py`) | 594 checks, 0 failures |
| Macros used in manuscript + supplement text | 119 distinct macros, all defined |
| Numbers from the submitted version found in the compiled PDFs | main: 7, supplement: 13; each occurrence is either in an explicitly labelled description of the submitted version or a coincidental substring of a different number (e.g. "8.8" inside "58.8"); contexts are listed in `results/qc/stale_number_contexts.json` |
| Frozen protocol committed before any evaluation-set training | commit in `configs/FROZEN_PROTOCOL_COMMIT.txt` |
| Clean-state rerun | see §C |

## B. Reviewer concern → change → evidence

| # | Concern | Code change | Experiment / artefact | Manuscript revision | Verification |
|---|---|---|---|---|---|
| R1.1 | Is it RL? Action does not affect next state | γ tuned incl. 0; E-CB (γ=0) as a separate model; `agents.py` docstring | HPO selected γ = 0.99, 0.99, 0.99, 0.99, 0.9; E-CB ROC-AUC 0.653 vs. E-DDQN 0.538; optimism gap E-DDQN +0.288 | Sec. III-D (Eqs. 2–3, contextual bandit), Sec. VI-B; claim of adaptive sequential control removed | `00_sanity_tests.py` (implied threshold 1/6; argmax-Q ⇔ p ≥ 1/6) |
| R1.2 | Transitions / episodes | `_sessions_to_stream`: within-session s', terminal flags, (1−done) in target | all agent runs | Sec. III-E, Alg. 1 | unit tests: next state in the same session, next second, one terminal per session |
| R1.3 | Teacher forcing invalid | removed; optional full-information replay stores each action with its own reward | ablation "± full-information replay" | Sec. III-E; old claim deleted | unit test: replay reward == R(stored action, label) |
| R1.4 | Temporal / participant leakage | raw XML parser, linkage groups, grouped nested CV, causal features, train-only scaler | leakage audit (gradient boosting): reconstructed submitted protocol 99.8 % recall vs. grouped split ROC-AUC 0.523; 92 % of positive test rows duplicated in training; unmodified submitted script MCC 0.870 (leaky) vs. -0.004 (grouped) | Secs. III-A–C, V-A; Suppl. S1, S5 | truncation test (max diff 0), tampering test, overlap checks = 0 |
| R1.5 | Test-set usage contradictions | HPO caches exclude outer-test rows; final stage scores each fold once; predictions saved | `results/predictions/*.csv.gz` | Sec. III-H; old per-checkpoint test plots removed | frozen-protocol commit precedes all evaluation runs |
| R1.6 | Unmatched baselines | `experiment.py`: identical splits, feature-set options, budget (16), checkpoint rule, cross-fitting, thresholds | 7 model families × 5 seeds × 5 outer folds; ablation; reward ratio | Secs. III-F, IV, V-B–V-G | identical row alignment asserted in paired tests |
| R1.7 | BN target statistics, train-mode arg-max, warm-up/update mismatch | `_sync_target` copies buffers; eval-mode arg-max; explicit hyper-parameters | — | Sec. III-E | unit test: target BN buffers equal online buffers |
| R2.1 | Adversarial claims unsupported | `attacks.py`, `configs/attacks.json` (frozen); labels never modified; z indicator separate | 29 perturbation variants + adaptive worst cases; max ROC-AUC change 0.089; evasion recall drop 4–19 pp | Secs. III-G, V-H, VI-D, limitations; FOV explicitly not testable | perturbations re-featurised with the frozen, train-fitted featurizer |
| R2.2 | Asymmetric reward vs. cost-sensitive threshold | common implied-probability score; D0/D1/recall rules for all models | E-DDQN D1 cost 0.663 vs. CS-MLP 0.557; reward-ratio study | Sec. III-D (Eq. 3), V-C, V-G | unit test of regret ratio 5 and threshold 1/6 |
| R2.3 | Contradictory numbers | single pipeline; macros; generated tables | — | all numbers replaced | `08_consistency_check.py` |
| R2.4 | McNemar counts/p-value | `metrics.mcnemar` asserts b − c = err_B − err_A; group bootstrap | E-DDQN vs. RF: b = 293, c = 1,178; group-bootstrap p = 0.001 | Sec. V-D, Table 7 | statsmodels recomputation (exact p and χ²) |
| R2.5 | Unverified citations (93.5 %, 35 ms) | — | `reports/06_reference_verification.md` | 9 removed, 15 corrected, verified additions listed | web-search evidence per reference |
| R2.6 | Provenance / reproducibility | `io_raw.py`, `run_all.sh`, requirements | provenance JSON, session table | Sec. III-A, Data Availability, Suppl. S1, S6 | dataset.csv shown identical to curated XML (lexicographic order) |

## C. Clean-state rerun

Clean-state rerun of commit `deb2cd9`: the pushed branch was cloned into an empty directory and `bash revision/run_all.sh --fresh --workers 4` deleted every generated artefact and regenerated everything from the raw XML files (sanity tests, audits, proxy runs of the earlier script, preprocessing audit, development calibration, hyper-parameter search, selection, final evaluation, ablation, reward ratio, aggregation, SHAP, tables, LaTeX builds, post-hoc baselines and analyses, new-submission paper and supplement, consistency check, document rendering).

* Exit status / timing (tail of the log): `real	154m25.457s | user	519m1.706s | sys	1m46.138s | EXIT 0 | END Tue Oct 13 18:56:20 UTC 2026`
* Artefacts compared: 142; differing or missing: 0.
* Per-sample prediction files with any numeric difference: 0.
* Result macros differing: 0 (wall-clock timing macros, which are not used in the text, are excluded: ['CSMLPMeanSeconds', 'DQNMeanSeconds', 'ECBMeanSeconds', 'EDDQNMeanSeconds', 'HGBMeanSeconds']).
* Post-hoc macros differing: 0 of 389.

All result-bearing artefacts reproduce: every per-sample score is identical, 107 files are byte-identical and 8 are identical in content, and the 4 compiled PDFs have identical text. The content-only differences are: `same content (parsed JSON)`; `same content (row/column order ignored)`; `same content (row/column order ignored; only wall-clock timing columns ['mean_seconds'] differ)`; `same content (row/column order ignored; only wall-clock timing columns ['seconds'] differ)`; `same content except wall-clock timing macros (*MeanSeconds)`; `same content except wall-clock timing macros ['CSMLPMeanSeconds', 'DQNMeanSeconds', 'ECBMeanSeconds', 'EDDQNMeanSeconds', 'HGBMeanSeconds']`. Details: `results/qc/clean_rerun_comparison.csv`.


## D. Remaining unresolved issues

1. No participant IDs, so participant independence is conservative but unverifiable.
2. No attacked sessions and no measured attack effects; the threat model is supported only by synthetic feature-space stress tests, and FOV manipulation cannot be tested.
3. Offline data cannot demonstrate sequential control.
4. With 21 groups the confidence intervals are wide: even the random forest's cost CI (0.381–0.577) includes the always-alarm cost 0.558.
5. The submitted 41-feature files and the baseline/ablation code were never in the repository, so the submitted numbers could only be reproduced by proxy.
6. Several references remain flagged for the authors to confirm (PRECYSE venue; VR-LENS venue).
