<!-- generated from reports/templates/05_results_template.md by scripts/09_render_docs.py; do not edit -->
# Results of the leakage-free, frozen evaluation

All numbers are generated from `results/tables/*.csv`; the manuscript uses the same values (`manuscript/generated/numbers.tex`).

* Evaluation set: 35 curated sessions, 9,390 one-second samples and 21 linkage groups.
* Splits: 5 outer folds for test and 3 inner folds for validation.
* Repetitions: five seeds per model.
* Primary operating rule: D1, the threshold that minimises the 5:1 cost on pooled inner-validation predictions.

## 1. The submitted numbers are reproduced by leakage

| Protocol (gradient boosting, 21 raw columns) | Accuracy % | Recall % | Spec. % | MCC | ROC-AUC |
|---|---|---|---|---|---|
| Oversample → row split (submitted) | 97.6 | 99.8 | 91.0 | 0.935 | 0.995 |
| Row split, no oversampling | 95.3 | 94.1 | 96.3 | 0.905 | 0.992 |
| Grouped split | 52.2 | 33.6 | 66.9 | 0.005 | 0.523 |

The unmodified submitted E-DDQN script was also run on two proxy splits:

* **Leaky proxy split:** recall 99.2 %, specificity 83.1 %, MCC 0.870.
* **Grouped proxy split:** recall 92.1 %, specificity 7.7 %, MCC -0.004.

Under the leaky protocol, 2,170 of 2,359 positive test rows (92 %) have exact duplicates in the training split.

## 2. Main comparison (rule D1, mean ± SD over 5 seeds)

| Model | Recall % | Spec. % | Cost (5:1) | ROC-AUC | PR-AUC | MCC |
|---|---|---|---|---|---|---|
| **E-DDQN** | 93.4 ± 2.5 | 7.4 ± 2.7 | 0.663 ± 0.048 | 0.538 | 0.483 | 0.016 |
| E-CB (γ = 0) | 97.1 ± 2.9 | 8.4 ± 2.8 | 0.575 ± 0.055 | 0.653 | 0.562 | 0.122 |
| Standard DQN | 95.2 ± 2.7 | 14.5 ± 4.9 | 0.584 ± 0.040 | 0.661 | 0.595 | 0.158 |
| CS-MLP | 99.4 ± 0.7 | 2.8 ± 1.9 | 0.557 ± 0.012 | 0.644 | 0.521 | 0.072 |
| Logistic regression | 99.1 | 8.1 | 0.532 | 0.626 | 0.576 | 0.167 |
| Gradient boosting | 97.0 | 14.6 | 0.543 | 0.692 | 0.593 | 0.197 |
| Random forest | 98.5 ± 0.3 | 18.2 ± 0.7 | **0.491** ± 0.003 | 0.688 | 0.548 | 0.266 |
| Always alarm | 100.0 | 0.0 | 0.558 | – | – | 0 |

Exact confusion matrices of the seed ensembles are in `manuscript/generated/tab_main_D1.tex` (FN/FP) and `results/predictions/`.

Paired group-bootstrap cost differences, E-DDQN minus each model (95 % CI, p):

| Comparison | Difference | 95 % CI | p |
|---|---|---|---|
| vs. random forest | +0.242 | +0.052 to +0.528 | 0.001 |
| vs. gradient boosting | +0.183 | – | 0.035 |
| vs. logistic regression | +0.194 | – | 0.026 |
| vs. CS-MLP | +0.190 | – | 0.039 |
| vs. E-CB | +0.175 | – | 0.014 |
| vs. standard DQN | +0.190 | – | 0.079 |

## 3. Diagnostics

* **Selected γ for E-DDQN:** 0.99, 0.99, 0.99, 0.99, 0.9.
* **Optimism gap** (outer-test minus inner-validation cost at selection): E-DDQN +0.288, E-CB +0.070, DQN +0.065, RF -0.015.
* **Overestimation** (mean greedy Q minus realised discounted validation return): E-DDQN -2.900, DQN +0.393, E-CB +0.088.
* **Largest SHAP attributions of the E-DDQN decision margin:** cum_rot, elapsed_s, speed_mean_sofar, CSPQ VR experience: some, cum_acc_spikes.

## 4. Ablation and reward ratio

See `manuscript/generated/tab_ablation_D1.tex`, `tab_ablation_D0.tex` and `tab_ratio.tex`. The narrative is in the manuscript, Sec. V-G.

## 5. Telemetry-perturbation stress tests

* **Threshold-free robustness:** the largest absolute change in pooled ROC-AUC over all models and whole-session variants is 0.089.
* **Adaptive worst-case evasion, at the D1 operating point:**
  * E-DDQN: recall 90.4 → 82.9 %.
  * E-CB: 96.6 → 78.0 %.
  * Random forest: 98.7 → 90.5 %.
* **Worst-case false-alarm induction:** false-positive rate rises to 94.5–100 % across models.
* **Field of view:** not testable, because it is constant within each game in the data.

## 6. Verdict

* **Safety objective:** near-complete detection with controlled false alarms is not achieved. Cost-optimal operating points alarm on 82–97 % of non-event seconds.
* **E-DDQN vs. standard DQN:** E-DDQN does not outperform the standard DQN.
* **E-DDQN vs. supervised models:** it is significantly worse than the cost-weighted random forest. Its gap to logistic regression, gradient boosting, CS-MLP and E-CB is smaller but also significant under the group bootstrap (p values in the table above).
* **Contextual-bandit variant:** E-CB (γ = 0) performs better than E-DDQN, consistent with the formal analysis.
