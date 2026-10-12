# Results of the leakage-free, frozen evaluation

All numbers are generated from `results/tables/*.csv`; the manuscript uses the same values (`manuscript/generated/numbers.tex`).

* Evaluation set: {{nSessionsEval}} curated sessions, {{nSamplesEval}} one-second samples and {{nGroupsEval}} linkage groups.
* Splits: {{nOuter}} outer folds for test and {{nInner}} inner folds for validation.
* Repetitions: five seeds per model.
* Primary operating rule: D1, the threshold that minimises the 5:1 cost on pooled inner-validation predictions.

## 1. The submitted numbers are reproduced by leakage

| Protocol (gradient boosting, 21 raw columns) | Accuracy % | Recall % | Spec. % | MCC | ROC-AUC |
|---|---|---|---|---|---|
| Oversample → row split (submitted) | {{LeakOldAcc}} | {{LeakOldRecall}} | {{LeakOldSpec}} | {{LeakOldMCC}} | {{LeakOldRocAuc}} |
| Row split, no oversampling | {{LeakRowAcc}} | {{LeakRowRecall}} | {{LeakRowSpec}} | {{LeakRowMCC}} | {{LeakRowRocAuc}} |
| Grouped split | {{LeakGrpAcc}} | {{LeakGrpRecall}} | {{LeakGrpSpec}} | {{LeakGrpMCC}} | {{LeakGrpRocAuc}} |

The unmodified submitted E-DDQN script was also run on two proxy splits:

* **Leaky proxy split:** recall {{OrigOldRecall}} %, specificity {{OrigOldSpec}} %, MCC {{OrigOldMCC}}.
* **Grouped proxy split:** recall {{OrigGrpRecall}} %, specificity {{OrigGrpSpec}} %, MCC {{OrigGrpMCC}}.

Under the leaky protocol, {{LeakDupPos}} of {{LeakTestPos}} positive test rows ({{LeakDupPct}} %) have exact duplicates in the training split.

## 2. Main comparison (rule D1, mean ± SD over 5 seeds)

| Model | Recall % | Spec. % | Cost (5:1) | ROC-AUC | PR-AUC | MCC |
|---|---|---|---|---|---|---|
| **E-DDQN** | {{EDDQNCostRecallMean}} ± {{EDDQNCostRecallSD}} | {{EDDQNCostSpecMean}} ± {{EDDQNCostSpecSD}} | {{EDDQNCostCostMean}} ± {{EDDQNCostCostSD}} | {{EDDQNCostRocAucMean}} | {{EDDQNCostPrAucMean}} | {{EDDQNCostMCCMean}} |
| E-CB (γ = 0) | {{ECBCostRecallMean}} ± {{ECBCostRecallSD}} | {{ECBCostSpecMean}} ± {{ECBCostSpecSD}} | {{ECBCostCostMean}} ± {{ECBCostCostSD}} | {{ECBCostRocAucMean}} | {{ECBCostPrAucMean}} | {{ECBCostMCCMean}} |
| Standard DQN | {{DQNCostRecallMean}} ± {{DQNCostRecallSD}} | {{DQNCostSpecMean}} ± {{DQNCostSpecSD}} | {{DQNCostCostMean}} ± {{DQNCostCostSD}} | {{DQNCostRocAucMean}} | {{DQNCostPrAucMean}} | {{DQNCostMCCMean}} |
| CS-MLP | {{CSMLPCostRecallMean}} ± {{CSMLPCostRecallSD}} | {{CSMLPCostSpecMean}} ± {{CSMLPCostSpecSD}} | {{CSMLPCostCostMean}} ± {{CSMLPCostCostSD}} | {{CSMLPCostRocAucMean}} | {{CSMLPCostPrAucMean}} | {{CSMLPCostMCCMean}} |
| Logistic regression | {{LRCostRecallMean}} | {{LRCostSpecMean}} | {{LRCostCostMean}} | {{LRCostRocAucMean}} | {{LRCostPrAucMean}} | {{LRCostMCCMean}} |
| Gradient boosting | {{HGBCostRecallMean}} | {{HGBCostSpecMean}} | {{HGBCostCostMean}} | {{HGBCostRocAucMean}} | {{HGBCostPrAucMean}} | {{HGBCostMCCMean}} |
| Random forest | {{RFCostRecallMean}} ± {{RFCostRecallSD}} | {{RFCostSpecMean}} ± {{RFCostSpecSD}} | **{{RFCostCostMean}}** ± {{RFCostCostSD}} | {{RFCostRocAucMean}} | {{RFCostPrAucMean}} | {{RFCostMCCMean}} |
| Always alarm | 100.0 | 0.0 | {{AlwaysCost}} | – | – | 0 |

Exact confusion matrices of the seed ensembles are in `manuscript/generated/tab_main_D1.tex` (FN/FP) and `results/predictions/`.

Paired group-bootstrap cost differences, E-DDQN minus each model (95 % CI, p):

| Comparison | Difference | 95 % CI | p |
|---|---|---|---|
| vs. random forest | {{PairDOneRFCostDiff}} | {{PairDOneRFCostLo}} to {{PairDOneRFCostHi}} | {{PairDOneRFPboot}} |
| vs. gradient boosting | {{PairDOneHGBCostDiff}} | – | {{PairDOneHGBPboot}} |
| vs. logistic regression | {{PairDOneLRCostDiff}} | – | {{PairDOneLRPboot}} |
| vs. CS-MLP | {{PairDOneCSMLPCostDiff}} | – | {{PairDOneCSMLPPboot}} |
| vs. E-CB | {{PairDOneECBCostDiff}} | – | {{PairDOneECBPboot}} |
| vs. standard DQN | {{PairDOneDQNCostDiff}} | – | {{PairDOneDQNPboot}} |

## 3. Diagnostics

* **Selected γ for E-DDQN:** {{EDDQNGammas}}.
* **Optimism gap** (outer-test minus inner-validation cost at selection): E-DDQN {{EDDQNOptGap}}, E-CB {{ECBOptGap}}, DQN {{DQNOptGap}}, RF {{RFOptGap}}.
* **Overestimation** (mean greedy Q minus realised discounted validation return): E-DDQN {{EDDQNOverest}}, DQN {{DQNOverest}}, E-CB {{ECBOverest}}.
* **Largest SHAP attributions of the E-DDQN decision margin:** {{ShapTopFive}}.

## 4. Ablation and reward ratio

See `manuscript/generated/tab_ablation_D1.tex`, `tab_ablation_D0.tex` and `tab_ratio.tex`. The narrative is in the manuscript, Sec. V-G.

## 5. Telemetry-perturbation stress tests

* **Threshold-free robustness:** the largest absolute change in pooled ROC-AUC over all models and whole-session variants is {{AttAucMaxAbsChange}}.
* **Adaptive worst-case evasion, at the D1 operating point:**
  * E-DDQN: recall {{EDDQNAttCleanRecall}} → {{EDDQNAttWorstRecall}} %.
  * E-CB: {{ECBAttCleanRecall}} → {{ECBAttWorstRecall}} %.
  * Random forest: {{RFAttCleanRecall}} → {{RFAttWorstRecall}} %.
* **Worst-case false-alarm induction:** false-positive rate rises to {{EDDQNAttWorstFPR}}–100 % across models.
* **Field of view:** not testable, because it is constant within each game in the data.

## 6. Verdict

* **Safety objective:** near-complete detection with controlled false alarms is not achieved. Cost-optimal operating points alarm on {{DOneFPRMin}}–{{DOneFPRMax}} % of non-event seconds.
* **E-DDQN vs. standard DQN:** E-DDQN does not outperform the standard DQN.
* **E-DDQN vs. supervised models:** it is significantly worse than the cost-weighted random forest. Its gap to logistic regression, gradient boosting, CS-MLP and E-CB is smaller but also significant under the group bootstrap (p values in the table above).
* **Contextual-bandit variant:** E-CB (γ = 0) performs better than E-DDQN, consistent with the formal analysis.
