# Related-work notes: RL-based and cost-sensitive cybersickness detection

- **Scope:** RL (DQN) classifiers for imbalanced and cost-sensitive detection, how contextual bandits relate to cost-sensitive classification, cybersickness detection on the UFFCSData gameplay data and how it was evaluated, exposure duration as a predictor, and inference with few clusters.
- **Search date:** 2026-10-14. **Submission cutoff:** not yet submitted, so all work up to the search date counts as prior work.
- **Tools:** web search only. Direct page fetches failed (arxiv.org and the other arXiv mirrors are blocked in this environment), so full texts could not be opened. Bibliographic details come from search results that quote catalog pages (PMLR, NSF PAR, RePEc/NBER, DBLP, UCF repository, Springer, PMC).
- **Caveat:** the reviewer is the assistant that helped re-implement the pipeline and draft this manuscript. These notes and the review are a structured self-review, not an independent referee report.

## 1. DQN-based classification (direct predecessors of E-DDQN)

| Work | Core idea | Relevance | Source / status |
|---|---|---|---|
| Lin, Chen, Qi, "Deep reinforcement learning for imbalanced classification," Applied Intelligence 50 (2020); arXiv:1901.01379 | Classification as an "imbalanced classification MDP" solved by DQN; larger reward for minority samples. | Cited as [11]. Later papers describe its episode as ending when a minority-class sample is misclassified. | Search abstract plus secondary descriptions. The original termination wording (Sec. III-A) was **not** read directly. |
| Yang et al., "Deep reinforcement learning for multi-class imbalanced training," Machine Learning 113 (2024), doi 10.1007/s10994-023-06481-z; arXiv:2205.12070 | Dueling + double DQN with a custom reward. The episode ends when a minority-class sample is misclassified or the data are exhausted; terminal flag = 1. | Cited as [12]. **Action-dependent termination** means the action changes the future, so it is not a pure contextual bandit. | Snippets from the journal PDF (d-nb.info mirror) and the arXiv PDF state the rule. |

**Implication for the manuscript.** Discussion VI-B says the contextual-bandit reasoning "applies to other DQN-based classifiers trained on fixed datasets [11], [12]". That needs a qualifier. With misclassification-triggered termination and γ > 0, a minority error also forfeits future value, so the effective cost ratio depends on γ and on the continuation value. E-DDQN, as implemented, does **not** use early termination (terminal only at session end). The phrase "E-DDQN follows this line" should state this difference.

## 2. Contextual bandits and cost-sensitive classification (formal background for RQ1)

| Work | Relevance | Status |
|---|---|---|
| Dudík, Hsu, Kale, Karampatziakis, Langford, Reyzin, Zhang, "Efficient Optimal Learning for Contextual Bandits," UAI 2011 (arXiv:1106.2369) | Reduces contextual bandits to cost-sensitive classification. When the rewards of all actions are revealed, the problem is equivalent to cost-sensitive classification. This is the formal relation behind the manuscript's RQ1 and its full-information replay. | Verified: PMLR listing (R9) and mlanthology. Page numbers conflict between sources (197–216 vs 169–178), so pages are omitted. |
| Elkan 2001 (already cited [17]) | Bayes threshold for asymmetric costs. | Cited. |
| Wang, Kallus, Sun, "The Central Role of the Loss Function in Reinforcement Learning," arXiv:2409.12799 (2024; v3 2025) | Survey that treats cost-sensitive classification as the simplest decision setting: offline learning, no effect on future contexts, full feedback. Shows the regression loss (squared vs BCE vs MLE) affects the efficiency of value-based methods. | Abstract only. **Not cited in the review**: it is not essential and its specific bounds were not checked. |

**Implication.** The equivalence in Section III-D (reward → 1/6 Bayes threshold; logged data → contextual bandit) follows directly from known results. Its value here is in applying it to asymmetric-reward DQN detectors, not in new theory. The manuscript says "we make explicit", which is appropriate, but it should cite the bandit/cost-sensitive-classification reduction literature.

## 3. Cybersickness detection on the gameplay data and its evaluation protocols

| Work | Reported result | Protocol note | Status |
|---|---|---|---|
| Kundu, Islam, Calyam, Hoque, "TruVR," ISMAR 2022, doi 10.1109/ISMAR55827.2022.00096 | EBM accuracy 94.10 % on gameplay data and 99.75 % on physiological data; gameplay data with 22 features and 9,391 samples from 37 participants. | Search summaries report a 70 % / 30 % train/test split for the paper (and the same split in LiteVR). That the split was at sample level (not by participant) is **implied** by the description in samples but not quoted. | Partly verified; the full text could not be opened. **Author action:** confirm Sec. "Experimental setup" before submission. |
| Kundu, Denton, Mongalo, Calyam, Hoque, "Securing VR experiences …," IEEE TDSC 22(6):6040–6057 (2025); arXiv:2503.13419 | Adversarial attacks on DL cybersickness detectors; XAI-guided attack detection; evaluated on Simulation 2021 and Gameplay datasets. | Matches the manuscript's [4]. | Verified via NSF PAR listing. |
| Ahmed, Kundu, Hoque, "Adversarial-VR," arXiv:2512.17029 (2025) | Testbed; MI-FGSM, PGD and C&W attacks. | One search summary says it appeared at ISMAR-Adjunct 2025. The manuscript cites the arXiv version. | ISMAR-Adjunct status **unverified**; worth checking before submission. |
| Porcino et al. (UFFCSData; [18], [24], [25], [33]) | Dataset source; symbolic ML. | n/a | Cited. |
| 2025 EEG cybersickness study (arXiv:2512.20620) | Argues leave-one-subject-out CV is the more rigorous protocol. | Supports the grouping argument. | Snippet only; **not cited** (different modality, published late). |

No source was found that re-evaluates the UFFCSData gameplay data under participant- or session-grouped splits. As far as these searches show, the manuscript's grouped benchmark on this dataset is new.

## 4. Exposure duration as a predictor (context for the elapsed-time baseline)

| Work | Relevance | Status |
|---|---|---|
| Kennedy, Stanney, Dunlap, "Duration and Exposure to Virtual Environments: Sickness Curves During and Across Sessions," Presence 9(5):463–472 (2000) | Exposure duration is positively and linearly related to sickness outcomes; repetition is negatively related. This is a classic result that anticipates the manuscript's finding that elapsed time alone matches the learned detectors. **Not cited in the manuscript.** | Bibliographic record from DBLP and the UCF repository; finding from the UCF abstract. DOI not confirmed, so none is given. |

## 5. Inference with few clusters (context for the 21-group bootstrap)

| Work | Relevance | Status |
|---|---|---|
| Cameron, Gelbach, Miller, "Bootstrap-Based Improvements for Inference with Clustered Errors," Review of Economics and Statistics 90(3):414–427 (2008), doi 10.1162/rest.90.3.414 | Standard cluster-robust inference over-rejects with roughly 5–30 clusters. Pairs-cluster bootstrap was less reliable than the wild cluster bootstrap-t in their simulations. Relevant to the manuscript's percentile pairs-cluster bootstrap over 21 unequal groups. | Verified via NBER, SSRN and RePEc listings. |
| Varma & Simon 2006 (already cited [51]) | Selection optimism under cross-validation. | Cited; verified (PMC1397873). |

## 6. Simpler baselines and open problems

- **Simpler baselines.** The manuscript already includes elapsed-time logistic regression, time+game HGB and trivial policies. A natural further baseline is a population onset (survival) curve per game, which is close to Time+game HGB.
- **Open problems.** No public cybersickness dataset with verified participant IDs and gameplay telemetry was found, and none with in-loop mitigation (needed for a genuine MDP). The labels are self-reports elicited by an undocumented procedure.

## 7. Coverage uncertainty

- Full texts of the arXiv papers could not be opened.
- Venue publications of 2025–2026 cybersickness work may be missing.
- The search for grouped re-evaluations of UFFCSData was limited to two queries.
