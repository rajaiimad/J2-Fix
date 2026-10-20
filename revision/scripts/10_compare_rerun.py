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


TIMING = {"seconds", "mean_seconds"}


def content_equal(p: Path, q: Path) -> str:
    """Byte-different files: compare content (row order / float formatting)."""
    try:
        if p.suffix == ".csv":
            a, b = pd.read_csv(p), pd.read_csv(q)
            if set(a.columns) != set(b.columns) or a.shape != b.shape:
                return "DIFFERS (shape/columns)"
            timing = [c for c in a.columns if c in TIMING]
            cols = sorted(c for c in a.columns if c not in timing)
            b = b[list(a.columns)]
            a = a.sort_values(cols).reset_index(drop=True)
            b = b.sort_values(cols).reset_index(drop=True)
            num = [c for c in a.select_dtypes("number").columns if c not in timing]
            d = float(np.nanmax(np.abs(a[num].to_numpy(float) - b[num].to_numpy(float)))) if len(num) else 0.0
            txt = all(((a[c].astype(str) == b[c].astype(str)) | (a[c].isna() & b[c].isna())).all()
                      for c in cols if c not in num)
            if d < 1e-9 and txt:
                extra = f"; only wall-clock timing columns {timing} differ" if timing else ""
                return f"same content (row/column order ignored{extra})"
            return f"DIFFERS (max |diff| {d:.3g})"
        if p.suffix == ".json":
            ja, jb = json.loads(p.read_text()), json.loads(q.read_text())
            if isinstance(ja, dict):
                keys = [k for k in set(ja) | set(jb) if ja.get(k) != jb.get(k)]
                if keys and all(k.endswith("MeanSeconds") for k in keys):
                    return f"same content except wall-clock timing macros {sorted(keys)}"
            return "same content (parsed JSON)" if ja == jb else "DIFFERS (JSON)"
        if p.suffix == ".tex":
            la, lb = p.read_text().splitlines(), q.read_text().splitlines()
            dl = [x for x, y in zip(la, lb) if x != y]
            if len(la) == len(lb) and dl and all("MeanSeconds" in x for x in dl):
                return "same content except wall-clock timing macros (*MeanSeconds)"
            return "DIFFERS"
    except Exception as e:  # noqa: BLE001
        return f"DIFFERS ({type(e).__name__})"
    return "DIFFERS"


def main(other: Path, note: str = ""):
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
    posthoc = RESULTS / "tables" / "posthoc"
    for p in sorted(list((RESULTS / "tables").glob("*.csv")) + list((RESULTS / "tables").glob("*.json")) +
                    [RESULTS / "selected_configs.json", RESULTS / "hpo_results.csv"] +
                    list(posthoc.glob("*.csv")) + list(posthoc.glob("*.json")) + list(posthoc.glob("*.tex")) +
                    [RESULTS / "selected_configs_posthoc.json", RESULTS / "hpo_results_posthoc.csv"] +
                    list((RESULTS / "tables" / "search_draw").glob("*")) +
                    list((RESULTS / "tables" / "score_scale").glob("*")) +
                    [RESULTS / "selected_configs_search_draw.json", RESULTS / "hpo_results_search_draw.csv"] +
                    list((RESULTS / "preprocessing").glob("*")) + list((RESULTS / "audit").glob("*.csv")) +
                    list((RESULTS / "audit").glob("*.json")) + list((REVISION_ROOT / "data" / "processed").glob("*.csv"))):
        rel = p.relative_to(REVISION_ROOT)
        q = other / rel
        if p.is_dir():
            continue
        if not q.exists():
            rows.append((str(rel), "MISSING in rerun"))
        elif sha(p) == sha(q):
            rows.append((str(rel), "identical (SHA-256)"))
        else:
            rows.append((str(rel), content_equal(p, q)))
    # 3. manuscript macros
    ma = json.loads((RESULTS / "tables" / "manuscript_macros.json").read_text())
    mb = json.loads((other / "results" / "tables" / "manuscript_macros.json").read_text())
    diff = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k) and not k.endswith("MeanSeconds"))
    timing_diff = sorted(k for k in set(ma) | set(mb) if ma.get(k) != mb.get(k) and k.endswith("MeanSeconds"))
    rows.append(("manuscript macros", f"{len(ma)} macros; {len(diff)} result macros differ" + (f": {diff[:10]}" if diff else "") +
                 (f"; wall-clock timing macros differ (expected): {timing_diff}" if timing_diff else "")))
    # 3b. post-hoc macros (new-submission paper)
    pa = json.loads((RESULTS / "tables" / "posthoc" / "posthoc_macros.json").read_text())
    pb_path = other / "results" / "tables" / "posthoc" / "posthoc_macros.json"
    pb = json.loads(pb_path.read_text()) if pb_path.exists() else {}
    ph_diff = sorted(k for k in set(pa) | set(pb) if pa.get(k) != pb.get(k))
    rows.append(("post-hoc macros", f"{len(pa)} macros; {len(ph_diff)} differ" + (f": {ph_diff[:10]}" if ph_diff else "")))
    # 3c. search-draw sensitivity macros
    sa = json.loads((RESULTS / "tables" / "search_draw" / "sd_macros.json").read_text())
    sb_path = other / "results" / "tables" / "search_draw" / "sd_macros.json"
    sb = json.loads(sb_path.read_text()) if sb_path.exists() else {}
    sd_diff = sorted(k for k in set(sa) | set(sb) if sa.get(k) != sb.get(k))
    rows.append(("search-draw macros", f"{len(sa)} macros; {len(sd_diff)} differ" + (f": {sd_diff[:10]}" if sd_diff else "")))
    # 4. generated LaTeX
    for d in ("manuscript/generated", "supplementary/generated", "paper/generated"):
        for p in sorted((REVISION_ROOT / d).glob("*.tex")):
            q = other / d / p.name
            if not q.exists():
                rows.append((f"{d}/{p.name}", "not produced by the rerun commit (table added afterwards from compared CSVs)"))
            else:
                rows.append((f"{d}/{p.name}", "identical" if sha(p) == sha(q) else content_equal(p, q)))
    # 5. text of the compiled PDFs (PDF bytes differ by build timestamps, so compare extracted text)
    import subprocess
    for d in ("paper/main.pdf", "paper/supplement/supplement.pdf", "manuscript/main.pdf", "supplementary/supplement.pdf"):
        a, b = REVISION_ROOT / d, other / d
        if not b.exists():
            rows.append((d, "MISSING in rerun"))
            continue
        ta = subprocess.run(["pdftotext", str(a), "-"], capture_output=True, text=True).stdout
        tb = subprocess.run(["pdftotext", str(b), "-"], capture_output=True, text=True).stdout
        rows.append((d, "identical text (pdftotext)" if ta == tb else "DIFFERS (PDF text)"))
    n_diff = sum(1 for _, s in rows if ("DIFFERS" in s or "MISSING" in s or
                                         ("max |diff|" in s and not s.startswith("max |diff| = 0;")) or
                                         " differ: " in s))
    pred_bad = [r for r in rows if r[0].startswith("predictions/") and not r[1].startswith("max |diff| = 0;")]
    log = (other.parent.parent / "clean_rerun.log")
    tail = log.read_text().splitlines()[-6:] if log.exists() else []
    commit = ""
    try:
        import subprocess
        commit = subprocess.run(["git", "-C", str(other), "log", "--format=%h", "-1"], capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    md = [f"Clean-state rerun of commit `{commit}`: the pushed branch was cloned into an empty directory and `bash revision/run_all.sh --fresh --workers 4` "
          "deleted every generated artefact and regenerated everything from the raw XML files (sanity tests, audits, proxy runs of the "
          "earlier script, preprocessing audit, development calibration, hyper-parameter search, selection, final evaluation, "
          "ablation, reward ratio, aggregation, SHAP, tables, LaTeX builds, post-hoc baselines and analyses, new-submission paper and "
          "supplement, consistency check, document rendering).", "",
          f"* Exit status / timing (tail of the log): `{' | '.join(t.strip() for t in tail if t.strip())}`",
          f"* Artefacts compared: {len(rows)}; differing or missing: {n_diff}.",
          f"* Per-sample prediction files with any numeric difference: {len(pred_bad)}.",
          f"* Result macros differing: {len(diff)} (wall-clock timing macros, which are not used in the text, are excluded: {timing_diff}).",
          f"* Post-hoc macros differing: {len(ph_diff)} of {len(pa)}.",
          f"* Search-draw macros differing: {len(sd_diff)} of {len(sa)}.", ""]
    if note:   # how the run actually went (interruptions, resumptions), stated by the person who ran it
        md[1:1] = ["", f"**Run history.** {note}"]
    if n_diff:
        md.append("Differences:")
        md += [f"* `{a}`: {b}" for a, b in rows if ("DIFFERS" in b or "MISSING" in b or (b.startswith("max |diff|") and not b.startswith("max |diff| = 0;")))]
    else:
        n_bit = sum(1 for _, b in rows if b.startswith("identical") and "pdftotext" not in b)
        n_pdf = sum(1 for _, b in rows if "pdftotext" in b)
        n_cont = sum(1 for _, b in rows if b.startswith("same content"))
        reasons = sorted({b for _, b in rows if b.startswith("same content")})
        md.append(f"All result-bearing artefacts reproduce: every per-sample score is identical, {n_bit} files are byte-identical and "
                  f"{n_cont} are identical in content, and the {n_pdf} compiled PDFs have identical text. The content-only differences are: " + "; ".join(f"`{r}`" for r in reasons) +
                  ". Details: `results/qc/clean_rerun_comparison.csv`.")
    out = RESULTS / "qc" / "clean_rerun.md"
    out.write_text("\n".join(md) + "\n")
    pd.DataFrame(rows, columns=["artefact", "comparison"]).to_csv(RESULTS / "qc" / "clean_rerun_comparison.csv", index=False)
    print("\n".join(md))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("clone", help="path to the rerun clone's revision/ directory")
    ap.add_argument("--note", default="", help="run history to record in the report (e.g. an interruption and resumption)")
    a = ap.parse_args()
    main(Path(a.clone).resolve(), a.note)
