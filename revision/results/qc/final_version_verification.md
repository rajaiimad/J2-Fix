# Verification of the final version against the clean rerun

The clean rerun of commit `2e49e93` (`clean_rerun.md`) regenerated every artefact from the raw data in an empty directory. Later commits changed the paper text, the references, the implementation of decision rule R3 of the search-draw analysis (`scripts/13_search_draw_sensitivity.py`: `|gap| <= 0.03`, as specified), and added the descriptive `scripts/14_score_scale.py`; no code that trains a model or produces a prediction changed.

To verify the final version, the source files (`revision/src`, `scripts`, `configs`, the paper sources, `run_all.sh`, `README.md`) of the clean clone were updated to the final commit, and every step after model training whose code changed was rerun there: `13_search_draw_sensitivity.py analyze`, `14_score_scale.py` (which first reproduces the saved D1 decisions of E-DDQN, E-CB and the CS-MLP exactly from the clone's own trained runs), `paper/build.sh` and `08_consistency_check.py`.

* Consistency check inside the clone: 1,021 checks, 0 failures.
* Generated result, table and macro files compared (`results/tables/score_scale`, `results/tables/search_draw`, `paper/generated`, `paper/supplement/generated`): 80; identical except `numbers.tex` (twice), which differs only in the wall-clock timing macros `*MeanSeconds`, not used in the text.
* Per-sample predictions of the six search-draw variants: identical content.
* Text of `paper/main.pdf` and `paper/supplement/supplement.pdf` (commit `928c639`): identical.
