# Frontier notes: cybersickness detection, RL-for-classification, adversarial VR

## Scope

* **Paper reviewed:** "Enhanced Double Deep Q-Network (E-DDQN) with Asymmetric Reward Design Versus Standard Deep Q-Network for Safety-Prioritized Cybersickness Detection in Virtual Reality Under an Adversarial Threat Model: A Comparative Analysis."
  * Uploaded file `main_8.pdf`, 13 pages. It is byte-identical (MD5 `281670e1…`) to `revision/manuscript/main.pdf` on branch `claude/pensive-dirac-m1f2nc`.
  * The supplement `revision/supplementary/supplement.pdf` was also read.
* **Search date:** 2026-10-13.
* **Submission cutoff:** unknown. The text describes itself as a revision of an earlier submission, so work up to late 2025 is treated as available to the authors.
* **Source access:**
  * Web search worked, so the evidence below comes from search-engine records of primary pages: arXiv abstract pages, PMC, mlanthology, IEEE Xplore and the SBC digital library.
  * Direct page fetches failed: DNS for arxiv.org and link.springer.com is blocked in this environment. No full text of the external papers was read.
  * Statements about external papers are therefore limited to what their abstracts or index records say.
* **Confidentiality:** no manuscript text was sent to search; queries used public topic terms only.

## 1. Closest prior work and what it does

| Work | Core idea | Relevance to the manuscript | Source / identifier |
|---|---|---|---|
| Kundu, Denton, Mongalo, Calyam, Hoque, "Securing Virtual Reality Experiences: Unveiling and Tackling Cybersickness Attacks with Explainable AI," IEEE TDSC 22(6):6040–6057 (cited as [3]) | Adversarial input perturbations (abstract-level: small, hard-to-perceive input perturbations; secondary summaries name FGSM/PGD/C&W) that stop cybersickness mitigation from triggering, plus an XAI-guided attack detector. Evaluated on the Simulation 2021 dataset and the **Gameplay** dataset. | The Gameplay dataset is the same UFFCSData race/flight release the manuscript uses. The manuscript cites [3] but does not say that [3] attacked detectors trained on the same data, and does not compare its perturbation stress tests with [3]. | arXiv:2503.13419; IEEE Xplore doc. 11037281; NSF PAR 10647472 (via search records) |
| Ahmed, Kundu, Hoque, "Adversarial VR: An Open-Source Testbed for Evaluating Adversarial Robustness of VR Cybersickness Detection and Mitigation," arXiv:2512.17029 (18 Dec 2025) | Unity testbed: DeepTCN and Transformer detectors trained on MazeSick drive field-of-view tunnelling; MI-FGSM, PGD and C&W attacks; C&W reduces Transformer accuracy about 5.9-fold. | Not cited. Directly relevant to Table I ("Only [2], [3] consider attacks") and to contribution 4. It also closes the loop from detection to field-of-view mitigation, which the manuscript says cannot be tested on UFFCSData. | arXiv abs page (search record). One search record states ISMAR-Adjunct 2025, DOI 10.1109/ISMAR-Adjunct68609.2025.00061, pp. 281–288; a second search could not confirm it. **Venue unverified; cite as arXiv.** |
| Kundu, Islam, Calyam, Hoque, "TruVR" (cited as [22]) | EBM, decision-tree and logistic-regression detectors; 94.10 % accuracy on the Gameplay dataset; 70 %/30 % sample split. | Same dataset, and per the arXiv record a sample-level 70/30 split. The manuscript's Table II shows a row-level split without oversampling gives HGB 95.3 % accuracy, close to TruVR's 94.10 %, whereas grouped evaluation collapses. The manuscript's statement that cited figures come from "their own datasets" is inaccurate for [22] and [3]. | arXiv:2209.05257 (search record) |
| Yang, El-Bouri, O'Donoghue, Lachapelle, Soltan, Eyre, Lu, Clifton, "Deep reinforcement learning for multi-class imbalanced training: applications in healthcare," Machine Learning 113:2655–2674 (2024) | Dueling + double deep Q-learning with a custom class-dependent reward and episode training for imbalanced classification; clinical case studies. | Not cited. Architecturally the closest precedent to E-DDQN (dueling double DQN, asymmetric reward, detection as an RL problem). Relevant to novelty. | DOI 10.1007/s10994-023-06481-z; PMC11065699; mlanthology mlj/2024/yang2024mlj-deep; arXiv:2205.12070 |
| Lin, Chen, Qi, "Deep reinforcement learning for imbalanced classification," Applied Intelligence 2020 (cited as [26]) | DQN with larger rewards for minority-class samples; classification as a sequential decision process. | Already cited; establishes that class-asymmetric rewards for detection are not new (the manuscript says so). | in bibliography |
| Elkan, "The foundations of cost-sensitive learning," IJCAI 2001 (cited as [27]) | Bayes-optimal threshold p* = C_FP/(C_FP + C_FN). | Contribution 1's "proof" reduces to this result once actions do not affect transitions. | in bibliography |
| Porcino et al., Entertainment Computing 2022 (cited as [17]); Porcino, Trevisan, Clua, SBGames XR-in-Games 2021 (cited as [33]) | Dataset creators; symbolic ML (decision trees, RF) on gameplay data. | The search record of the 2022 paper reports 37 subjects. A secondary summary mentions 88 volunteers and a within-subject design across both games (secondary; **not verified**). TruVR's record describes the Gameplay release as 35 participants (26 male, 9 female). | SBC library and ScienceDirect PII S1875952121000707 (search records) |

## 2. Comparable results and protocol differences

* **Prior Gameplay-dataset results** (TruVR 94.10 % accuracy; Kundu et al. TDSC) come from sample-level splits, per the TruVR record. No participant- or session-grouped results on this dataset were found in the search.
* **Manuscript's own results** (grouped nested CV, 9,390 samples, 21 linkage groups):
  * best ROC-AUC 0.692 (HGB) and 0.688 (RF);
  * E-DDQN ROC-AUC 0.538;
  * 5:1 cost: RF 0.491 vs always-alarm 0.558; E-DDQN 0.663.
* **Comparability:** none of the external numbers are comparable to the manuscript's grouped results, because of the split protocol. The manuscript's Table II reproduces the inflation mechanism.

## 3. Simpler baselines and unresolved problems

* **Elapsed-time / onset-time baseline.** Supplement S1 reports labels close to monotone, a median onset of 82 s, and 9 of 35 sessions never reporting discomfort. Supplement S2.2 shows that 29 of the 35 selected model–fold configurations use the "exposure" or "exposure+profile" feature sets. SHAP ranks cumulative rotation and elapsed time first. A one- or two-feature exposure model is the obvious missing baseline.
* **Personalised vs pooled models.** Search records of an IEEE Access 2023 eye-index study and an NSF-hosted leave-one-out study show that personalisation is an open question. These were not used in the review.
* **Adversarial ML on cybersickness detectors.** Optimisation-based attacks (FGSM/PGD/C&W) exist in [3] and in Ahmed et al. The manuscript's adversary is a selection over 29 fixed physically-motivated perturbations: more interpretable, but weaker.

## 4. Repository facts checked (author-side, not used as external evidence)

From `revision/results/preprocessing/`:

* The curated release contains short aborted sessions followed within minutes by full sessions with identical profiles:
  * G02: 106 rows, then a 302-row session 161 s after its start;
  * G06: 25 rows, then 302 rows;
  * G09: 104 rows, then 302 rows;
  * G18: 53 rows, then 302 rows.
* This supports the manuscript's argument that the 35 curated sessions are not 35 independent participants.
* Group G06 merges 6 Race sessions with a common profile over about 50 minutes. These are plausibly several different people (over-merging).
* Flight positives are almost all grade 1 (2,184 grade-1, 40 grade-2, 1 grade-3 samples). Race has 472 / 630 / 820 samples at grades 1 / 2 / 3.
* The manuscript and supplement do not report this grade distribution.

## 5. Verification log for references used in the review

* **Yang et al., Machine Learning 2024** — VERIFIED (search records only):
  * title, authors, volume 113 and pages 2655–2674 confirmed via PMC11065699, mlanthology and the search result listing the DOI;
  * online 28 Nov 2023, volume year 2024.
* **Ahmed, Kundu, Hoque, arXiv:2512.17029** — PARTIALLY VERIFIED:
  * title, authors and submission date from the arXiv abstract-page search record;
  * venue (ISMAR-Adjunct 2025) reported by one search record and not confirmed by another, so it is cited as an arXiv preprint only.
* **Unverified leads, not cited:**
  * Wiering et al., "Reinforcement learning algorithms for solving classification problems," ADPRL 2011. Only an Academia.edu copy was found; venue page not confirmed.
  * Dudík, Langford, Li, ICML 2011. Verified, but not needed.
