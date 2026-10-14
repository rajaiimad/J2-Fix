# Response to the structured pre-submission review (`review_manuscript4.txt`)

Every concern has been addressed in the manuscript and its supplement. The new numbers come from three analyses of the **saved predictions and selected configurations only**. No model was retrained or re-tuned, and no earlier result changed. The analyses are specified in `configs/posthoc.json` under `review_round_2`, are produced by `scripts/11_posthoc.py`, and are labelled in the paper as added after the review.

The consistency check now passes **680 / 680** (previously 621).

## Two findings that changed the paper

1. **An exact group-level sign-flip test is more conservative than the group bootstrap.** For E-DDQN versus the random forest it gives p = 0.014 unadjusted, but 0.083 after Holm adjustment; the group bootstrap gives Holm-adjusted p = 0.006. The direction is the same in every outer fold and in every jackknife replicate. The abstract, results, discussion, conclusion and cover letter now report both tests, and no longer present this comparison as significant at a family-wise 5 % level under every test.
2. **Selected feature sets.** Configurations that include the questionnaire (CSPQ) indicators rank worse. In 4 of 5 outer folds, every selected configuration with the indicators has a lower within-fold ROC-AUC than every configuration without them: mean deviation from the fold mean −0.069 vs +0.041, or −0.056 vs +0.020 without E-DDQN. E-DDQN chose these indicators in all 5 folds. The diagnosis section now presents this exploratory finding alongside bootstrapping and selection optimism.

## Point-by-point

| Concern | Change |
|---|---|
| **3.1** Diagnosis overstated | Contribution 4 is now "exploratory diagnosis". Section V-G is rewritten with three diagnostics, and "none isolates a cause" is stated: (i) bootstrapping, noting that E-CB also chose different features (no questionnaire indicators in 4 of 5 folds) and that the fixed-configuration γ = 0 ablation changes little (ROC-AUC 0.538 → 0.576); (ii) the new questionnaire-indicator association (Supplementary S5.9); (iii) selection optimism, with the near-flat selection criterion (0.42–0.54 vs 0.558) now stated. The conclusion reads "more consistent with noisy validation-based selection of questionnaire-based configurations than with bootstrapping alone". Discussion VI-B is adjusted and limitation (viii) added. |
| **3.2** Scope relative to [11], [12]; novelty of the formal link | Methods III-D now has an "Error-triggered termination" paragraph. [11] and [12] end an episode on a minority-class error, so the action changes the future and the effective cost becomes γ-dependent. E-DDQN does not do this, which is now stated in the Introduction, Related Work and Methods. Discussion VI-B is qualified. Contribution 1 and Table I now say the link is derived "from known results", citing Elkan [17] and Dudík et al. (UAI 2011, added). |
| **3.3** Effective sample size; pooled ROC-AUC | Sections III-G and V-B state that the evidence comes from 35 sessions, 21 groups and 26 onsets, and that per-second metrics mainly reflect when, and in which sessions, discomfort begins. Within-fold ROC-AUC is added (Section V-C; Supplementary S5.7). The random forest ranks slightly above Time-LR within folds (0.715 vs 0.709), so the text now says Time-LR has the highest *pooled* values. E-DDQN remains last (0.539). |
| **3.4** Few-cluster inference | Section III-G cites Cameron, Gelbach and Miller (2008, added) and states that p-values between 0.01 and 0.05 are approximate and that CIs condition on the trained models. The exact sign-flip test (all 2^21 sign patterns) is reported in V-E and Supplementary S5.8, and limitation (i) is extended. |
| **3.5** "Matched" budget | Wording changed to "the same number of configurations". Search-space sizes are given in Section IV-B, Supplementary S2.1 and limitation (vi): E-DDQN 2,985,984, DQN 497,664, E-CB 248,832, CS-MLP 4,608, HGB 1,728, RF 192, LogReg 24. The noisy selection criterion is discussed in V-G. |
| **3.6** Perturbation study too long | RQ3 is reframed as a sanity check. Section III-H is shortened, with values moved to Supplementary S4.1, and V-I is shortened. Table XII moved to Supplementary S4.3. The explanation is also corrected: the old text said insensitivity arose "because the detectors hardly use those channels", but several exposure features are computed from perturbed channels, and a perturbation applied to every test session alike can shift scores without reordering them. The text now says only that unchanged ranking is not evidence of robustness, and points to the fixed-threshold results. The Discussion, Conclusion and Implications are aligned. |
| S6: exposure-duration literature | Kennedy, Stanney and Dunlap (2000) cited in III-F and V-C. |
| S7: "all detectors rely on exposure" | Restricted to the evidence: 29 of 35 selected configurations use exposure feature sets. SHAP is described as covering E-DDQN only, a near-chance model. |
| Table VIII 0.754 vs 0.663 | The caption was wrong ("mean over folds and seeds"). The value is the unweighted mean over folds of the per-fold seed-ensemble cost; the caption now says so and explains the difference from Table IV. |
| Unreadable confusion-matrix figure | Removed from the supplement; the exact counts are in Supplementary S3.1. |
| Ref. [30] ISMAR-Adjunct version | **Not changed:** the proceedings version could not be verified. Left for the authors (checklist). |
| TruVR 70/30 split | Search summaries of the paper report a 70 %/30 % split; the full text could not be opened. Left for the authors to confirm (checklist). |
| Placeholders | Author-side; unchanged. |
| Dense results text | Partly addressed by moving Table XII and shortening Sections III-H and V-I. The paper is 17 pages (was 16) because of the added caveats, diagnostics and references; trim to the journal's limit once it is chosen. |

## Not done, and why

- **No new experiments** (for example, re-tuning E-DDQN without the questionnaire features). Such a run would be a new, post-hoc model selection, and the review did not require it. The feature-set association is reported as exploratory instead.
- **The sign-flip test was added as a sensitivity analysis, not made the primary test.** The primary inference (group bootstrap) was fixed before testing. Both are now reported.
