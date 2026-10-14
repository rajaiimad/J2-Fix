<!-- Draft cover letter. Text in [square brackets] must be completed or confirmed by the authors. -->

[Date]

[Editor's name]
Editor-in-Chief, [Journal name]

Dear [Editor's name],

We submit the manuscript **"{{Title}}"** for consideration as an original research article in *[Journal name]*.

Asymmetric-reward reinforcement-learning (RL) detectors have been proposed for safety-prioritized detection, where a missed event is costlier than a false alarm. Our manuscript asks whether such a detector, E-DDQN (a dueling Double Deep Q-Network that penalizes missed cybersickness events five times more than false alarms), improves cybersickness detection in virtual reality under leakage-controlled evaluation. The study uses the public UFFCSData gameplay dataset.

The main findings are:

1. **Formulation.** Applying known results, we show that on logged data the alarm cannot affect future observations. The task is therefore a contextual bandit, and the 5:1 reward induces exactly the decision rule of 5:1 cost-sensitive classification.
2. **Comparison.** Seven models were compared under a nested, session-grouped protocol fixed before testing.
   - E-DDQN did not outperform a standard DQN.
   - It had a higher cost than a cost-weighted random forest in every outer fold, marginally in one (Holm-adjusted p = {{PHHolmRF}} by group bootstrap and {{PHSfRFHolm}} by the more conservative exact sign-flip test).
   - In a post-hoc baseline, no model ranked seconds significantly better than elapsed time alone (ROC-AUC {{PHTimeLRRocAucMean}}).
   - No model combined high recall with a controlled false-alarm rate.
3. **Evaluation protocol.** Session grouping is essential on these data. Random row-level splits, with or without oversampling, give ROC-AUC {{LeakRowRocAuc}}–{{LeakOldRocAuc}}, against {{LeakGrpRocAuc}} under session-grouped splits. This quantifies a known pitfall on this dataset; a reconstruction of the protocol of an earlier, unpublished version of this study yields similarly inflated scores.

We believe the work suits *[Journal name]* because [one or two sentences on the journal's scope, e.g. its interest in rigorous evaluation of machine-learning methods for virtual reality and human–computer interaction]. The paper reports a carefully controlled negative result. It gives practical guidance for evaluating cybersickness detectors: participant- or session-grouped splits, trivial and exposure-time baselines, and comparison of RL detectors with cost-weighted supervised models.

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
