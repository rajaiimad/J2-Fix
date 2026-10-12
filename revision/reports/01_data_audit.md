# Phase 2 — Data and preprocessing audit (leakage-free rebuild)

Produced by `scripts/02_preprocessing_audit.py`; every check below is an
executable assertion (the script fails if a leakage test fails). Machine-
readable outputs: `results/preprocessing/`, frozen splits:
`data/processed/outer_folds.csv`, `data/processed/inner_folds.csv`.

## 1. Schema and provenance

| Source | Content | Used for |
|---|---|---|
| `RAW_DATABASE/RAW_DATABASE/DATA_EXPORT_<Game>_<date>/FILE.xml` | 74 sessions, 18,384 samples, one `<Data>` element per ~1 s: 9 questionnaire (CSPQ) fields, 6 session-configuration flags, TimeStamp, CameraFieldOfView, PlayerSpeed, PlayerAcceleration, CameraRotationX/Y/Z, (Dec-2019 only) PlayerPositionX/Y/Z, RegionOfInterest, GameFps, DiscomfortLevel (0–3) | parsed directly |
| `.../VRSQ_FILE.xml` | pre/post VRSQ questionnaire per session | documented, not used (session-level, post-hoc) |
| `DATABASE_SELECTED_DATA/DATABASE/<k>/FILE.xml` | curated release, 35 sessions = 35 of the 37 Dec-2019 raw sessions (verified sample by sample) | **evaluation set** |
| `dataset.csv` | the 35 curated sessions in lexicographic folder order, categorical codes, no session id | only to prove provenance of the manuscript's data |

The label is the participant-reported **discomfort level** logged every
second (0 none … 3 severe). The repository does not document the input
device used to report it. Binary target (unchanged from the manuscript):
`y = 1` iff DiscomfortLevel ≥ 1 ("cybersickness event"). It is **not** an
attack label.

## 2. Partition of the raw sessions by role

| Role | Sessions | Samples | Positives | Grade 0/1/2/3 | Prevalence |
|---|---|---|---|---|---|
| Evaluation (curated release, Dec-2019, seated) | 35 | 9,390 | 4,147 | 5,243 / 2,656 / 670 / 821 | 0.442 |
| Development only (Oct-2019, standing) | 37 | 8,512 | 3,415 | 5,097 / 1,781 / 796 / 838 | 0.401 |
| Unused (Dec-2019, excluded from the release by its authors) | 2 | 482 | 13 | – | – |

The development wave was used **only** to debug code and calibrate the
training budget (`results/dev_calibration/`). Its camera-rotation channels
are constant within every session (logging defect), which is one more
reason it is not mixed with the evaluation data.

Evaluation set by game: Flight 20 sessions / 5,397 samples / prevalence
0.412 (grades 1–3: 2,184 / 40 / 1); Race 15 sessions / 3,993 samples /
prevalence 0.481 (472 / 630 / 820).

## 3. Grouping and independence

* No participant identifier exists. Sessions are linked into
  **conservative linkage groups** (`src/eddqn/grouping.py`): identical
  9-field questionnaire profile, or a restart within 180 s after an aborted
  session (< 200 samples) with ≤ 2 differing fields. Log:
  `results/preprocessing/linkage_log.csv` (26 links in the evaluation set).
* Result: **21 groups** from 35 sessions (largest: 6 Race sessions with an
  identical "female, 18–36, no VR experience, no glasses, left eye" profile;
  one group links a Race and a Flight session pair with identical profiles).
* Groups are the unit of every split. The rule over-merges (it cannot
  separate two people with the same profile), which only makes evaluation
  more conservative. It cannot detect one person who answered the
  questionnaire differently in two non-consecutive sessions; this residual
  risk is stated as a limitation.

## 4. Splits (frozen)

5 outer folds (StratifiedGroupKFold over groups, stratified on
game × label, seed 20261012); within each outer development set, 3 inner
grouped folds for tuning, checkpointing and threshold selection.

| Outer fold | Sessions | Groups | Samples | Positives | Prevalence |
|---|---|---|---|---|---|
| 0 | 9 | 4 | 2,378 | 942 | 0.396 |
| 1 | 5 | 3 | 1,510 | 691 | 0.458 |
| 2 | 9 | 5 | 2,273 | 1,058 | 0.466 |
| 3 | 6 | 4 | 1,615 | 686 | 0.425 |
| 4 | 6 | 5 | 1,614 | 770 | 0.477 |

Every sample of the evaluation set is predicted exactly once, by models
that never saw its linkage group, its session, or its exact questionnaire
profile (`partition_overlap_checks.csv`: session overlap 0, group overlap 0,
identical-profile overlap 0, test feature rows identical to a training row
0, for all five outer folds; inner train/validation and inner-train/outer-
test overlaps asserted empty).

## 5. Preprocessing sequence (all fitted on training rows only)

1. Parse XML; decimal comma/dot normalisation; translate categorical answers.
2. Assign session, game (folder name), linkage group.
3. Binary label `y` (grade ≥ 1).
4. **Split** by linkage group (before any feature that looks at more than one sample).
5. Fit the featurizer on the training rows: imputation value for the
   GameFps = 0 start-up artefact (training median, = 90 in every fold) and the
   acceleration-spike threshold (90th percentile of |acceleration| on training
   rows, = 16 in every fold). The frame-drop threshold (80 fps) is fixed.
6. Compute causal features per session (trailing windows of 5 and 15 s,
   cumulative sums from session start) — 39 telemetry features + 14
   questionnaire indicators.
7. Fit a RobustScaler (median / IQR) on training rows; apply frozen to
   validation and test rows.
8. No oversampling, undersampling or synthetic samples anywhere. Class
   imbalance is handled only inside training (replay composition, loss
   weights) and by validation-selected thresholds.

**Causality test** (`leakage_checks.json`): for 40 random (session, t)
pairs, features of sample t computed from the full session and from the
session truncated at t are identical (max |diff| = 0). **Train-only test**:
tampering with test rows (acceleration ×50 + 999, fps = 0) leaves all learned
parameters and the training/validation matrices bit-identical.

## 6. Retained and removed variables

Retained (definitions in `results/preprocessing/feature_dictionary.csv`):
game indicator, elapsed time, speed, acceleration, |acceleration|, camera
quaternion components, per-second rotation change, fps (artefact-imputed),
region-of-interest one-hot, trailing-window mean/std/delta/max/min/spike-rate/
drop-fraction for speed, |acceleration|, rotation rate and fps (5 s, 15 s),
cumulative rotation, cumulative spikes, cumulative frame drops, running mean
speed; questionnaire indicators (gender, age band, VR experience, glasses,
eye dominance, flicker sensitivity, myopia/astigmatism/hyperopia).

Which subset a model uses (`telemetry`, `telemetry+profile`, `exposure`,
`exposure+profile`) is a hyper-parameter selected on inner validation folds.

Removed:

| Variable | Reason |
|---|---|
| DiscomfortLevel and anything derived from it | label |
| CameraFieldOfView | constant within each game (Race 96.016, Flight 111.755): duplicate of the game indicator; no FOV variation exists in the data |
| StaticFrame, CameraAutoMovement | constant within each game: duplicates of the game indicator |
| HapticFeedback, DegreeOfControl, DofSimulation, Locomotion, UserPosture, UserSymptoms | constant over the whole evaluation set |
| PlayerPositionX/Y/Z | absolute course coordinates; Z grows almost linearly with time in Flight; absent in the Oct-2019 wave; would allow memorising course locations |
| VRSQ scores | measured after the session (future information) |

Audit of the manuscript's engineered features: a 1-s window at 1 Hz holds
one sample, so "per-window mean/std" is undefined; "FOV-modulation
amplitude" is identically zero in this data; the "acceleration-spike count"
and "frame-persistence ratio" are reimplemented causally with a
training-only threshold (spikes) and a fixed physical threshold (frames).

## 7. Data-quality summary (evaluation set)

* Missing values: none. GameFps = 0 on the first sample of 8 sessions (start-up artefact, imputed); 54 samples < 80 fps after start.
* Sampling interval 1.000 s (min 0.68, max 1.31); timestamps strictly increasing in every session.
* Duplicate telemetry rows: 0 within sessions, 0 across sessions.
* Labels: grades 0–3 present; 9 of 35 sessions never positive; labels are nearly monotone within a session (mean 1.1 switches; 7 sessions contain a 1→0 transition); median onset 81.5 s (range 4–294 s).
* Consequence: consecutive samples are strongly dependent; sample-level
  significance tests overstate evidence, so cluster (group) bootstrap is
  used alongside McNemar.

## 8. Remaining limitations

* Participant identity cannot be established; group-level independence is
  the strongest verifiable unit.
* 35 sessions / 21 groups is small; outer-fold estimates are noisy and are
  reported with group-bootstrap confidence intervals.
* The label is a self-report of discomfort, not an attack indicator.
