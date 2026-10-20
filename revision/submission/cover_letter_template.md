<!-- Draft cover letter. Text in [square brackets] must be completed or confirmed by the authors. -->

[Date]

[Editor's name]
Editor-in-Chief, [Journal name]

Dear [Editor's name],

We submit the manuscript **"{{Title}}"** for consideration as an original research article in *[Journal name]*.

Asymmetric-reward reinforcement-learning (RL) detectors have been proposed for safety-prioritized detection, where a missed event is costlier than a false alarm. Our manuscript asks whether such a detector, E-DDQN (a dueling Double Deep Q-Network that penalizes missed cybersickness events five times more than false alarms), improves cybersickness detection in virtual reality under leakage-controlled evaluation. The study uses the public UFFCSData gameplay dataset.

The main findings are:

1. **Formulation.** Applying known results, we show that on logged data the alarm cannot affect future observations. The task is therefore a contextual bandit, and the 5:1 reward induces exactly the decision rule of 5:1 cost-sensitive classification; in practice, class-balanced replay shifts the operating point actually learned.
2. **Comparison.** Seven models were compared under a nested, session-grouped protocol fixed before testing.
   - E-DDQN did not have a significantly lower 5:1 cost than a standard DQN, with its primary random search draw or with two further draws specified before they were run; in ranking, the standard DQN was better with the primary draw (unadjusted p = {{SDPairOneAucP}}, approximate) and E-DDQN with another (p = {{SDPairTwoAucP}}).
   - E-DDQN's own result depended strongly on its search draw (within-fold ROC-AUC {{SDEDDQNWfMin}}–{{SDEDDQNWfMax}}), which suggests that sensitivity to the search draw contributes substantially to its weak primary result; the experiment does not isolate a single cause, and it does not show a benefit of the asymmetric reward.
   - With its primary draw its seed-ensemble cost was higher than that of a cost-weighted random forest in every outer fold, marginally in one ({{PHEnsEDDQNCost}} vs {{PHEnsRFCost}}); the difference was significant under the primary group bootstrap (Holm-adjusted p = {{PHHolmRF}}) but not under the exact sign-flip sensitivity test ({{PHSfRFHolm}}), so it is not firmly established.
   - In a post-hoc baseline, no primary model ranked seconds significantly better than elapsed time alone (ROC-AUC {{PHTimeLRRocAucMean}}).
   - No model combined high recall with a controlled false-alarm rate.
3. **Evaluation protocol.** Session grouping is essential on these data. Random row-level splits, with or without oversampling, give ROC-AUC {{LeakRowRocAuc}}–{{LeakOldRocAuc}}, against {{LeakGrpRocAuc}} under session-grouped splits. This quantifies a known pitfall on this dataset; a reconstruction of the protocol of an earlier, unpublished version of this study yields similarly inflated scores.

We believe the work suits *[Journal name]* because [one or two sentences on the journal's scope, e.g. its interest in rigorous evaluation of machine-learning methods for virtual reality and human–computer interaction]. The paper reports a carefully controlled negative result. It gives practical guidance for evaluating cybersickness detectors: participant- or session-grouped splits, trivial and exposure-time baselines, and comparison of RL detectors with cost-weighted supervised models over more than one random search draw.

All code, the pre-specified protocol, the per-sample predictions and the scripts that regenerate every number, table and figure from the raw data are archived at [DOI]. A clean rerun of the final version from an empty directory reproduced every reported result exactly.

On behalf of all authors, I confirm the following:
- The manuscript is original. It has not been published and is not under consideration elsewhere. [Confirm. If an earlier version was submitted to another journal, it must have been withdrawn or rejected before this submission.]
- All authors have approved the submission.
- The authors declare no conflict of interest.
- The use of an AI assistant is disclosed in the manuscript, in accordance with the journal's policy.

[Optional: suggested reviewers with affiliations and e-mail addresses, and any opposed reviewers.]

Thank you for considering our manuscript.

Sincerely,

Rajai Darabee (corresponding author)
Faculty of Science, Management & Computing, Universiti Teknologi PETRONAS
32610 Seri Iskandar, Perak, Malaysia
rajai_24006920@utp.edu.my
