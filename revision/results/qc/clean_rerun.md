Clean-state rerun: the pushed branch was cloned into an empty directory and `bash revision/run_all.sh --fresh --workers 4` deleted every generated artefact and regenerated everything from the raw XML files (sanity tests, audits, proxy runs of the submitted script, preprocessing audit, development calibration, hyper-parameter search, selection, final evaluation, ablation, reward ratio, aggregation, SHAP, tables, LaTeX builds, consistency check, document rendering).

* Exit status / timing (tail of the log): `wrote reports/07_quality_control.md | real	170m47.606s | user	585m8.472s | sys	2m3.134s | EXIT 0`
* Artefacts compared: 90; differing or missing: 0.
* Per-sample prediction files with any numeric difference: 0.
* Result macros differing: 0 (wall-clock timing macros, which are not used in the text, are excluded: ['DQNMeanSeconds', 'ECBMeanSeconds', 'EDDQNMeanSeconds']).

All result-bearing artefacts reproduce: every per-sample score is identical, 62 files are byte-identical and 7 are identical in content (their only differences are wall-clock timing fields, which naturally vary between runs, and column order in `hpo_results.csv`). Details: `results/qc/clean_rerun_comparison.csv`.
