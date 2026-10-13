# Response to Reviewers

**Manuscript:** Enhanced Double Deep Q-Network (E-DDQN) with Asymmetric Reward Design Versus Standard Deep Q-Network for Safety-Prioritized Cybersickness Detection in Virtual Reality Under an Adversarial Threat Model: A Comparative Analysis

We thank both reviewers. Their comments led us to rebuild the study from the raw data. We found that the results of the submitted version were produced by data leakage, and we report this openly.

* Every number in the revised manuscript was regenerated from the raw UFFCSData XML files by the code in `revision/`, under a protocol committed before any model was trained on the evaluation sessions.
* The revised results do **not** support the headline claims of the submitted version. We have replaced them instead of defending them.
* The title, the research gap and E-DDQN as the central framework are retained. The contribution statements now describe what the evidence supports.

Numbers below are inserted automatically from `revision/results/tables/manuscript_macros.json`, the same source the manuscript uses.

---

## Summary of the main changes

1. **Data provenance and leakage.**
   * The data are the public UFFCSData release (Porcino et al.). Our previous text called it "GLCD" and did not cite it.
   * The submitted pipeline oversampled every discomfort grade to 5,243 samples and only then split rows at random. This reproduces our earlier partition sizes (14,680 / 3,146 / 3,146) exactly.
   * Under that protocol {{LeakDupPct}} % of positive test rows have exact duplicates in training. A generic gradient-boosting model reaches {{LeakOldAcc}} % accuracy and {{LeakOldRecall}} % recall.
   * With a grouped split, the same model on the same columns drops to ROC-AUC {{LeakGrpRocAuc}}.
2. **New, leakage-free protocol.**
   * Splitting unit: conservative session-linkage groups ({{nGroupsEval}} groups from {{nSessionsEval}} sessions; no participant IDs exist).
   * Evaluation: nested grouped cross-validation ({{nOuter}} outer × {{nInner}} inner folds).
   * Features are causal; all preprocessing is fitted on training groups only.
   * One frozen protocol governs every model: equal tuning budgets, validation-only checkpoints and thresholds, and single scoring of each outer-test fold.
3. **RL formulation.**
   * We prove that on logged data the problem is a contextual bandit.
   * The 5:1 asymmetric reward induces exactly the 5:1 cost-sensitive Bayes threshold P(y=1|s) ≥ 1/6.
   * Implementation errors were corrected, including invalid teacher forcing, cross-session transitions and target-network statistics.
4. **Results.**
   * E-DDQN: 5:1 expected cost {{EDDQNCostCostMean}} ± {{EDDQNCostCostSD}}, ROC-AUC {{EDDQNCostRocAucMean}}.
   * Standard DQN: cost {{DQNCostCostMean}}, ROC-AUC {{DQNCostRocAucMean}}.
   * Best model, a cost-weighted random forest: cost {{RFCostCostMean}}, ROC-AUC {{RFCostRocAucMean}}.
   * Always alarm: cost {{AlwaysCost}}.
   * E-DDQN does not outperform the standard DQN. It is significantly worse than the random forest (group-bootstrap p = {{PairDOneRFPboot}}).
5. **Adversarial framing.**
   * The dataset contains no attacks, so the target is a cybersickness label.
   * Detector robustness is now evaluated with bounded, reproducible perturbations of the frame-rate, camera-orientation and locomotion telemetry.
   * These are explicitly labelled as synthetic feature-space stress tests. Field-of-view manipulation cannot be evaluated because the field of view never varies in the data.
6. **Statistics and citations.**
   * The McNemar contingency tables are now checked against the error counts. The previous McNemar values were internally inconsistent.
   * Group-bootstrap inference is added.
   * Nine references that could not be found were removed and fifteen were corrected, including the 93.5 % / ~35 ms attributed to Kundu et al., which we could not verify.

---

## Reviewer 1

**R1.1 — "The action does not affect the next telemetry sample; is this genuinely reinforcement learning?"**

We agree, and we now show it formally (Sec. III-D).
* The telemetry was logged without the alarm in the loop, so P(s_{t+1} | s_t, a_t) = P(s_{t+1} | s_t).
* Hence Q*(s,a) = E[r|s,a] + γ E[V*(s')|s], whose second term is action-independent. The optimal policy is therefore myopic for every γ, and the problem is a contextual bandit.
* We no longer claim that E-DDQN learns adaptive sequential control.
* γ is kept as a hyper-parameter chosen on validation data, and the γ = 0 special case is evaluated as a separately tuned model (E-CB).

Empirically:
* Validation selected γ = {{EDDQNGammas}} for E-DDQN. The resulting models generalised worst of all models: optimism gap {{EDDQNOptGap}}, versus at most {{ECBOptGap}} for every other model.
* E-CB reached ROC-AUC {{ECBCostRocAucMean}}, versus {{EDDQNCostRocAucMean}} for E-DDQN.

This is consistent with the theory that bootstrapping can only add noise here.

**R1.2 — State transitions and episode construction.**
* The submitted code used the next row of a randomly shuffled chunk as s'. During warm-up it used the next file row. It set no terminal flags.
* An episode is now one recorded session in temporal order, and s' is the next second of the same session.
* The last sample is terminal and the target uses (1 − done). No transition links two sessions.
* Unit tests verify all of this (`scripts/00_sanity_tests.py`, 22/22 pass).

**R1.3 — Teacher forcing.**
* The submitted code computed the reward of a random action but stored the true label as the action. For example, a random "silent" decision on an event was stored as *alarm* with reward −0.5. This trained the correct action toward the false-negative penalty.
* The procedure is removed.
* Labels are available offline, so the reward of both actions is known. E-DDQN may instead store the counterfactual action with **its own** reward ("full-information replay"). This is a valid transition, and its use is tuned on validation data.
* The earlier claim that teacher forcing "preserves the safety incentives" was wrong and has been deleted.

**R1.4 — Temporal and participant/session leakage.**
* This was the decisive problem (see Summary item 1).
* All splits are now made at the level of linkage groups before any feature is computed. Features use only past samples of the same session; this is verified by truncation tests.
* All learned preprocessing is fitted on training groups only; this is verified by tampering tests.
* Executable checks report zero session, group, identical-profile and duplicated-row overlap between development and test data (`results/preprocessing/partition_overlap_checks.csv`).
* Participant identity cannot be verified because the release contains no participant IDs. We state this limitation and explain why the linkage groups are conservative.

**R1.5 — Test-set usage.**
* The reviewer was right: the submitted script scored the test set every 10 episodes, and Table 6 and Figs. 7, 10 and 13 reported per-checkpoint test results.
* We treat all earlier results as exposed. In the revision:
  * the protocol (`configs/protocol.json`) and perturbation set (`configs/attacks.json`) were committed before any model was trained on the evaluation sessions;
  * outer-test rows are not even featurised during hyper-parameter search;
  * each outer-test fold is scored exactly once by the frozen final stage;
  * all reported metrics are computed from the saved predictions.
* The October-2019 raw sessions were used only for development and calibration.

**R1.6 — Unmatched baselines.**
* All models now share the same splits, candidate feature sets, target, random-search budget ({{HPOBudget}} configurations per family; 12 for logistic regression), checkpoint rule, cross-fitting recipe, threshold rules and paired statistics. The models are:
  * E-DDQN;
  * a standard DQN (symmetric ±1 reward, max-operator target, hard target copies, uniform replay);
  * E-CB (contextual bandit);
  * a cost-sensitive MLP with the same trunk family;
  * logistic regression, gradient boosting and a random forest, all with the same 5:1 class weight.
* Component contributions are isolated by a leave-one-component-out ablation and by a reward-ratio sensitivity analysis (Sec. V-G).

**R1.7 — Other implementation issues.**
* The Polyak update ignored batch-normalisation statistics; buffers are now synchronised.
* The Double-DQN arg-max ran in training mode.
* The warm-up size (14,680 vs. 25,000) and update interval (25 vs. 50) did not match the paper.
* Code comments contradicted the code.
* All of these are fixed and documented (`reports/00_repository_audit.md` §5).

---

## Reviewer 2

**R2.1 — Unsupported adversarial claims.**
* We agree that grade ≥ 1 marks self-reported cybersickness, not an attack, and that no attacked sessions exist in the data.
* We retained the title and research gap. The threat model (frame pacing, motion distortion, FOV manipulation) motivates the work and is supported by verified literature (Odeleye et al., VR4Sec 2021; Tseng et al., CHI 2022; Kundu et al., TDSC 2025).
* We now evaluate only what the data support: bounded, reproducible perturbations of the logged telemetry channels, with features recomputed by the frozen featurizer and labels never changed.
* The scenarios include adaptive per-session worst cases for evasion and false-alarm induction.
* Results:
  * threshold-free ROC-AUC changes by at most {{AttAucMaxAbsChange}};
  * worst-case evasion lowers recall on event seconds by {{AttEvasionDropMin}}–{{AttEvasionDropMax}} percentage points;
  * worst-case false-alarm induction raises the false-positive rate to {{EDDQNAttWorstFPR}}–100 %.
* FOV manipulation cannot be evaluated because the field of view is constant within each game.
* The manuscript states throughout that these are feature-space stress tests, not demonstrations of physical rendering attacks.

**R2.2 — Relationship between the asymmetric reward and cost-sensitive thresholding.**
* Eq. (3) shows that Q*(s,1) − Q*(s,0) = 1.0·p(s) − 0.2·(1 − p(s)), so the greedy policy alarms iff p(s) ≥ 1/6. This is exactly the Bayes rule of a cost-sensitive classifier with C_FN : C_FP = 5 : 1.
* We therefore compare all models on a common calibrated scale and with the same validation-selected operating rules.
* With matched rules, the asymmetric reward provides no advantage over cost-weighted training with a validation-selected threshold:
  * E-DDQN cost {{EDDQNCostCostMean}} vs. CS-MLP {{CSMLPCostCostMean}}, logistic regression {{LRCostCostMean}} and random forest {{RFCostCostMean}};
  * untuned arg-max policy: E-DDQN {{EDDQNBayesCostMean}} vs. random forest {{RFBayesCostMean}}.
* The reward-ratio sensitivity analysis (1:1 to 10:1) is reported in Sec. V-G.

**R2.3 — Contradictory numerical results.**
* All numbers of the submitted version are replaced.
* The new numbers come from one pipeline (`run_all.sh`). Every manuscript number is a macro generated from saved predictions.
* `scripts/08_consistency_check.py` independently recomputes all confusion matrices, metrics and McNemar tests with scikit-learn and statsmodels and compares them with the manuscript.
* The previous contradictions are listed in Supplementary §S5, including test-set usage, "the reward is the only change", the 2-output vs. 4-class baseline, "threshold-independent" MCC/F2 and the teacher-forcing ablation.

**R2.4 — McNemar statistics.**
* The reviewer is correct. With 172 baseline errors and 98 E-DDQN errors, b − c must equal 74, but the reported b = 96 and c = 34 give 62. The printed χ² = 28.6 was computed correctly from impossible counts.
* McNemar tables are now built from the paired test predictions and asserted to satisfy b − c = err_B − err_A, then re-checked with statsmodels.
* For E-DDQN versus the random forest the table is b = {{PairDOneRFb}}, c = {{PairDOneRFc}}.
* Sample-level McNemar tests treat autocorrelated 1-Hz samples as independent. We therefore report a paired group bootstrap of the cost difference as the primary inference.

**R2.5 — Unverified citations, in particular 93.5 % accuracy and ~35 ms latency for [2].**
* Every reference was checked (`reports/06_reference_verification.md`).
* Kundu et al. exists (arXiv:2503.13419; IEEE TDSC 22(6):6040–6057). We could not find the 93.5 % accuracy or the ~35 ms latency in any accessible source, and both numbers are removed.
* Its abstract-level summaries report about 90 % and 94 % detection accuracy on two datasets, one of which appears to be the same UFFCSData release. We now cite the paper only qualitatively.
* TruVR and LiteVR were cited with wrong accuracies (91.3 % and 89.7 %); the papers report 94.10 % on gameplay data (99.75 % on physiological data) and about 94 %, respectively. These are corrected.
* Nine references could not be found: Nair 2023, the "MAC" paper with the stated authors, Ma 2024, Kourtesis 2024, Qu 2022, Ubeysinghe 2024, Valluripally 2023, Naeem 2025 and Karapiperis 2025. They were removed.
* Related verified work was added, including Lin et al. 2020, a DQN classifier with class-asymmetric rewards, which qualifies our novelty claim.

**R2.6 — Dataset provenance and reproducibility.**
* Sec. III-A now cites UFFCSData and describes the curated release, label, prevalence and grouping.
* Data provenance, a full feature dictionary, learned preprocessing parameters, search spaces, selected configurations and per-fold results are in the Supplement.
* `revision/run_all.sh` regenerates everything from the raw XML files.

---

## Issues that cannot be resolved with the available data

1. Participant-level independence cannot be verified because no participant IDs exist. Linkage groups are conservative, but a participant who answered the questionnaire differently in non-consecutive sessions cannot be detected.
2. Physically validated adversarial attacks cannot be evaluated: the data contain no attacked sessions and no measurement of the effect of any manipulation. FOV manipulation cannot be tested at all.
3. Genuine sequential control (an alarm that changes future states) cannot be evaluated offline.
4. With {{nGroupsEval}} independent groups, confidence intervals are wide. Even the best model's cost CI ({{RFCICostLo}}–{{RFCICostHi}}) includes the cost of always alarming ({{AlwaysCost}}).
5. The submitted 41-feature files, baseline, ablation and multi-seed code were not available, so the submitted numbers could only be reproduced by proxy.
