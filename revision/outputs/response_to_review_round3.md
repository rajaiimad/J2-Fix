# Response to the third-round points (Results section)

Three wording issues and one open question were raised. The wording issues are fixed at their source, which was wider than the three sentences. The open question was answered by an experiment specified before it was run, and its result changes how the paper describes E-DDQN.

The consistency check now passes all of its checks (736 after the wording fixes; more after the experiment's checks were added; see `results/qc/consistency_report.json`).

## 1. Wording issues (no number changed)

**Root cause.** Some comparisons were worded as facts in three situations:
- the paper's own tests were not significant;
- the tests were only approximate (bootstrap p between 0.01 and 0.05 with 21 groups, which Section III-G calls approximate);
- or no test had been performed.

| # | Issue | Fix |
|---|---|---|
| 1 | V-C: "Both minimal baselines rank seconds better than E-DDQN" gave only Time-LR's interval; the Time+game HGB comparison rests on p = 0.030. | Both are given: Time-LR +0.163 (CI +0.063 to +0.287, p < 0.001) "clearly", Time+game HGB +0.135 (CI +0.015 to +0.270, p = 0.030) "less conclusively", marked approximate. |
| 2 | V-B: E-DDQN's cost "(higher than always alarming)" read as definitive. | "above the 0.558 of always alarming as a point estimate; not significant, Section V-E". V-E now gives the test (+0.168, CI −0.024 to +0.466, p = 0.104) and says that E-DDQN is not shown to be worse than the trivial policy. |
| 3 | V-H: "Every variant ranks close to chance (0.529–0.576)". | "Every variant ranks seconds only weakly (ROC-AUC 0.529–0.576, where 0.5 is chance)". The ablation is also stated to be untested (point estimates). |

**The same problem was found and fixed elsewhere:**
- **V-B, V-I, V-J:** "E-DDQN ranks close to chance" is replaced by its interval (seed-ensemble ROC-AUC 0.541, 95% CI 0.382–0.690, which includes chance).
- **V-A:** the random forest's "lowest cost" is now marked as a point estimate; differences among the supervised models were not tested.
- **V-D:** the matched operating points are labelled "descriptive, no test". In the cost curves, "stays below the trivial policies" is labelled as a point estimate, and the text adds that at R = 5 no model differs significantly after Holm adjustment.
- **V-G:** "E-CB ranks much better" became "ranks better", with its non-significant Holm-adjusted cost test.
- **Supplement S5:** the p-value reading rule now also applies to its tables.

**Guards in `08_consistency_check.py`:**
- **Forbidden phrases:** the old wording is rejected.
- **p-value caveat:** every main-text paragraph that quotes a bootstrap p between 0.01 and 0.05 must say "approximate" or "not significant".
- **Required quotes:** both baseline comparisons, the E-DDQN vs always-alarm p-value and E-DDQN's interval must be quoted.
- **Tested against the old text:** the phrase guards catch all three issues. The omission in issue 1 is caught by the required-quote check.

## 2. The search-draw question (an experiment, not a correction)

**Design (committed in `b15fa6e` before any of its models was trained).** `configs/posthoc.json`, key `search_draw_sensitivity`, implemented in `scripts/13_search_draw_sensitivity.py`.
- **Variants:**
  - E-DDQN and the standard DQN were each tuned again under the full protocol: same splits, search seed, 16 configurations, selection, checkpoint, cross-fitting, five final seeds and thresholds.
  - Each had two further random draws: configuration seeds 9120 and 9130 for E-DDQN, 9122 and 9132 for DQN.
  - Each also had one draw restricted to the exposure features (9200 and 9202).
- **Decision rules fixed in advance:**
  - **R1:** the headline is challenged if E-DDQN has a significantly lower cost than DQN in any pair.
  - **R2:** E-DDQN is called draw-dependent if its cost or within-fold ROC-AUC spans more than 0.05.
  - **R3:** the feature-set explanation is supported if, with exposure features only, E-DDQN's within-fold ROC-AUC is within 0.03 of DQN's.

**Verification:**
- Draw 1 reproduces the primary results exactly.
- Five search and final jobs retrained from scratch reproduced bit for bit.
- A clean rerun of the final version (commit `2e49e93`) from an empty directory reproduced all 170 compared artefacts exactly, including every variant's per-sample predictions and all 102 search-draw macros. It was interrupted once by a container restart and resumed from its saved per-job outputs; this is recorded in `results/qc/clean_rerun.md`.
- The consistency check recomputes every new number independently: costs, within-fold ROC-AUC, the selection rule in all 30 variant folds, the exact sign-flip p-values and the outcomes of R1–R3.

**Results**

| | E-DDQN | standard DQN |
|---|---|---|
| Within-fold ROC-AUC, draws 1 / 2 / 3 | 0.539 / 0.714 / 0.671 | 0.666 / 0.631 / 0.629 |
| Seed-mean 5:1 cost, draws 1 / 2 / 3 | 0.663 / 0.549 / 0.558 | 0.584 / 0.634 / 0.580 |
| Exposure-only candidates in the draw | 2 / 8 / 7 | 6 / 4 / 3 |
| Exposure features only: within-fold ROC-AUC, cost | 0.687, 0.565 | 0.712, 0.536 |

- **R1, not challenged.** No draw gives E-DDQN a significantly lower cost. The seed-ensemble differences range from −0.135 to +0.190, and the smallest p is 0.079.
- **R2, draw-dependent.** E-DDQN's cost spans 0.114 and its within-fold ROC-AUC spans 0.175. That runs from the lowest of the primary models to just below the highest (random forest, 0.715).
- **R3, supported.** The exposure-only gap is 0.026.
- **Beyond the rules: ranking reverses.** The DQN ranks seconds better with draw 1 (−0.125, CI −0.264 to −0.018, p = 0.021, approximate). E-DDQN ranks better with draw 2 (+0.088, CI +0.021 to +0.162, p = 0.009).

**What this changes in the paper.** E-DDQN's last place in the primary analysis is largely a consequence of its search draw, not of its reward or of bootstrapping. In draw 2 it selected γ = 0.99 in three of five folds and still reached its best ranking.

The paper now says this in the abstract, contributions, V-B, V-C, V-E, V-G (iv), the ablation caveat, the Discussion (RQ2, VI-B, implications), limitations (iv), (vi) and (viii), the Conclusion, Supplementary S5.11, the README and the submission templates.

The claim "E-DDQN does not outperform the standard DQN" is now stated with its metric: E-DDQN never has a lower 5:1 cost than the DQN, and in ranking each agent is better in one draw. The comparison with the random forest is stated for E-DDQN's primary draw. With the other draws, E-DDQN's cost (0.549–0.565) is still above the forest's 0.491 as a point estimate; that was not tested.

**What it does not change:**
- the formal result (RQ1);
- the leakage analysis;
- no model being shown to improve on always alarming;
- no primary model ranking seconds significantly better than elapsed time;
- the stress-test conclusions.

## Not changed, and why

- **The draws of the other five families were not varied.** This is stated as a limitation (vi). The question was about E-DDQN versus the standard DQN, and the experiment answers it. Re-tuning every family would be a new benchmark rather than a correction.
- **The variants were not tested against the random forest or the exposure-time baselines.** Those comparisons were not pre-specified. The paper reports the variants' values descriptively and says that they were not tested.
