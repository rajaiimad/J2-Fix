# Response to the fourth-round points

Six problems were raised. Problems 2 and 3 asked for code-level verification; it was carried out on the real folds with a new script, and every requested check passes. Problems 1, 4, 5 and 6 asked for wording and framing changes; they were made in the abstract, introduction, methods, results, discussion, conclusion, supplement, README and cover letter.

**What did not change:** no model, prediction, threshold, test or reported number. The new script trains no reported model.

**Checks:**
- `scripts/15_pipeline_verification.py`: 169 of 169 checks pass (`results/qc/pipeline_verification.md`).
- `scripts/08_consistency_check.py`: all of its checks pass, including 12 new guards for this round.

## Problem 1: aggregation used for each cost value

**Fix.**
- **Abstract.** Every cost is now given as "mean over seeds (seed ensemble)": E-DDQN 0.663 (0.726), standard DQN 0.584 (0.536), random forest 0.491 (0.485).
- **Abstract, inferential comparison.** It is stated to use the seed ensembles: difference +0.242, 95 % CI +0.052 to +0.528. It was significant under the primary group bootstrap (Holm-adjusted p = 0.006) but not under the exact sign-flip sensitivity test (p = 0.083).
- **Conclusion and cover letter.** Use the same labels and the same wording.
- **Results.** Already distinguished the two aggregations (main results table: left block seed mean ± SD, right block seed ensemble; V-E explains why the ensemble differences are larger). The V-E summary sentence now quotes the effect size and CI next to both p-values.

## Problem 2: leakage controls

**Verification.** `scripts/15_pipeline_verification.py` reuses the production code; nothing is re-implemented. All checks pass:

| What | Result |
|---|---|
| Linkage groups, sessions, exact questionnaire profiles | None shared by any two partitions, for the outer split and all 45 partition pairs of the 15 outer × inner splits. Each group is in exactly one outer fold. Inner folds partition exactly the development groups. Saved split files equal the recomputed splits. |
| Duplicated rows | No raw telemetry row, with or without elapsed time, and no derived feature vector of an evaluation partition is identical to a training row. |
| Train-only preprocessing | Learned parameters and the training matrix are unchanged when every telemetry value of the validation and test rows is replaced by noise, for all 15 splits. |
| Hyper-parameter search | Caches contain no outer-test rows; none of the 3,390 search runs stored a test score. Every selected configuration is the best pooled inner-validation configuration, re-derived from the search log (35 selections). |
| Thresholds | All 210 D1 thresholds (per seed and seed ensemble) are re-derived exactly from the saved inner-validation scores. The threshold function takes no test input. |
| Checkpoints | All 300 neural training runs use the best inner-validation epoch; no training log records a test metric. |

**One check failed, was found to be ill-posed, and was replaced (stated in the report, README and Supplementary S8).** It was a pass/fail criterion requiring each test row's nearest training row to be farther away than the next second of the same session. It failed in 4 of 5 folds. The comparison is ill-posed: the nearest of about 7,000 rows is naturally closer than one fixed neighbour. It is now descriptive, with two reference distances (medians across outer folds):

| Distance | Median |
|---|---|
| Test row → nearest development row | 1.35–2.92 |
| Development row → nearest row of another linkage group | 1.67–2.01 |
| Development row → nearest other row of its own session | 1.40–1.49 |

How to read these distances:
- Test rows are about as close to the training data as unrelated groups are to each other.
- In two folds (1 and 3), test rows are about as close as rows of the same session.
- The measure discriminates weakly in this feature space, so it neither indicates nor excludes a shared participant. The paper says exactly this.

**Text changes.**
- **III-B** now summarises the checks. It states that they establish session- and linkage-group-disjoint evaluation, not participant independence.
- **Limitation (ii)** adds that the groups are reconstructed from questionnaire profiles and session timing, and repeats this distinction.
- **Supplementary S8 (new)** gives the details.

The paper does not describe the evaluation as participant-independent anywhere.

## Problem 3: replay buffer and training loop

**Verification.** E-DDQN, E-CB and the standard DQN were trained with each outer fold's selected configuration on the first inner split: 15 runs, shortened to two epochs; the code path is the same as the full runs. Every transition written to the replay buffer was logged (240,646 in total). In every run:

- **Reward:** the stored reward equals R(a, y) for the stored action and the label of the stored state.
- **Next state:** every non-terminal next state is the next second of the same session.
- **Terminal flag:** set exactly at the last second of each session.
- **Buffer contents:** the buffer holds exactly the logged states, actions, rewards, next states and flags. No transition joins two sessions, and no action is overwritten after its reward is computed.
- **Row order:** the training rows of each session are contiguous and in temporal order.

The executed action and the rewarded action are the same array in `ValueAgent.fit`/`_store`. With full-information replay, which is tuned on or off and was selected in some folds, the counterfactual action is stored as a separate transition with its own reward. This is described in III-E, and no stored transition pairs one action with another's reward.

All checks pass, so no correction or rerun was needed. III-E now reports this verification next to the unit tests.

## Problem 4: one primary inferential procedure

**Choice and justification.** The group bootstrap is the primary procedure. Its code was committed with the frozen protocol (commit 15225db) before any evaluation run, and it gives the effect size, CI and p-value from one resampling distribution. The exact sign-flip test was added after a pre-submission review, when all results were known, so it is the sensitivity analysis. We did not switch the primary procedure after seeing the results.

**Rule stated in III-G.** Every comparison is reported as an effect size with its 95 % CI and Holm-adjusted p-values. A difference counts as firmly established only if it is significant under both procedures.

**Consistent interpretation.** The abstract, introduction, results (V-E), discussion (RQ2, limitation (i)), conclusion, README and cover letter now all say the same:
- E-DDQN has a higher seed-ensemble cost than the random forest (+0.242, CI +0.052 to +0.528).
- The difference is significant under the primary procedure but not under the sensitivity analysis, so it is not firmly established.
- The paper does not conclude that the random forest is superior.

**Always-alarm comparison.** "No model is shown to improve on always alarming" is now qualified in V-E and the conclusion as a statement about the strength of the evidence, not a demonstration of equivalence.

## Problem 5: cause of E-DDQN's weak primary result

**Wording.** "Is largely a consequence of its search draw" (V-G, introduction, discussion VI-B, README) and "reflects its search draw" (abstract, conclusion, cover letter) are replaced. The new wording says the results *suggest* that sensitivity to the search draw contributes (substantially) to the weak primary result. V-G adds that the draw, selected feature sets, discount factors and other hyper-parameters varied together. The experiment therefore isolates no single factor and does not establish the draw as the sole or principal cause.

**Asymmetric reward.** V-G and VI-B now state that the results do not support a benefit of the asymmetric reward. With E-DDQN's configurations held fixed, replacing it with the symmetric ±1 reward gave the lowest cost of all ablation variants (a point estimate within about one seed SD).

**Guards.** The consistency check now rejects the old phrases in the paper, README and cover letter.

## Problem 6: adversarial framing

- **Title.** It already contains no adversarial claim: "Does an Asymmetric-Reward E-DDQN Improve Safety-Prioritized Cybersickness Detection in Virtual Reality? A Leakage-Controlled Comparison with Standard DQN and Cost-Sensitive Baselines". We kept it. "Safety-prioritized" refers to the 5:1 cost, not to attacks.
- **Introduction.** RQ3 is now marked as a secondary sanity check. A new sentence states that it is a feature-space stress test, not an evaluation of attacks: UFFCSData contains no manipulated sessions, so it cannot show whether a detector recognizes real rendering attacks or is robust to them. Contribution 4 calls it a secondary feature-space stress test.
- **Abstract and conclusion.** The perturbation result is now labelled "a stress test, not an attack evaluation" (abstract) and "a secondary feature-space stress test, which does not evaluate real attacks" (conclusion).
- **Unchanged.** Discussion VI-D and Supplementary S4 already made this distinction.

## Files

**Code and outputs:**
- `scripts/15_pipeline_verification.py` (new)
- `results/qc/pipeline_verification.{md,json}`
- `results/tables/pipeline_verification/pv_macros.tex`
- `run_all.sh` and `paper/build.sh` (include the new step)

**Paper:**
- Sections: abstract, s1, s3, s5, s6, s7
- `supplement/sections/s_verify.tex` (new S8) and `s_repro.tex`

**Other documents:**
- `README.md`
- `submission/cover_letter_template.md`
- `scripts/08_consistency_check.py` (12 new guards)
