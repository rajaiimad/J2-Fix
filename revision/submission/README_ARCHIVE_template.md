# Code and data for "{{Title}}"

**Authors:** R. Darabee, M. Muniandy, O. Shindi, C. W. Khuen, E. H. Sumiea.

This archive regenerates every number, table and figure of the paper and its supplementary material from the raw UFFCSData session files. It also contains the saved per-sample predictions, so the results can be checked without retraining any model.

## Contents

| Path | Content |
|---|---|
| `revision/src/eddqn/` | Raw-data parser, session-linkage grouping, causal features, E-DDQN and baseline models, metrics and statistics |
| `revision/scripts/` | Pipeline steps `00_`–`13_` (see below); `08_consistency_check.py` recomputes the reported numbers with independent library implementations |
| `revision/configs/protocol.json` | Evaluation protocol, committed before any model was trained on the evaluation sessions |
| `revision/configs/posthoc.json` | Specification of the post-hoc analyses; the exposure-time baselines, Holm adjustment, always-alarm comparison, grouping sensitivity and cost curves were committed before they were run, later additions are recorded under `review_round_2` and `_later_additions`, and the search-draw sensitivity analysis (`search_draw_sensitivity`) was specified with its decision rules and committed before it was run |
| `revision/configs/attacks.json` | Telemetry-perturbation scenarios |
| `revision/data/processed/` | Outer and inner split tables (session-linkage groups) |
| `revision/results/` | Per-sample predictions (`predictions/*.csv.gz`), metric tables, figures, audits, QC reports |
| `revision/paper/` | LaTeX source and PDF of the paper and its supplement (`paper/supplement/`) |
| `revision/manuscript/generated/`, `revision/supplementary/generated/` | Generated LaTeX tables and macros used by the paper build |
| `UFFCSData-master_raw_source/` | The UFFCSData files needed by the pipeline (see *Data*) |
| `DRL_cybersickness_FAST_v2.py` | The earlier, unpublished E-DDQN implementation. It is run unmodified to reconstruct the oversampling-before-splitting protocol (paper, Section IV-D; supplement, Section S6) |

## Reproduce

Requirements: Python 3.13 and the packages pinned in `revision/requirements.txt`. A CPU is sufficient. A LaTeX distribution with `latexmk` is needed for the PDFs.

```bash
pip install -r revision/requirements.txt
bash revision/run_all.sh --fresh --workers 4   # about 3-3.5 h on 4 CPU cores
```

`--fresh` deletes every generated result and rebuilds everything from the raw XML files:
1. Sanity tests, data audit and the reconstruction of the earlier protocol.
2. Preprocessing and splits.
3. Hyper-parameter search, selection, final evaluation, ablation and reward-ratio runs.
4. Aggregation and SHAP.
5. Post-hoc baselines and analyses, including the search-draw sensitivity analysis.
6. Paper and supplement build.
7. Consistency check.

A clean run of the archived pipeline reproduced all outputs exactly. It covered 142 artefacts, including every per-sample prediction and every reported number (`revision/results/qc/clean_rerun.md`).

To check or rebuild the paper from the included results without retraining:

```bash
python3 revision/scripts/08_consistency_check.py   # independent recomputation of the reported numbers
bash revision/paper/build.sh                       # rebuilds paper/main.pdf and paper/supplement/supplement.pdf
```

Seeds: data splitting 20261012 (outer) and 20261013–20261017 (inner); hyper-parameter search 777 (801–802 for the post-hoc baselines); final training 1000–1004; perturbations 4242; bootstrap 5–7 and 11. Every process runs on CPU with one thread, so the results are deterministic on a given platform. Minor floating-point differences across hardware are possible.

## Data

UFFCSData was collected and released by Porcino et al. (<https://github.com/tmp1986/UFFCSData>) under the GNU AGPL-3.0. Its licence is included in `UFFCSData-master_raw_source/LICENSE`. This archive contains:
- the curated release (`DATABASE_SELECTED_DATA`);
- the raw exports (`RAW_DATABASE`);
- `dataset.csv`, used only for the reconstruction of the earlier protocol.

The game build and the Weka files of the original repository are not included. They are available from the original repository.

## Licence

Code: [to be chosen by the authors, e.g. MIT or GPL-3.0; note that the included UFFCSData files remain under AGPL-3.0].

## Not included

The following are not needed to reproduce the paper and are not part of this archive:
- correspondence with journals;
- internal review notes;
- the earlier manuscript.

## Cite

Please cite the paper (citation to be added on publication) and this archive ([DOI]).
