# Revision workspace: leakage-free rebuild of the E-DDQN study

The original submission files at the repository root are left **unmodified**:
* `DRL_cybersickness_FAST_v2.py`
* `Manuscript (2).pdf`
* `UFFCSData-master_raw_source/`

Everything produced for the revision lives here.

## Deliverables

| # | Deliverable | Location |
|---|---|---|
| 1 | Reproducible preprocessing pipeline (raw XML → leakage-checked partitions and model inputs) | `src/eddqn/io_raw.py`, `grouping.py`, `features.py`, `data.py`; `scripts/02_preprocessing_audit.py`; frozen splits in `data/processed/` |
| 2 | Data audit report | `reports/01_data_audit.md` (+ `results/preprocessing/`) and repository/provenance audit `reports/00_repository_audit.md` (+ `results/audit/`) |
| 3 | Corrected model code: E-DDQN, standard DQN, contextual-bandit E-CB, cost-sensitive MLP, LogReg, gradient boosting, random forest | `src/eddqn/agents.py`, `src/eddqn/supervised.py`, `src/eddqn/experiment.py`; formulation report `reports/03_rl_formulation.md` |
| 4 | Training/evaluation scripts with frozen configuration, seeds, validation-only selection and saved predictions | `configs/protocol.json`, `configs/attacks.json` (frozen at the commit in `configs/FROZEN_PROTOCOL_COMMIT.txt`); `scripts/03_run_protocol.py`, `scripts/04_aggregate.py`; per-sample predictions in `results/predictions/` |
| 5 | Experimental results: metrics, confusion matrices, ROC/PR, CIs, paired tests, ablations, reward ratio, clean vs. perturbed | `results/tables/`, `results/figures/`; summary `reports/05_results.md` |
| 6 | Revised manuscript (LaTeX + PDF) | `manuscript/main.tex`, `manuscript/main.pdf` |
| 7 | Revised supplementary material | `supplementary/supplement.tex`, `supplementary/supplement.pdf` |
| 8 | Reviewer-response draft | `reviewer_response/response_to_reviewers.md` |
| 9 | Final quality-control report | `reports/07_quality_control.md` (+ `results/qc/`) |
| – | Reference verification | `reports/06_reference_verification.md` |
| – | **Submission package** (final manuscript, supplement, separate figures, cover letter and highlights drafts, curated code-and-data archive for a DOI) | `python3 scripts/12_make_submission_package.py` → `submission_package/` (not tracked; templates in `submission/`) |
| – | **New-submission version** (re-framed paper for a new journal; includes post-hoc exposure-time baselines and sensitivity analyses) | `paper/main.pdf`, `paper/supplement/supplement.pdf` (build: `bash paper/build.sh`); checklist `paper/SUBMISSION_CHECKLIST.md`; post-hoc spec `configs/posthoc.json`, code `scripts/11_posthoc.py` and `scripts/13_search_draw_sensitivity.py`, results `results/tables/posthoc/` and `results/tables/search_draw/` |

## Reproduce

```bash
pip install -r revision/requirements.txt         # CPU is sufficient
bash revision/run_all.sh --fresh --workers 4      # ~2.5-3.5 h on 4 CPU cores (2 h 46 min of computing in the clean rerun of the final version)
```

`run_all.sh` runs these steps in order:

1. Sanity tests.
2. Provenance and leakage audit.
3. The unmodified submitted script on the proxy splits.
4. Preprocessing audit, including the frozen splits.
5. Development-wave calibration.
6. Hyper-parameter search, selection, final evaluation, ablation and reward-ratio runs.
7. Aggregation, SHAP and table/macro generation.
8. Post-hoc analyses (`scripts/11_posthoc.py`) and the search-draw sensitivity analysis (`scripts/13_search_draw_sensitivity.py`).
9. LaTeX build and the consistency check.

The last step independently recomputes every confusion matrix, metric and McNemar table and compares it with the manuscript.

## Key design decisions

* **Data:** the 35-session curated UFFCSData release is used for evaluation. The 37 Oct-2019 sessions are used only for development.
* **Unit of independence:** conservative *session-linkage groups*, because the release contains no participant IDs.
* **Splits:** nested grouped cross-validation (5 outer × 3 inner). Outer-test rows are not featurised during tuning, and each outer fold is scored once.
* **Features and preprocessing:** causal features only; all learned preprocessing is fitted on training groups.
* **Fair comparison:** every model gets the same search procedure and budget (16 configurations; 12 for logistic regression, whose space has only 24 configurations), checkpoint rule, cross-fitting recipe, operating rules and paired statistics.
* **Primary decision rule:** the threshold minimising the 5:1 cost on validation predictions.

## Post-hoc analyses (after the primary results)

All of these were specified after the primary results were known and use the frozen protocol's splits, rules and seeds. They differ in when they were specified:

* **Committed in `configs/posthoc.json` before they were run:** the two exposure-time baselines, the Holm adjustment of the comparisons with E-DDQN, the comparison with always alarming, the grouping sensitivity analyses (session bootstrap and leave-one-group-out jackknife) and the cost curves.
* **Added later without prior commitment:** the paired comparisons of the exposure-time baselines with the primary models, the Holm adjustment of the always-alarm comparison, the Q-value-scale diagnostic, and (after a pre-submission review, key `review_round_2`) the within-fold ROC-AUC, the exact group sign-flip tests and the feature-set and search-draw tallies.
* **Specified, with decision rules, and committed before it was run (key `search_draw_sensitivity`, commit `b15fa6e`):** the search-draw sensitivity experiment, which re-tunes E-DDQN and the standard DQN with two further random search draws and one exposure-only draw.
* **Final pre-submission check (descriptive, no training):** the score scale of the untuned rule D0 (`scripts/14_score_scale.py`). Class-balanced replay and the Huber loss with a ±1 reward move the nominal cut-off p̂ ≥ 1/6 to 0.08–0.21 on P(y=1|s) for E-DDQN, E-CB and the balanced CS-MLP, and to 0.25 for the standard DQN at γ = 0. Rule D1 and all ranking metrics are unaffected.

Main post-hoc results:

* **Elapsed-time baseline (Time-LR).** A logistic regression on elapsed time alone reaches pooled ROC-AUC 0.704, the highest pooled value of all models; within folds the random forest is slightly higher (0.715 vs 0.709). No primary model ranks seconds significantly better than Time-LR, but equivalence is not established either. At the 5:1 operating point the random forest has a lower cost (group bootstrap p = 0.021, exact sign-flip p = 0.044; approximate with 21 groups).
* **E-DDQN vs the random forest (E-DDQN's primary search draw).** E-DDQN's seed-ensemble cost is higher in every outer fold (marginally in one). The difference is significant under the group bootstrap after Holm adjustment (p = 0.006), but not under the more conservative exact sign-flip test (Holm-adjusted p = 0.083).
* **Always-alarm comparison.** With linkage groups as units, no model is shown to beat always-alarm at 5:1 after Holm adjustment (the adjustment was added without prior commitment). With sessions as units, the random forest's advantage remains significant after adjustment (p = 0.002, Holm 0.018; approximate).
* **Grouping sensitivity.** The session-level bootstrap and the leave-one-group-out jackknife give the same direction for every comparison.
* **Search-draw sensitivity (pre-specified).** In no draw does E-DDQN have a significantly lower cost than the standard DQN (differences −0.135 to +0.190; smallest p = 0.079). But E-DDQN's result depends strongly on its draw: within-fold ROC-AUC 0.539–0.714 and seed-mean cost 0.549–0.663 across three draws (standard DQN: 0.629–0.666 and 0.580–0.634). In ranking, the standard DQN is better with the primary draw (p = 0.021, approximate) and E-DDQN with draw 2 (p = 0.009). Restricted to exposure features, E-DDQN is within 0.026 within-fold ROC-AUC of the DQN, which supports the feature-set explanation (rule R3). E-DDQN's last place in the primary analysis is therefore largely a consequence of its search draw.

## Headline

Under this protocol E-DDQN does **not** have a significantly lower 5:1 cost than the standard DQN, with its primary search draw or with two further pre-specified draws; in ranking, each agent is significantly better in one draw. With its primary draw its seed-ensemble cost is higher than that of a cost-weighted random forest in every outer fold (significant under the group bootstrap, not after Holm adjustment under the exact sign-flip test), but that draw is its weakest of three. No model achieves high recall with a controlled false-alarm rate on these data. See `reports/05_results.md`.
