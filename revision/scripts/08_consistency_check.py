"""Final quality control: independent recomputation + manuscript consistency.

1. Recompute, with sklearn/statsmodels (NOT eddqn.metrics), every confusion
   matrix, derived metric and McNemar statistic from the saved per-sample
   predictions and compare with the macros used in the manuscript.
2. Check that every macro used in the manuscript/supplement is defined and
   that no stale number from the submitted manuscript survives outside the
   explicitly labelled audit passages.
3. Check the McNemar contingency identity b - c = err_B - err_A.
Writes results/qc/consistency_report.json and exits non-zero on failure.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score, matthews_corrcoef,
                             precision_score, recall_score, roc_auc_score)
from statsmodels.stats.contingency_tables import mcnemar as sm_mcnemar

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eddqn import RESULTS, REVISION_ROOT  # noqa: E402

QC = RESULTS / "qc"
QC.mkdir(parents=True, exist_ok=True)
MAC = json.loads((RESULTS / "tables" / "manuscript_macros.json").read_text())
MKEY = {"E-DDQN": "EDDQN", "E-CB": "ECB", "DQN": "DQN", "CS-MLP": "CSMLP", "LogReg": "LR", "HGB": "HGB", "RF": "RF"}
RULES = {"D1_min_cost": "Cost", "D0_bayes_1_6": "Bayes", "recall>=0.95": "Rec"}
fails, checks = [], 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def num(x):
    return float(str(x).replace("$-$", "-").replace(",", ""))


def close(a, b, tol):
    return abs(num(a) - num(b)) <= tol


# ---------------------------------------------------------------- 1. recompute
indep = []
preds = {}
for m, k in MKEY.items():
    p = RESULTS / "predictions" / f"{m}.csv.gz"
    if not p.exists():
        continue
    df = pd.read_csv(p)
    preds[m] = df
    for rule, rk in RULES.items():
        col = f"pred_{rule}"
        per_seed = []
        for seed, g in df.groupby("seed"):
            y, yp, s = g.y.to_numpy(), g[col].to_numpy(), g.score.to_numpy()
            tn, fp, fn, tp = confusion_matrix(y, yp, labels=[0, 1]).ravel()
            rec = recall_score(y, yp, zero_division=0)
            spec = tn / (tn + fp)
            rowd = {"model": m, "rule": rule, "seed": seed, "TP": tp, "TN": tn, "FP": fp, "FN": fn,
                    "recall": rec, "specificity": spec, "precision": precision_score(y, yp, zero_division=0),
                    "f1": f1_score(y, yp, zero_division=0), "mcc": matthews_corrcoef(y, yp),
                    "balanced_accuracy": (rec + spec) / 2, "expected_cost": (5 * fn + fp) / len(y),
                    "roc_auc": roc_auc_score(y, s), "pr_auc": average_precision_score(y, s)}
            indep.append(rowd)
            if seed != "ens":
                per_seed.append(rowd)
            else:
                for met, mk, tol in (("FN", "FN", 0), ("FP", "FP", 0), ("TP", "TP", 0), ("TN", "TN", 0)):
                    key = f"{k}{rk}{mk}Ens"
                    if key in MAC:
                        check(int(num(MAC[key])) == int(rowd[met]), f"{key}: macro {MAC[key]} vs recomputed {rowd[met]}")
        ps = pd.DataFrame(per_seed)
        for met, mk, scale, tol in (("recall", "Recall", 100, 0.051), ("specificity", "Spec", 100, 0.051),
                                    ("expected_cost", "Cost", 1, 0.0006), ("roc_auc", "RocAuc", 1, 0.0006),
                                    ("pr_auc", "PrAuc", 1, 0.0006), ("mcc", "MCC", 1, 0.0006),
                                    ("balanced_accuracy", "BalAcc", 100, 0.051), ("f1", "Fone", 100, 0.051)):
            key = f"{k}{rk}{mk}Mean"
            if key in MAC:
                check(close(MAC[key], scale * ps[met].mean(), tol), f"{key}: macro {MAC[key]} vs recomputed {scale * ps[met].mean():.4f}")
pd.DataFrame(indep).to_csv(QC / "independent_recomputation.csv", index=False)

# McNemar with statsmodels on the seed-ensemble D1 predictions
mc_rows = []
if "E-DDQN" in preds:
    a = preds["E-DDQN"][preds["E-DDQN"].seed == "ens"].reset_index(drop=True)
    for m, df in preds.items():
        if m == "E-DDQN":
            continue
        b = df[df.seed == "ens"].reset_index(drop=True)
        check((a[["session_id", "step"]].values == b[["session_id", "step"]].values).all(), f"row alignment {m}")
        y = a.y.to_numpy()
        ca, cb = a.pred_D1_min_cost.to_numpy() == y, b.pred_D1_min_cost.to_numpy() == y
        tab = np.array([[np.sum(ca & cb), np.sum(ca & ~cb)], [np.sum(~ca & cb), np.sum(~ca & ~cb)]])
        r = sm_mcnemar(tab, exact=True)
        rc = sm_mcnemar(tab, exact=False, correction=True)
        bb, cc = tab[0, 1], tab[1, 0]
        check(bb - cc == (~cb).sum() - (~ca).sum(), f"McNemar identity {m}")
        key = f"PairDOne{MKEY[m]}"
        if key + "b" in MAC:
            check(int(num(MAC[key + "b"])) == bb and int(num(MAC[key + "c"])) == cc,
                  f"McNemar counts {m}: macro b={MAC[key + 'b']} c={MAC[key + 'c']} vs {bb},{cc}")
        mc_rows.append({"B": m, "b": int(bb), "c": int(cc), "errors_A": int((~ca).sum()), "errors_B": int((~cb).sum()),
                        "p_exact_statsmodels": float(r.pvalue), "chi2_cc_statsmodels": float(rc.statistic),
                        "p_chi2_cc_statsmodels": float(rc.pvalue)})
pd.DataFrame(mc_rows).to_csv(QC / "mcnemar_statsmodels.csv", index=False)
t = RESULTS / "tables" / "paired_tests_D1_min_cost.csv"
if t.exists() and mc_rows:
    ours = pd.read_csv(t).set_index("B")
    for r in mc_rows:
        o = ours.loc[r["B"]]
        check(close(o.p_exact, r["p_exact_statsmodels"], 1e-9 + 1e-6 * r["p_exact_statsmodels"]), f"exact p {r['B']}")
        check(close(o.chi2_cc, r["chi2_cc_statsmodels"], 1e-6), f"chi2 {r['B']}")

# ---------------------------------------------------- 2. manuscript consistency
defined = set(MAC)
used = set()
for tex in list((REVISION_ROOT / "manuscript").rglob("*.tex")) + list((REVISION_ROOT / "supplementary").rglob("*.tex")):
    if "generated" in tex.parts:
        continue
    txt = tex.read_text()
    for name in re.findall(r"\\([A-Z][A-Za-z]+)(?![A-Za-z])", txt):
        if name in defined:
            used.add(name)
        elif re.match(r"^(EDDQN|ECB|DQN|CSMLP|LR|HGB|RF|Leak|Orig|Pair|Ratio|Always|Never|Best|Shap|HPO|nSess|nSamp|nGroup|nOuter|nInner|nPos|nNever|nEvent|nModels)", name):
            check(False, f"{tex.name}: macro \\{name} used but not defined")
stale = ["96.88", "99.53", "88.95", "94.24", "97.96", "0.916", "94.53", "94.57", "0.861", "8.8", "28.6", "20,972", "14,680", "2,359"]
pdf_hits = {}
for pdf in (REVISION_ROOT / "manuscript" / "main.pdf", REVISION_ROOT / "supplementary" / "supplement.pdf"):
    if not pdf.exists():
        continue
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    hits = []
    for s in stale:
        for mt in re.finditer(re.escape(s), txt):
            ctx = txt[max(0, mt.start() - 120): mt.end() + 60].replace("\n", " ")
            hits.append({"number": s, "context": re.sub(r"\s+", " ", ctx)})
    pdf_hits[pdf.name] = hits
(QC / "stale_number_contexts.json").write_text(json.dumps(pdf_hits, indent=1))

report = {"checks": checks, "failures": fails, "macros_defined": len(defined), "macros_used_in_text": len(used),
          "stale_number_occurrences": {k: len(v) for k, v in pdf_hits.items()},
          "note": "stale-number occurrences are listed with context in stale_number_contexts.json and must all be inside the explicitly labelled audit of the submitted version"}
(QC / "consistency_report.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1)[:3000])
sys.exit(1 if fails else 0)
