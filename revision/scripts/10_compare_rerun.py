"""Compare a clean-state rerun (fresh clone, run_all.sh --fresh) with the
committed results and write results/qc/clean_rerun.md.

Usage: python scripts/10_compare_rerun.py /path/to/clone/revision
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eddqn import RESULTS, REVISION_ROOT  # noqa: E402


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(other: Path):
    rows = []
    # 1. per-sample predictions (numeric comparison; gzip headers contain timestamps)
    for p in sorted((RESULTS / "predictions").glob("*.csv.gz")):
        q = other / "results" / "predictions" / p.name
        if not q.exists():
            rows.append((f"predictions/{p.name}", "MISSING in rerun"))
            continue
        a, b = pd.read_csv(p), pd.read_csv(q)
        same_shape = a.shape == b.shape and list(a.columns) == list(b.columns)
        num = a.select_dtypes("number").columns
        maxdiff = float(np.nanmax(np.abs(a[num].to_numpy(float) - b[num].to_numpy(float)))) if same_shape else np.inf
        same_txt = same_shape and all((a[c].astype(str) == b[c].astype(str)).all() for c in a.columns if c not in num)
        rows.append((f"predictions/{p.name}", f"max |diff| = {maxdiff:.3g}; non-numeric identical: {same_txt}"))
    # 2. every CSV/JSON table
    for p in sorted(list((RESULTS / "tables").glob("*.csv")) + list((RESULTS / "tables").glob("*.json")) +
                    [RESULTS / "selected_configs.json", RESULTS / "hpo_results.csv"] +
                    list((RESULTS / "preprocessing").glob("*")) + list((RESULTS / "audit").glob("*.csv")) +
                    list((RESULTS / "audit").glob("*.json")) + list((REVISION_ROOT / "data" / "processed").glob("*.csv"))):
        rel = p.relative_to(REVISION_ROOT)
        q = other / rel
        if p.is_dir():
            continue
        rows.append((str(rel), "identical (SHA-256)" if q.exists() and sha(p) == sha(q) else
                     ("MISSING in rerun" if not q.exists() else "DIFFERS")))
    # 3. manuscript macros
    ma = json.loads((RESULTS / "tables" / "manuscript_macros.json").read_text())
    mb = json.loads((other / "results" / "tables" / "manuscript_macros.json").read_text())
    diff = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k))
    rows.append(("manuscript macros", f"{len(ma)} macros; {len(diff)} differ" + (f": {diff[:10]}" if diff else "")))
    # 4. generated LaTeX
    for d in ("manuscript/generated", "supplementary/generated"):
        for p in sorted((REVISION_ROOT / d).glob("*.tex")):
            q = other / d / p.name
            rows.append((f"{d}/{p.name}", "identical" if q.exists() and sha(p) == sha(q) else "DIFFERS"))
    n_diff = sum(1 for _, s in rows if ("DIFFERS" in s or "MISSING" in s or
                                         ("max |diff|" in s and not s.startswith("max |diff| = 0;"))))
    pred_bad = [r for r in rows if r[0].startswith("predictions/") and not r[1].startswith("max |diff| = 0;")]
    log = (other.parent.parent / "clean_rerun.log")
    tail = log.read_text().splitlines()[-6:] if log.exists() else []
    md = ["Clean-state rerun: the pushed branch was cloned into an empty directory and `bash revision/run_all.sh --fresh --workers 4` "
          "deleted every generated artefact and regenerated everything from the raw XML files (sanity tests, audits, proxy runs of the "
          "submitted script, preprocessing audit, development calibration, hyper-parameter search, selection, final evaluation, "
          "ablation, reward ratio, aggregation, SHAP, tables, LaTeX builds, consistency check, document rendering).", "",
          f"* Exit status / timing (tail of the log): `{' | '.join(t.strip() for t in tail if t.strip())}`",
          f"* Artefacts compared: {len(rows)}; differing or missing: {n_diff}.",
          f"* Per-sample prediction files with any numeric difference: {len(pred_bad)}.",
          f"* Manuscript macros differing: {len(diff)}.", ""]
    if n_diff:
        md.append("Differences:")
        md += [f"* `{a}`: {b}" for a, b in rows if ("DIFFERS" in b or "MISSING" in b or (b.startswith("max |diff|") and not b.startswith("max |diff| = 0;")))]
    else:
        md.append("Every compared artefact is identical to the committed version (bit-identical CSV/JSON/LaTeX; per-sample scores identical).")
    out = RESULTS / "qc" / "clean_rerun.md"
    out.write_text("\n".join(md) + "\n")
    pd.DataFrame(rows, columns=["artefact", "comparison"]).to_csv(RESULTS / "qc" / "clean_rerun_comparison.csv", index=False)
    print("\n".join(md))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
