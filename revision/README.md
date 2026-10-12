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

## Reproduce

```bash
pip install -r revision/requirements.txt         # CPU is sufficient
bash revision/run_all.sh --fresh --workers 4      # ~3 h wall time on 4 CPU cores
```

`run_all.sh` runs these steps in order:

1. Sanity tests.
2. Provenance and leakage audit.
3. The unmodified submitted script on the proxy splits.
4. Preprocessing audit, including the frozen splits.
5. Development-wave calibration.
6. Hyper-parameter search, selection, final evaluation, ablation and reward-ratio runs.
7. Aggregation, SHAP and table/macro generation.
8. LaTeX build and the consistency check.

The last step independently recomputes every confusion matrix, metric and McNemar table and compares it with the manuscript.

## Key design decisions

* **Data:** the 35-session curated UFFCSData release is used for evaluation. The 37 Oct-2019 sessions are used only for development.
* **Unit of independence:** conservative *session-linkage groups*, because the release contains no participant IDs.
* **Splits:** nested grouped cross-validation (5 outer × 3 inner). Outer-test rows are not featurised during tuning, and each outer fold is scored once.
* **Features and preprocessing:** causal features only; all learned preprocessing is fitted on training groups.
* **Fair comparison:** every model gets the same tuning budget, checkpoint rule, cross-fitting recipe, operating rules and paired statistics.
* **Primary decision rule:** the threshold minimising the 5:1 cost on validation predictions.

## Headline

Under this protocol E-DDQN does **not** outperform the standard DQN. It is significantly worse than a cost-weighted random forest, and no model achieves high recall with a controlled false-alarm rate on these data. See `reports/05_results.md`.
