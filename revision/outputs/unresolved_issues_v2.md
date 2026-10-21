# Unresolved issues (need author decision or information)

## Methodological and reporting issues

1. **Thresholds are chosen and applied on different score scales: RESOLVED (checked).**
   - The issue: each D1 threshold is chosen on single-model out-of-fold (OOF) scores but applied to test scores averaged over three inner models.
   - The check: a post-hoc analysis, committed before it was run (`configs/posthoc.json`, key `threshold_scale_sensitivity`; `scripts/16_threshold_scale.py`), applied the unchanged thresholds to single-model test scores.
   - The result:
     - The seed-mean cost changes by +0.045 to +0.067 for the neural models (E-DDQN +0.054), and by −0.009 to +0.014 for logistic regression, HGB and RF.
     - Averaging narrows score spread by a similar factor for all models (median SD ratio 0.85 for E-DDQN, 0.85–0.93 for the others).
     - The cost ranking of the seven models is unchanged.
   - Conclusion: the scale difference does not explain E-DDQN's weak result. Reported in limitation (ix) and Supplementary Sec. S9.10.
   - Still open: the full-length version (`main_access.tex`) does not mention this point.

2. **The abstract calls the extra search draws "pre-specified".**
   - The draws were specified and committed before they were run, but after the primary results were known.
   - The body text says this precisely. The abstract's single word could be read as "specified before the study".
   - Option: replace it with "specified before being run". The abstract is shared by both versions.

3. **Hardware is not reported.**
   - Table 1 has a red placeholder for the CPU model and memory. The repository records only "four CPU cores, 2.5–3.5 h".
   - Please supply both values.

4. **The batch-norm statistics copy never acted in the reported runs.**
   - It is implemented and shown in Fig. 2, but all selected E-DDQN networks use layer normalization.
   - v2 states this. No action is needed unless you prefer to drop it from the figure.

## Which version to submit

5. **v1 (21 pages) and v2 (15 pages) now differ in wording.**
   - v2 contains the reviewer-driven clarifications listed in the revision report, such as the post-hoc markers, the threshold-scale limitation and the definitions. v1 does not.
   - Numbers and conclusions are the same in both.
   - **Your decision:** choose which version to submit. I recommend v2. If you keep v1, ask me and I will port the clarifications back.

## Formatting and template

6. **The IEEE Access template is a provisional copy.**
   - `ieeeaccess.cls` is a 2019 copy (see `access_template/README.md`), because the official template download was blocked from this environment.
   - Replace it with the current official template before submission.

7. **Page limit and fee are unverified.**
   - IEEE Access's page limit, overlength policy and article-processing charge were not checked on the journal site.

8. **Supplement numbering.**
   - The moved gap table is Supplementary Table S5, located in Sec. S9.2.
   - If the journal requires the supplement as a separate file with its own numbering, re-check the "Supplementary Sec. S9.x" references.

## Still open from earlier rounds

9. **Unverified reference details:** the DOI of VR-LENS, the page numbers of Ahmed et al. (2025), and the UFFCSData licence wording (confirmed only through secondary sources).

10. **Author inputs:**
    - biographies and photographs;
    - DOI of the code archive;
    - ethics ruling;
    - CRediT roles;
    - AI-use statement details;
    - ORCID iDs;
    - co-author approval;
    - similarity check;
    - proofreading.

## Limits of the evidence (unchanged; stated in the paper, not fixable by editing)

- 21 independent groups.
- No verified participant identifiers.
- A single dataset.
- Coarse self-reported labels.
- The search-draw diagnosis does not isolate a single cause.
- The perturbations are synthetic and feature-space only.
