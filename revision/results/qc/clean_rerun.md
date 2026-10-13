Clean-state rerun of commit `deb2cd9`: the pushed branch was cloned into an empty directory and `bash revision/run_all.sh --fresh --workers 4` deleted every generated artefact and regenerated everything from the raw XML files (sanity tests, audits, proxy runs of the earlier script, preprocessing audit, development calibration, hyper-parameter search, selection, final evaluation, ablation, reward ratio, aggregation, SHAP, tables, LaTeX builds, post-hoc baselines and analyses, new-submission paper and supplement, consistency check, document rendering).

* Exit status / timing (tail of the log): `real	154m25.457s | user	519m1.706s | sys	1m46.138s | EXIT 0 | END Tue Oct 13 18:56:20 UTC 2026`
* Artefacts compared: 142; differing or missing: 0.
* Per-sample prediction files with any numeric difference: 0.
* Result macros differing: 0 (wall-clock timing macros, which are not used in the text, are excluded: ['CSMLPMeanSeconds', 'DQNMeanSeconds', 'ECBMeanSeconds', 'EDDQNMeanSeconds', 'HGBMeanSeconds']).
* Post-hoc macros differing: 0 of 389.

All result-bearing artefacts reproduce: every per-sample score is identical, 107 files are byte-identical and 8 are identical in content, and the 4 compiled PDFs have identical text. The content-only differences are: `same content (parsed JSON)`; `same content (row/column order ignored)`; `same content (row/column order ignored; only wall-clock timing columns ['mean_seconds'] differ)`; `same content (row/column order ignored; only wall-clock timing columns ['seconds'] differ)`; `same content except wall-clock timing macros (*MeanSeconds)`; `same content except wall-clock timing macros ['CSMLPMeanSeconds', 'DQNMeanSeconds', 'ECBMeanSeconds', 'EDDQNMeanSeconds', 'HGBMeanSeconds']`. Details: `results/qc/clean_rerun_comparison.csv`.
