# IEEE Access submission readiness: shortened manuscript (v2)

**Upload bundle:** `submission_ieee_access/` (zipped: `submission_ieee_access.zip`). It is built by `scripts/17_ieee_access_bundle.py`, which:
- compiles `main.tex` on its own in an empty directory; and
- fails unless the result has the same text as `paper/main_access_v2.pdf`.

**Where the requirements come from.** The official IEEE Access site (ieeeaccess.ieee.org) and the IEEE template selector cannot be reached from this environment: DNS fails for the fetch tool and the proxy returns 403. The requirements below come from search-result extracts of the official **IEEE Access Submission Checklist** (PDF dated 2025-09) and the official IEEE 2026 APC list. Items marked "(unconfirmed)" come from secondary sources only.

## Requirements and status

| # | Requirement | Status |
|---|---|---|
| 1 | Double-column, single-spaced, using the required IEEE Access template | Done, but with a provisional 2019 copy of `ieeeaccess.cls` (third-party redistribution). **Action: replace it with the current official template from the IEEE Author Center.** `main.tex` should compile unchanged; recheck the layout afterwards. |
| 2 | Word or LaTeX file plus a PDF, with exactly matching content | Done. Single-file `main.tex` (all `\input`s and the bibliography inlined) plus `Manuscript.pdf` compiled from it. Text identity is checked by the script. |
| 3 | Files no larger than 40 MB | Done: about 1.8 MB in total. |
| 4 | No page limit; under 20 pages recommended; over 20 pages needs a pre-submission inquiry to the EIC | Done: 15 pages including references and biographies. |
| 5 | Abstract of 150–250 words, one paragraph, no displayed equations or references (secondary sources add "self-contained") | Done: about 245 words, one paragraph, no references or equations. |
| 6 | Abbreviations and acronyms defined at first use in the article, even if already defined in the abstract | Done: E-DDQN, RL, DQN, E-CB, CS-MLP, LogReg, HGB, RF, ROC-AUC, PR-AUC, MCC, CI, SD, OOF, SHAP, EEG and CSPQ are defined at first use. Fig. 1's caption defines the abbreviations it uses. The section heading no longer contains "MDP". Guarded by the consistency check. |
| 7 | Index terms (keywords) | Done: 8 terms, in alphabetical order. Consider checking them against the IEEE Taxonomy. |
| 8 | Short biographies for ALL authors at submission, below the references | **Not done (author input).** Five red placeholders. Photographs: placeholder boxes; at submission they may be optional (unconfirmed). |
| 9 | Figures cited in order, legible, vector where possible | Done. Five figures, all vector PDF, cited in order 1–5. Tables are cited in order 1–5. |
| 10 | IEEE reference style | Done: IEEEtran.bst; 55 references, all cited. |
| 11 | Data/code availability, ethics, conflict of interest, funding, generative-AI disclosure | Sections present. **Author input:** archive DOI, ethics ruling, AI-use version and period, CRediT roles. |
| 12 | ORCID for the submitting author (unconfirmed) | **Author action** in ScholarOne. |
| 13 | Graphical abstract | Requested after acceptance (660×295 px JPG, < 45 KB, caption ≤ 60 words). Not needed now; Fig. 1 or Fig. 3 could be adapted. |
| 14 | Article processing charge | US$2,160 (IEEE 2026 APC list, via search; members get a discount). Payable on acceptance. |
| 15 | Supplementary material | Done: `Supplementary_Material.pdf`, cited as "Supplementary Sec. S…", to upload as a supplementary file. |
| 16 | Cover letter | Draft: `Cover_letter_draft.md`, filled from the paper's numbers. Complete the [bracketed] items (date, archive DOI, originality statement, optional reviewers). |

## Content double-check (scientific)

**Automated checks**
- `scripts/08_consistency_check.py`: **all checks pass**. For v2 it also guards:
  - overstatements;
  - required caveats in every section;
  - all equation, figure, table and algorithm labels;
  - the settings table against `configs/protocol.json`;
  - supplement cross-references;
  - abbreviation definitions;
  - keyword order;
  - page count.
- `scripts/15_pipeline_verification.py`: 169/169 code-level checks (splits, preprocessing, selection, thresholds, replay buffer).

**Independent critical review of v2:** all 7 must-fix and 13 should-fix findings were addressed.

**Threshold-scale check:** specified before it was run. It does not change any conclusion and is reported as limitation (ix).

**Numbers:** every number comes from generated macros; none is typed by hand.

## Must do before pressing "Submit"

1. Replace `ieeeaccess.cls` and `images/` with the current official IEEE Access template, recompile, and check the layout.
2. Fill in every red placeholder:
   - five biographies (photographs are optional at submission);
   - archive DOI;
   - ethics ruling;
   - CRediT roles;
   - AI-use details;
   - CPU model and memory (Table 1).
3. Deposit the code archive (for example, on Zenodo) to obtain the DOI.
4. Get all co-authors' approval; run a similarity check; proofread.
5. Decide on two optional wording points:
   - the abstract's "pre-specified" (draws specified before being run, but after the primary results);
   - acronyms in the title ("E-DDQN", "DQN"). IEEE style discourages acronyms in titles unless widely known.
