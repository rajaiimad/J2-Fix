#!/usr/bin/env bash
# Assemble a self-contained copy of the generated inputs (macros, tables,
# figures) next to the paper source, then compile it.  Every number comes from
# scripts/05_make_tables.py (primary analysis), scripts/11_posthoc.py (post-hoc
# analyses) or scripts/13_search_draw_sensitivity.py (search-draw sensitivity);
# nothing in paper/generated or paper/figs is edited by hand.
set -euo pipefail
cd "$(dirname "$0")"
R=..
mkdir -p generated figs
cp "$R"/manuscript/generated/*.tex generated/
cp "$R"/results/tables/posthoc/posthoc_macros.tex generated/
cp "$R"/results/tables/posthoc/tab_main_D1_with_posthoc.tex generated/
cp "$R"/results/tables/search_draw/sd_macros.tex generated/
sed -i -e 's/(submitted protocol)/(earlier protocol)/' -e 's/E-DDQN (submitted code)/E-DDQN (earlier code)/' \
       -e 's/Submitted script, submitted protocol (proxy)/Earlier script, earlier protocol (proxy)/' \
       -e 's/Submitted script, grouped split (proxy)/Earlier script, grouped split (proxy)/' generated/tab_leakage.tex
! grep -qi submitted generated/tab_leakage.tex
cp "$R"/results/figures/posthoc_roc.pdf "$R"/results/figures/posthoc_cost_curves.pdf figs/
cp "$R"/results/figures/shap_margin.pdf figs/
latexmk -pdf -interaction=nonstopmode -quiet main.tex >/dev/null 2>&1 || true
grep -E "^!|Overfull|undefined" main.log || echo "main.pdf: no errors, no overfull boxes, no undefined references"

# supplement
mkdir -p supplement/generated supplement/figs
cp "$R"/supplementary/generated/*.tex supplement/generated/
cp generated/*.tex supplement/generated/
cp generated/tab_leakage.tex supplement/generated/          # relabelled copy
cp "$R"/results/tables/posthoc/tab_ph_*.tex supplement/generated/
cp "$R"/results/tables/search_draw/tab_sd_*.tex supplement/generated/
cp "$R"/results/figures/confusion_D1_min_cost.pdf "$R"/results/figures/roc_pr_main.pdf supplement/figs/
(cd supplement && latexmk -pdf -interaction=nonstopmode -quiet supplement.tex >/dev/null 2>&1 || true)
grep -E "^!|Overfull|undefined" supplement/supplement.log || echo "supplement.pdf: no errors, no overfull boxes, no undefined references"
