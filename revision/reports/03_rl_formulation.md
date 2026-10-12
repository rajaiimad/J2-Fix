# Phase 3 — Is the detector a genuine MDP? Formulation, derivation and corrections

## 1. Objects, as implemented in `src/eddqn/agents.py`

| Element | Definition in the corrected code |
|---|---|
| Episode | One recorded play-through (session) of one game, ~1 Hz, ≤ 303 s. Episodes never share samples and are never concatenated into one transition. |
| State `s_t` | Causal feature vector of the session at second `t` (`src/eddqn/features.py`: trailing windows and cumulative sums over seconds `0..t` of the same session, plus pre-session questionnaire fields when the tuned feature set includes them). |
| Action `a_t` | `0` = stay silent, `1` = raise the cybersickness alarm. |
| Reward `r_t = r(a_t, y_t)` | E-DDQN: TP +0.5, TN +0.1, FN −0.5, FP −0.1 (manuscript Eq. 9). Standard DQN baseline: ±1. |
| Transition | `s_{t+1}` = the next logged second **of the same session**; the last sample of a session is terminal (`done = 1`, no bootstrap). |
| Discount `γ` | Hyper-parameter in {0, 0.5, 0.9, 0.99}, selected on inner validation folds only. |
| Target | Double-DQN: `y = r + γ(1−done) Q_target(s', argmax_a Q_online(s', a))`. |
| Target network | Polyak averaging of parameters **and** copying of BatchNorm running statistics (`τ` tuned); hard copies for the DQN baseline. |
| Replay | Circular buffer; class-balanced (`ρ` Normal / `1−ρ` Attack by true label) for E-DDQN, uniform for DQN. Optional *full-information replay*: the counterfactual action is stored as well, **with its own reward**. |
| Exploration | ε-greedy, ε decays multiplicatively per epoch from 1.0 to 0.01. |
| Checkpoint | Epoch with the lowest achievable 5:1 cost on the inner **validation** groups (tie-break PR-AUC). The outer-test groups are never seen during training or selection. |

## 2. What does the action influence?

The telemetry was logged by the game while participants played. The alarm
did not exist at logging time, so it cannot change any later sample:

  P(s_{t+1} | s_t, a_t) = P(s_{t+1} | s_t)   (exogenous context process)

and the reward depends only on (a_t, y_t). Therefore, for any γ < 1,

  Q*(s, a) = E[r(a, y) | s] + γ · E[ V*(s_{t+1}) | s_t = s ],

where the second term does **not** depend on `a`. Consequences:

1. The optimal policy is the *myopic* policy `π*(s) = argmax_a E[r(a,y)|s]`
   for every γ — i.e. the problem is a **contextual bandit** (one-step
   decision with context `s_t`), not a control problem in which actions
   steer future states.
2. With the asymmetric reward,
   `Q*(s,1) − Q*(s,0) = p(s)·(r_TP − r_FN) − (1 − p(s))·(r_TN − r_FP) = 1.0·p(s) − 0.2·(1 − p(s))`,
   with `p(s) = P(y=1|s)`. The greedy policy alarms iff `p(s) ≥ 0.2/1.2 = 1/6`.
   This is exactly the Bayes rule of cost-sensitive classification with
   misclassification costs `C_FN : C_FP = (r_TP − r_FN) : (r_TN − r_FP) = 5 : 1`
   (Elkan, 2001). The asymmetric reward **is** a 5:1 cost-sensitive
   decision threshold; it is not a different objective.
3. Bootstrapping (γ > 0) adds an action-independent term whose estimation
   noise enters both Q-values; it cannot improve the optimal policy and
   can only help or hurt through estimation effects (e.g. a smoother
   target). Whether it helps here is an empirical question answered on
   validation folds (γ is tuned; γ = 0 is the contextual-bandit case,
   evaluated separately as the "E-CB" model).
4. Because labels are available offline for every sample, the reward of
   **both** actions is known. Learning only from the taken action (bandit
   feedback) discards information; storing both (full-information replay)
   is a valid way to use it and turns Q-learning into a cost-sensitive
   regression of `E[r|s,a]`. It is offered to the tuner as a component.

A genuine MDP would require the alarm to change the future (e.g. a
mitigation that alters rendering and hence later telemetry and symptoms).
No such intervention exists in UFFCSData, and its effect cannot be
evaluated offline without a simulator or a new user study. **We therefore
do not claim that E-DDQN learns adaptive sequential control.** E-DDQN is
evaluated as a value-based learner of a cost-sensitive detection policy,
with episodes and temporal transitions defined consistently with the data.

## 3. Defects of the submitted implementation and their fixes

| # | Submitted code (`DRL_cybersickness_FAST_v2.py`) | Consequence | Fix |
|---|---|---|---|
| 1 | Teacher forcing: reward computed for the random action, but the **true label** stored as the action (lines 349–361). | A random "Normal" on an attack is stored as *(Attack, −0.5)*: the correct action is trained toward the FN penalty and the wrong action never sees it. The manuscript's claim that "the safety incentives of (9) are preserved" was false. | Removed. Optional full-information replay stores each action with **its own** reward (unit-tested). |
| 2 | `s'` = next row of a randomly shuffled batch (line 345); warm-up used file order (line 311). | Transitions linked unrelated samples (often different sessions/participants); γ = 0.99 bootstrapped on noise. | `s'` = next second of the same session; terminal flag at session end. |
| 3 | No terminal flags. | Bootstrapping across episode boundaries. | `done` flag, `(1−done)` in the target. |
| 4 | Polyak update over `parameters()` only (lines 197–201); target net in eval mode. | Target BatchNorm statistics stayed at mean 0 / var 1 forever: the target network computed a different function. | Buffers copied at every update (unit-tested). |
| 5 | Double-DQN argmax computed with the online net in train mode. | Dropout noise in action selection; BN statistics polluted by `s'`. | Computed in eval mode. |
| 6 | Test set scored every 10 episodes and printed during training (line 383). | Test exposure during development. | Outer-test rows are not featurised during HPO; scored once by the frozen final stage. |
| 7 | Warm-up filled `min(25 000, 14 680)` transitions; update interval 25 vs. 50 in the paper. | Script ≠ manuscript. | Warm-up and update schedule are explicit, logged hyper-parameters. |
| 8 | Header comments describing 2.5:1 and 1.67:1 rewards; "accuracy" selection that actually maximised F1. | Misleading documentation. | Rewritten; selection rule stated once in `configs/protocol.json`. |

## 4. Empirical checks (filled in from `results/`; see Section 6 of the QC report)

* numerical stability / Q-value bounds, overestimation (mean Q of the
  greedy action vs. its realised discounted return on validation groups),
* collapse / class bias (alarm rate, all-positive policies),
* sensitivity to initialisation (5 seeds per outer fold),
* the effect of γ (E-DDQN vs. E-CB) and of every component (ablation).

See `reports/05_results.md` for the numbers.
