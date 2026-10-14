# Deep audit of the new-submission paper (paper/ and its supplement)

Scope: abstract, every section of `paper/main.tex`, all tables, figure
captions and equations, the supplement, and their agreement with the code
(`src/eddqn/*.py`, `scripts/*.py`, `configs/*.json`) and the saved outputs
(`results/`). Each claim was checked by reading the code that produces it or by
recomputing it from the saved predictions and tables. No experiment was rerun
and no result changed. The only outputs that changed are four new macros and
the re-generated macro files. Regenerating them reproduced every other output
exactly: per-sample predictions identical, figure text identical.

## 1. Confirmed issues and fixes

| # | Where | Problem | Fix |
|---|-------|---------|-----|
| 1 | Results V-D, cost curves | "As R grows, every curve approaches 1" is false. At R = 20 the relative cost is 1.508 for E-DDQN and 1.304 for DQN; Time+game HGB is above 1 for R ≥ 10. | The text now says that well-thresholded models move toward 1, and that models whose thresholds still miss event seconds rise above 1 because each miss is weighted by R. The R = 20 values come from macros. |
| 2 | Results V-D | "the 5:1 ratio places the operating point where that weakness is most visible" was not supported by any analysis. | Replaced with a quantitative statement from new macros. The lowest relative cost over all models and ratios is 0.72 (RF, R = 1.5), so no model removes more than about 28 % of the cost of the better trivial policy. |
| 3 | Table "Threshold-free robustness" caption (also in the old `manuscript/`) | It said "21 whole-session variants". The code uses 17: 12 stress variants plus 5 evasion-only variants. | The caption now uses the macro `\AttAucNVariants` (= 17) and mentions the evasion-only candidates. |
| 4 | Results V-B and Discussion V-B | "once sessions and participants are not shared" and "once participants are not shared" claim participant independence. The data cannot show that. | Both now read "sessions and linkage groups". |
| 5 | Results V-B | ROC-AUC was compared with the prevalence (0.44). ROC-AUC's chance level is 0.5. | The text now gives the 0.5 chance level for ROC-AUC, and adds the best PR-AUC (0.595, DQN) next to its chance level, the prevalence. |
| 6 | Methods, formulation | p̂ was described as a "calibrated-probability scale". For a learned Q-function, p̂ is an estimate: it is not calibrated and can fall outside [0, 1]. | Reworded. Eq. (5) is now a numbered equation. |
| 7 | Results V-F (reward ratio) | "moves along the trade-off exactly as Eq. (3) predicts". The equation predicts the direction and the cut-off, not the numbers. | Now "in the direction Eq. (3) predicts (implied cut-off 1/(1+R))". |
| 8 | Discussion VI-B | "strong bootstrapping … made the learned margins noisy and the validation-based selection over-optimistic" is a causal claim. | Reworded as an association with the two diagnostics in V-E: lower ROC-AUC than γ = 0, and the largest selection optimism. |
| 9 | Limitation (vii) vs Supplement S1 | The paper said the October camera channels "were not logged"; the supplement said they "are constant within every session". | Both now say constant within every session (a logging defect). |
| 10 | Supplement S7, README, run_all.sh | Runtime was given as "about 3 hours". The measured clean rerun took 154 min on 4 cores. | Now "about 2.5 hours (154 minutes in our clean rerun)". |
| 11 | Methods, SHAP | "the first final model of that fold". `07_shap.py` retrains a model with that model's configuration, seed and inner split; bit-identity was not checked. | Reworded to say exactly that. The reason DeepExplainer failed is now stated: the additivity check fails because LayerNorm is not recognized, which was reproduced. |
| 12 | Supplement S1 | "mean 1.1 switches per session" was hard-coded. | Now uses the macro `\PHLabelBinaryChanges`. |
| 13 | `src/eddqn/data.py` docstring | Stale counts: "35 Oct-2019" and "4 Dec-2019" sessions. | Corrected to 37 and 2. The code itself was already correct. |
| 14 | Methods | Attack Types I–III were used without being defined. The camera channels were called quaternion components; the dataset does not document this. | Types are now defined in the threat model. The rotation channel is described with its observed range, and the text notes that the parameterization is undocumented. |

## 2. Methodology rewrite (Section III)

Section III is now nine numbered steps that follow the pipeline in Fig. 1, with
a notation table (Table II) that defines every key term. All statements were
checked against the code:

- **Step 1, data and target.** Dataset, provenance, label and label dynamics. The profile has 9 fields: the 7 CSPQ items plus 2 fields that are constant in the curated release.
- **Step 2, grouping.** Why grouping is needed; the linkage rule (identical 9-field profile, or a restart within 180 s after a session of < 200 rows with ≤ 2 differing fields); nested grouped cross-validation with stratification on game × label; outer seed 20261012 and inner seeds 20261013–20261017.
- **Step 3, causal features.** Definition of a causal feature; the 39 telemetry features broken down as 13 instantaneous, 22 trailing-window and 4 cumulative; spike and frame-drop definitions; the start-up fps artifact; the 11 CSPQ indicators. Preprocessing is fitted on the training rows of each inner split. The feature sets have 39, 50, 8 and 19 features.
- **Step 4, formulation.** Reward (Eq. 1); decomposition with terminal flags (Eq. 2); the three consequences stated separately; regrets (Eq. 4); implied probability (Eq. 5), which uses each agent's own reward table (DQN: Δ = 2, 2).
- **Step 5, E-DDQN.** Each component with its purpose and implementation:
  - dropout placement;
  - Double-DQN target (Eq. 6), with the arg-max in eval mode and y = r when γ = 0;
  - Huber loss, Adam with L2 decay, gradient clipping at 1.0, cosine schedule down to 1e-5;
  - Polyak update plus BN statistics;
  - buffer of 50,000, doubled with full-information replay;
  - ε schedule;
  - warm-up of 4,000 transitions;
  - full-information replay;
  - checkpointing every 2 epochs.
- **Step 6, baselines.** As a list; DQN target written out; un-weighting is Eq. (7).
- **Step 7, protocol.** Four stages (search, cross-fitted final training, thresholds, single test evaluation). D1 breaks ties toward 1/6; the recall rule takes the largest qualifying threshold; event-level metrics are defined; the bootstrap p-value resolution is stated.
- **Step 8, stress tests.** Threat types; 24 stress variants plus 5 hiding variants, 29 in total; 17 whole-session candidates for the adaptive worst cases.
- **Step 9, SHAP.**

## 3. Verified without change (method of verification)

- **Feature counts** (39 / 11 / 8 / 50 / 19): from `features.py` and `feature_dictionary.csv`.
- **Grouping parameters, split seeds and stratification label:** `grouping.py`, `data.py`.
- **Train-only fitting:** `prepare_fold` fits the featurizer and the RobustScaler on the inner-training rows.
- **Reward table, regrets, 1/6 cut-off and implied-probability formula:** `agents.py`.
- **Un-weighting** p = p_w/(5 − 4p_w): `supervised.py`.
- **Dueling head, Double-DQN target, Polyak update with buffer copy, class-balanced replay, ε schedule, warm-up, full-information replay, checkpoint criterion:** `agents.py`.
- **Search spaces, budgets (16; 12 for LogReg), fixed training settings (40 epochs, learn every 2 chunks, 5 consolidation updates):** `configs/protocol.json`, `03_run_protocol.py`.
- **HPO and final stages, cross-fitting and threshold rules:** `03_run_protocol.py`, `experiment.py`, `metrics.py`.
- **Bootstrap p-value formula and percentile CIs:** `metrics.py`. No bootstrap p-value equals 0; the smallest is 0.001.
- **Holm adjustment:** recomputed with statsmodels for all three rules.
- **McNemar test:** exact and χ² with continuity correction; identity b − c = err_B − err_A.
- **Perturbations:** `attacks.py` and `attacks.json` give 29 variants (24 stress, 5 evasion-only) and 17 whole-session candidates. The logged acceleration equals the per-second speed difference in every session, as the supplement states.
- **Reward ratio 5:1 reproduces the main E-DDQN run bit for bit:** all 75 run files (5 folds × 5 seeds × 3 inner splits), validation and test scores.
- **Ablation text:** every number, and the claim that no change exceeds one seed SD (max |Δ| = 0.038 < 0.048).
- **Reward-ratio text:** greedy recall and specificity trend; largest tuned-cost difference 0.044 < smallest seed SD 0.048.
- **Cost-curve numbers:** recomputed from `cost_curves.csv`. At R = 5 they equal the D1 seed-ensemble costs, which the script asserts.
- **Attack ranking claims:** 87 % of combinations change by less than 0.03, max |Δ| = 0.089, and the largest drops are as stated.
- **SHAP set-up:** 200 background samples, 400 test samples, GradientExplainer in all 5 folds, all selected E-DDQN networks layer-normalized.
- **Software versions and clean-rerun runtime:** from the rerun record.

## 4. New automated checks

`scripts/08_consistency_check.py` now also verifies:

- the feature counts and feature-set sizes stated in Section III;
- the numbers of perturbation variants and adaptive candidates (Fig. 1, Section III-H, Table caption);
- the split seeds;
- the cost-curve summary numbers;
- the best primary ROC-AUC and PR-AUC models named in the text;
- ratio 5:1 = main run (when the run files are present);
- that none of the corrected phrasings comes back.

Result: **621 checks, 0 failures** (previously 593).

## 5. Not verifiable from the repository (author-side)

- The TruVR split description (70/30 sample split) should be confirmed against the full text of Kundu et al. 2022.
- The meaning of the `UserSymptoms` field: the paper calls it "a symptoms field" only.
- The camera-rotation parameterization (undocumented; stated as such).
- The remaining items in `paper/SUBMISSION_CHECKLIST.md`: placeholders, DOI, licence, reference details, journal choice.
