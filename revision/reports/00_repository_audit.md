# Phase 1 — Repository, provenance and original-pipeline audit

Generated from `scripts/01_audit_original.py` (outputs in `results/audit/`).
All original files are preserved unmodified at the repository root; every
revision artefact lives under `revision/`.

## 1. What the repository actually contains

| Item requested / expected | Present? | Notes |
|---|---|---|
| Raw dataset | **Yes** | `UFFCSData-master_raw_source/` (AGPL-3.0): 74 raw session exports (`RAW_DATABASE`), the dataset authors' curated release of 35 sessions (`DATABASE_SELECTED_DATA`), `dataset.csv`, three Weka `.arff` files, and the Unity data-collector build (Windows binaries). |
| Source code of the submitted model | **Yes** | `DRL_cybersickness_FAST_v2.py` (540 lines). |
| Manuscript | **Yes (PDF only)** | `Manuscript (2).pdf`, 16 pages, pdfTeX output. **No LaTeX source**, so the revised manuscript was rebuilt from the PDF text (`revision/manuscript/`). |
| Preprocessing scripts | **No** | No script producing the 41-feature `X_train.csv / X_val.csv / X_test.csv` exists. |
| Processed train/val/test CSVs | **No** | The submitted script reads them from the working directory; they are not in the repository. |
| Trained models, logs, result spreadsheets, figures | **No** | None of `TrainedModel_FastDQL/`, `Results_FastDQL/` or the figure sources are present. |
| Standard-DQN baseline code, ablation code, multi-seed / McNemar code, classical baselines | **No** | Only the E-DDQN script exists. |
| Supplementary material | **No** | Not present; a new supplement was written (`revision/supplementary/`). |
| Reviewer reports | **No** | Reviewer concerns were taken from the task description. |

Consequence: the published numbers **cannot be reproduced exactly**, and
every result in the manuscript that depends on missing code (baseline,
ablation, five-seed study, McNemar, classical baselines, SHAP ranking) is
unverifiable from the repository.

## 2. Dataset identification and provenance

* The manuscript calls the data "Gaze-Locomotion Cybersickness Dataset
  (GLCD)" with 20,972 samples and 41 features and gives **no citation**. No
  dataset of that name was found. The repository's data is **UFFCSData**
  (Universidade Federal Fluminense; T. Porcino et al.,
  https://github.com/tmp1986/UFFCSData), a race game and a flight game played
  in VR, logged at ~1 Hz, with a participant-reported discomfort level 0–3
  per sample.
* `DATABASE_SELECTED_DATA/<k>/FILE.xml` (k = 1..35) are byte-identical in
  telemetry and labels to 35 of the 37 Dec-2019 raw exports (verified sample
  by sample, `results/audit/provenance.json`).
* `dataset.csv` (9,390 rows, 21 features + label) is **exactly** these 35
  sessions concatenated in lexicographic folder order (1, 10, 11, …), with
  categorical fields integer-coded and **no session identifier**.
* Grade counts in the curated release: 0: 5,243; 1: 2,656; 2: 670; 3: 821.
  The manuscript's 20,972 samples = 4 × 5,243 and its 3,670 training samples
  per grade = 0.7 × 5,243: **every minority grade was oversampled to the size
  of grade 0 (grade 2 by ×7.8) before the 70/15/15 split.** This also
  inverted the class balance: the raw binary prevalence is 44.2 % (Normal is
  the majority), while the manuscript's test set is 75.0 % "Attack".
* Identifiers available: session folder name (game + start time). **No
  participant identifier exists.** Questionnaire profiles show that
  sessions ≠ participants (e.g. an aborted 104-s session followed 108 s later
  by a full session with an identical 9-field profile). See
  `reports/01_data_audit.md` for the conservative linkage groups used.
* Data-quality findings: GameFps = 0 on the first sample of 8 curated
  sessions (start-up artefact); camera rotation is **constant in all 37
  Oct-2019 raw sessions** (logging defect, not present in the curated
  release); FOV, StaticFrame and CameraAutoMovement are constant within each
  game (pure game indicators); acceleration is exactly the per-second speed
  difference.

## 3. Trace of the submitted pipeline

| Stage | Manuscript | What can be traced |
|---|---|---|
| Ingestion | "VR telemetry stream (GLCD, 41 features)" | dataset.csv / XML (21 features). The 41-feature construction is not available. |
| Feature engineering | Fig. 4: 1-s sliding windows (stride 1), mean/std/first difference, "motion-instability index", "acceleration-spike count", "FOV-modulation amplitude", "frame-persistence ratio", one-hot encoding | No code. At 1 Hz, a 1-s window contains one sample. FOV is constant within each game, so an FOV-modulation amplitude is identically 0. Whether spike thresholds used whole-session (future) statistics cannot be determined. |
| Class balancing | not described | Oversampling to 5,243 per grade **before** splitting (reconstructed from the counts). |
| Split | "supplied pre-split into disjoint partitions… no information leaks" | Contradicted: the counts imply oversample-then-split at row level; 1-Hz rows from the same 5-min session (and duplicated rows) fall in train and test. |
| Scaling | robust quartile scaling | Not in the script; unknown whether it was fitted on training rows only. |
| Model / training | E-DDQN | `DRL_cybersickness_FAST_v2.py` (defects in §5). |
| Model selection | "test set evaluated exactly once" | Script scores the test set every 10 episodes (line 383); Table 6, Figs. 7, 10, 13 report test metrics per checkpoint. |
| Baseline, ablation, seeds, McNemar, SHAP ranking | reported | No code. |

## 4. Reproduction

**Exact reproduction is infeasible** (missing 41-feature CSVs and code).
Two proxy reproductions were run with the same 21 `dataset.csv` columns:

| Protocol (HistGradientBoosting, default settings) | Accuracy | Recall | Specificity | MCC | ROC-AUC |
|---|---|---|---|---|---|
| A. Oversample to 5,243/grade, then stratified 70/15/15 row split (**reproduces 14,680 / 3,146 / 3,146 exactly**) | 0.976 | 0.998 | 0.910 | 0.935 | 0.995 |
| B. Row-level random split, no oversampling | 0.953 | 0.941 | 0.963 | 0.905 | 0.992 |
| C. Grouped 5-fold split over session-linkage groups | 0.522 | 0.336 | 0.669 | 0.005 | **0.523** |

Under protocol A, **2,170 of the 2,359 positive test rows (92 %) have an
exact duplicate in the training split**, and all 35 sessions appear in both
splits. A generic tree model reproduces the manuscript's headline numbers
(96.88 % accuracy, 99.53 % recall) without any RL, and collapses to chance
(ROC-AUC 0.52) once the split respects session/participant independence.
The published results are therefore explained by leakage, not by E-DDQN.

The unmodified submitted script was also run on both proxy splits
(`scripts/01b_run_original_proxy.sh`, `results/original_repro/`); see
`reports/05_results.md` §1.

## 5. Defects in the submitted code

| Line(s) | Defect | Severity |
|---|---|---|
| 345, 311 | `s'` = next row of a shuffled chunk (training) / next file row (warm-up): transitions between unrelated samples, no terminal flags, γ = 0.99 bootstraps on noise. | High (invalid MDP) |
| 350–361 | Teacher forcing stores the **label** as the action but the reward of the **random** action: e.g. (Attack, −0.5). Trains the correct action toward the FN penalty. | High |
| 197–201, 154 | Polyak averaging skips BatchNorm buffers; target net (eval mode) uses running mean 0 / var 1 forever. | High |
| 229 | Double-DQN argmax with online net in train mode (dropout, BN-stat pollution). | Medium |
| 383, 400–402 | Test set scored and printed every 10 episodes. | High (test exposure) |
| 302 | Warm-up = min(25,000, 14,680) = 14,680, manuscript says 25,000. | Low (mismatch) |
| 266 | `LEARN_EVERY = 25`, manuscript says 50. | Low (mismatch) |
| 5–12, 273–291, 388–390 | Comments contradict code (2.5:1 / 1.67:1 reward, "accuracy" selection that maximises F1). | Low |
| 35–38 | "Exactly reproducible" claim: `torch.use_deterministic_algorithms` not set; `gather` backward is nondeterministic on GPU. | Low |
| 505–512 | SHAP explains raw Q(s, Attack) (includes V(s)) on only 50 test rows; `check_additivity=False`. | Medium |

## 6. Manuscript inconsistencies and unsupported claims (summary)

* Arithmetic of Tables 7–9 is internally consistent (`results/audit/manuscript_number_check.csv`).
* **McNemar (Sec. V-E) is inconsistent**: with 172 baseline errors and 98
  E-DDQN errors, b − c must equal 74; the printed b = 96, c = 34 gives 62.
  χ² = 28.6 is computed correctly from the printed (impossible) counts.
* "Test evaluated exactly once" vs. per-checkpoint test results (Table 6, Figs. 7, 10, 13).
* "The reward is the only change relative to the baseline" vs. Table 5 (14 differences).
* Baseline described as 2-output (Table 5) and as a native 4-class model (Sec. IV-C).
* Baseline trained 150 episodes with last-episode selection vs. 500 episodes with validation selection for E-DDQN.
* "Rewarding TP 5× more than TN counters majority-class pressure" — Attack *was* the (artificial) majority.
* MCC and F2 called "threshold-independent".
* "Teacher forcing … essentially unchanged" while Table 11 shows removing it improves every metric (consistent with defect 350–361).
* Adversarial framing: no attacked data exist; the "Attack" label is any self-reported discomfort ≥ 1.
* Fig. 4 feature pipeline and Sec. III-B "supplied pre-split" contradict each other; FOV-modulation features cannot vary in this data.
* Citations: 9 of 42 references could not be found or are mis-attributed; several quantitative claims (93.5 % / ~35 ms for [2], 91.3 % TruVR, 89.7 % LiteVR) do not match the sources. See `reports/06_reference_verification.md`.
