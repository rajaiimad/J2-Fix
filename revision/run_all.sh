#!/usr/bin/env bash
# Regenerate every artefact of the revision from the raw UFFCSData XML files.
# Usage: bash revision/run_all.sh [--workers N] [--fresh]
#   --fresh  delete every generated artefact (results, splits, generated LaTeX, PDFs, rendered reports) first.
# Wall time ~2-2.5 h on 4 cores (109 and 154 min in two clean reruns; dominated by the RL hyper-parameter search and ablation).
set -euo pipefail
cd "$(dirname "$0")"
WORKERS=4; FRESH=0
while [[ $# -gt 0 ]]; do case $1 in --workers) WORKERS=$2; shift 2;; --fresh) FRESH=1; shift;; *) echo "unknown $1"; exit 1;; esac; done
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
if [[ $FRESH == 1 ]]; then   # remove every generated artefact
  rm -rf results/* data/processed/* manuscript/generated manuscript/figs supplementary/generated supplementary/figs \
         manuscript/main.pdf supplementary/supplement.pdf reports/05_results.md reports/07_quality_control.md \
         reviewer_response/response_to_reviewers.md \
         paper/generated paper/figs paper/main.pdf paper/supplement/generated paper/supplement/figs \
         paper/supplement/supplement.pdf
  mkdir -p results data/processed
fi
python3 scripts/00_sanity_tests.py                      # unit checks of the corrected agent
python3 scripts/01_audit_original.py                    # provenance, leakage reproduction
bash    scripts/01b_run_original_proxy.sh               # unmodified submitted script on proxy splits
python3 scripts/02_preprocessing_audit.py               # splits + leakage assertions (writes data/processed)
python3 scripts/dev_calibration.py                      # development-wave calibration (Oct-2019 only)
FAM="E-DDQN E-CB DQN CS-MLP LogReg HGB RF"
python3 scripts/03_run_protocol.py hpo    $FAM --workers "$WORKERS"
python3 scripts/03_run_protocol.py select $FAM
python3 scripts/03_run_protocol.py final  $FAM --workers "$WORKERS"
python3 scripts/03_run_protocol.py ablation --workers "$WORKERS"
python3 scripts/03_run_protocol.py ratio    --workers "$WORKERS"
python3 scripts/04_aggregate.py
python3 scripts/07_shap.py
python3 scripts/05_make_tables.py                        # LaTeX numbers/tables for manuscript + supplement
# revision manuscript for the original journal (not part of the public archive)
if [[ -f manuscript/main.tex ]]; then ( cd manuscript && latexmk -pdf -interaction=nonstopmode -quiet main.tex ); fi
if [[ -f supplementary/supplement.tex ]]; then ( cd supplementary && latexmk -pdf -interaction=nonstopmode -quiet supplement.tex ); fi
python3 scripts/11_posthoc.py run --workers "$WORKERS"  # post-hoc baselines (configs/posthoc.json)
python3 scripts/11_posthoc.py analyze                    # post-hoc statistics, tables, figures, macros
python3 scripts/13_search_draw_sensitivity.py run --workers "$WORKERS"  # search-draw sensitivity (pre-specified, configs/posthoc.json)
python3 scripts/13_search_draw_sensitivity.py analyze    # its statistics, decision rules, tables, macros
bash    paper/build.sh                                   # new-submission paper + supplement
python3 scripts/08_consistency_check.py                  # every number in the PDFs traced to results
python3 scripts/09_render_docs.py                        # reviewer response, results and QC reports from templates
