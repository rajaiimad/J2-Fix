# Final cross-check of the manuscript and the supplementary material

**Scope.** Both documents were checked against each other and against the code, data and outputs. Six independent audits ran in two rounds:
1. every literal number;
2. cross-document consistency;
3. methods, equations and statistics against the code;
4. claims and references;
5. a re-read of the corrected documents;
6. the mathematics of the new score-scale analysis.

**How findings were handled.** Every finding was re-verified against the code, the data or the commit history before anything was changed. Findings that could not be verified were not acted on; they are listed at the end.

**What changed.** No model, prediction, threshold or previously reported number changed. The results were not rerun to change any finding. One new descriptive analysis was added (Supplementary S5.12, `scripts/14_score_scale.py`); it trains no model.

**Verification.**
- The consistency check passes all of its 1,022 checks (previously 921).
- The code's own sanity tests pass 22 of 22.
- The final version was re-verified against the clean rerun: `results/qc/final_version_verification.md`.

## Substantive corrections

| # | Finding (verified) | Fix |
|---|---|---|
| 1 | **The score scale of the untuned rule D0.** The paper said every model's score estimates P(y=1\|s), so that D0 is the 5:1 Bayes cut-off for all models. This is not true for three cases. Class-balanced replay (E-DDQN, E-CB) and the class-balanced minibatches of the CS-MLP train on a class mix other than the prevalence, so the odds shift by k = ((1−ρ)/ρ)((1−π)/π). The Huber loss with the ±1 reward makes the standard DQN's score nonlinear. | Section III-D now states both effects. The effective cut-off of p̂ ≥ 1/6 on P(y=1\|s) is 0.084–0.157 for E-DDQN (approximate, since its γ is 0.9–0.99), 0.120–0.208 for E-CB, 0.121–0.149 for the balanced CS-MLP, and 0.25 for the DQN at γ = 0. III-F, III-G (rule D0), V-D, V-H (reward ratio: 1/(1+kR)), the Discussion (RQ1, VI-B, implications) and limitation (ix) were updated, and Supplementary S5.12 is new. Rule D1 and the ranking metrics do not use this scale. A reproducible sensitivity analysis rescales every inner model to P(y=1\|s): at most 0.8 % of D1 decisions change, the cost changes by at most 0.007 and ROC-AUC by at most 0.003. |
| 2 | **Provenance.** The Holm adjustment of the always-alarm comparison was not in the committed specification (17f142a). | It is now labelled as added without prior commitment in III-G, limitation (iv), S5 intro, S5.3, the README and `posthoc.json` `_later_additions`. |
| 3 | **Session-level always-alarm result was not reported.** With sessions rather than linkage groups as units, the random forest's advantage over always alarming remains significant after Holm adjustment (p = 0.002, adjusted 0.018). | This is now reported in V-E, S5.3 and the README. "No model is shown to improve on always alarming" is now qualified as "with linkage groups as the unit of inference" in V-D, V-E and the Conclusion. |
| 4 | **"E-DDQN does not have a lower cost than the DQN" across draws.** In draws 2 and 3, E-DDQN's cost was lower as a point estimate. | Changed to "not a significantly lower cost". The ranking reversal is stated with its unadjusted, approximate p-values. |
| 5 | **"Higher cost than the random forest in every outer fold".** This holds only for the seed ensembles: in fold 0 the seed means reverse (0.596 vs 0.598). | Changed to "seed-ensemble cost" in the Introduction, Discussion, Conclusion, README and cover letter. |
| 6 | **Perturbations "all clipped to the observed ranges".** The frame-rate caps of 60 and 45 fps lie below every Flight frame rate (70–94 fps after the first second). | Main text III-H and S4.1 now state the actual bounds. |
| 7 | **S6 said the unit tests guard all six earlier-code defects.** They cover only items 1–3. | Items 4–6 are now described as avoided by design. The SHAP description is also corrected: expected gradients were used in every fold. |
| 8 | **Decision rule R3 was coded one-sided.** | The code is now \|gap\| ≤ 0.03, as specified. The outcome and every output are unchanged. |

## Wording and consistency fixes

- **Qualifiers:**
  - "no primary model" (rather than "no model") ranked seconds significantly better than elapsed time;
  - Time-LR has the highest pooled *seed-mean* values;
  - the exact sign-flip p is no longer called approximate;
  - perturbation effects are quantified (87 % of changes < 0.03, maximum 0.089);
  - the abstract's p-values are tied to the seed-ensemble difference.
- **Corrected descriptions:**
  - event-level alarm percentages are means of per-session fractions;
  - the no-warm-up ablation changes only one fold;
  - unit-test wording;
  - pitfall (i) of the earlier code;
  - the learned-parameter file;
  - LogReg's 12-configuration draw (V-G, Table I);
  - matched operating points (all four recall targets checked).
- **Captions:** Table IV and the S3.2 tables (bold face, ensemble FN/FP), event-level and ROC/PR captions (averaging; AP = PR-AUC).
- **Terminology:** questionnaire indicators are now defined once (called "profile" in feature-set names); seed-ensemble FPR range in V-I.
- **Claims about prior work:** softened to what the cited papers show (rendering attacks "could induce sickness or physical harm"; Kundu et al. cited for attacks on detectors). "To our knowledge" added for the claim about public datasets.
- **References:**
  - VR-LENS is now IUI 2023, pp. 819–834;
  - Porcino 2021's venue is XR in Games, held with ACM IMX 2021;
  - UFFCSData now has a year;
  - PreCYSE now has 8(2):42;
  - Huber (1964) is added for the Huber loss.
- **Highlights and cover letter:** updated to match.

## Remaining problems (not fixable from code or text, or for the authors)

1. **Dataset limits (stated as limitations):**
   - 21 independent groups;
   - no verified participant identifiers;
   - a single dataset.
2. **Search draws:** only E-DDQN and the DQN were re-tuned with further draws. The other five families' rankings may also depend on their draws (limitation vi).
3. **Rule D0:** it remains the protocol's fixed cut-off p̂ ≥ 1/6. Its interpretation is now stated correctly, but the reported D0 numbers are on each model's nominal scale.
4. **Unverified details:**
   - the DOI of VR-LENS (not added);
   - the page numbers of Ahmed et al. 2025 (not added);
   - the UFFCSData licence and Lin et al. 2020's termination rule, confirmed only through secondary sources.
5. **Author items:**
   - journal choice and formatting (the paper is now 19 pages, the supplement 16);
   - DOI of the code archive;
   - ethics statement, CRediT roles, ORCID iDs, AI-use statement;
   - similarity check and proofreading;
   - co-author approval of the revised conclusions.
