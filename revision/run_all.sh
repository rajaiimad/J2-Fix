#!/usr/bin/env bash
# Regenerate every artefact of the revision from the raw UFFCSData XML files.
# Usage: bash revision/run_all.sh [--workers N] [--fresh]
#   --fresh  delete results/runs (all trained-model scores) before running.
# Total CPU time ~10 h on 4 cores (dominated by the RL hyper-parameter search).
set -euo pipefail
cd "$(dirname "$0")"
WORKERS=4; FRESH=0
while [[ $# -gt 0 ]]; do case $1 in --workers) WORKERS=$2; shift 2;; --fresh) FRESH=1; shift;; *) echo "unknown $1"; exit 1;; esac; done
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
[[ $FRESH == 1 ]] && rm -rf results/runs results/selected_configs.json results/hpo_results.csv
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
( cd manuscript && latexmk -pdf -interaction=nonstopmode -quiet main.tex )
( cd supplementary && latexmk -pdf -interaction=nonstopmode -quiet supplement.tex )
python3 scripts/08_consistency_check.py                  # every number in the PDFs traced to results
