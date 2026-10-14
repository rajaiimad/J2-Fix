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

# ------------------------------------------- 4. post-hoc baselines and new paper
PH_JSON = RESULTS / "tables" / "posthoc" / "posthoc_macros.json"
paper_hits = {}
if PH_JSON.exists():
    PH = json.loads(PH_JSON.read_text())
    for m, k in (("Time-LR", "TimeLR"), ("TimeGame-HGB", "TimeHGB")):
        df = pd.read_csv(RESULTS / "predictions" / f"{m}.csv.gz", dtype={"seed": str})
        per = []
        for seed, g in df[df.seed != "ens"].groupby("seed"):
            y, yp, sc = g.y.to_numpy(), g.pred_D1_min_cost.to_numpy(), g.score.to_numpy()
            tn, fp, fn, tp = confusion_matrix(y, yp, labels=[0, 1]).ravel()
            per.append({"recall": recall_score(y, yp), "spec": tn / (tn + fp), "cost": (5 * fn + fp) / len(y),
                        "auc": roc_auc_score(y, sc), "prauc": average_precision_score(y, sc), "mcc": matthews_corrcoef(y, yp)})
        per = pd.DataFrame(per).mean()
        check(close(PH[f"PH{k}RecallMean"], 100 * per.recall, 0.051), f"PH {k} recall")
        check(close(PH[f"PH{k}SpecMean"], 100 * per.spec, 0.051), f"PH {k} spec")
        check(close(PH[f"PH{k}CostMean"], per.cost, 0.0006), f"PH {k} cost")
        check(close(PH[f"PH{k}RocAucMean"], per.auc, 0.0006), f"PH {k} auc")
        check(close(PH[f"PH{k}PrAucMean"], per.prauc, 0.0006), f"PH {k} prauc")
        check(close(PH[f"PH{k}MCCMean"], per.mcc, 0.0006), f"PH {k} mcc")
        e = df[df.seed == "ens"]
        tn, fp, fn, tp = confusion_matrix(e.y, e.pred_D1_min_cost, labels=[0, 1]).ravel()
        check(int(num(PH[f"PH{k}FN"])) == fn and int(num(PH[f"PH{k}FP"])) == fp, f"PH {k} ensemble FN/FP")
    # seed-ensemble metrics (Table III, right block) and seed-mean vs ensemble cost differences
    ens_cost, mean_cost = {}, {}
    for m, k in list(MKEY.items()) + [("Time-LR", "TimeLR"), ("TimeGame-HGB", "TimeHGB")]:
        df = pd.read_csv(RESULTS / "predictions" / f"{m}.csv.gz", dtype={"seed": str})
        e = df[df.seed == "ens"]
        tn, fp, fn, tp = confusion_matrix(e.y, e.pred_D1_min_cost, labels=[0, 1]).ravel()
        ens_cost[m] = (5 * fn + fp) / len(e)
        mean_cost[m] = np.mean([(5 * ((g.y == 1) & (g.pred_D1_min_cost == 0)).sum() + ((g.y == 0) & (g.pred_D1_min_cost == 1)).sum()) / len(g)
                                for _, g in df[df.seed != "ens"].groupby("seed")])
        check(close(PH[f"PHEns{k}Cost"], ens_cost[m], 0.0006), f"PH ensemble cost {m}")
        check(close(PH[f"PHEns{k}Recall"], 100 * tp / (tp + fn), 0.051), f"PH ensemble recall {m}")
        check(close(PH[f"PHEns{k}Spec"], 100 * tn / (tn + fp), 0.051), f"PH ensemble specificity {m}")
    for m, k in list(MKEY.items()) + [("Time-LR", "TimeLR"), ("TimeGame-HGB", "TimeHGB")]:
        if m == "E-DDQN":
            continue
        check(close(PH[f"PHMeanDiff{k}"], mean_cost["E-DDQN"] - mean_cost[m], 0.0006), f"PH seed-mean cost difference {m}")
        check(close(PH[f"PHEnsDiff{k}"], ens_cost["E-DDQN"] - ens_cost[m], 0.0006), f"PH ensemble cost difference {m}")
        key = f"PairDOne{k}CostDiff"
        if key in MAC:   # Table VI differences are ensemble differences
            check(close(MAC[key], ens_cost["E-DDQN"] - ens_cost[m], 0.0006), f"{key} equals the ensemble difference")
    # number of questionnaire indicators stated in the text equals the number used by the code
    n_prof = int(pd.read_csv(RESULTS / "preprocessing" / "feature_dictionary.csv").feature.str.startswith("prof_").sum())
    ptxt = (REVISION_ROOT / "paper" / "sections" / "s3_method.tex").read_text()
    check(f"{n_prof} CSPQ indicators" in ptxt, f"paper states the number of CSPQ indicators ({n_prof})")
    # Holm adjustment recomputed with statsmodels
    from statsmodels.stats.multitest import multipletests
    hl = pd.read_csv(RESULTS / "tables" / "posthoc" / "paired_tests_holm.csv")
    for rule, g in hl.groupby("rule"):
        adj = multipletests(g.cost_diff_p_cluster_bootstrap, method="holm")[1]
        check(np.allclose(adj, g.p_holm, atol=1e-12), f"Holm {rule}")
    # Methods text vs code: feature counts, perturbation variants, seeds
    from eddqn.attacks import load_attack_config, variants
    from eddqn.features import EXPOSURE
    fdict = pd.read_csv(RESULTS / "preprocessing" / "feature_dictionary.csv")
    n_tele = int((~fdict.feature.str.startswith("prof_")).sum())
    check(f"the {n_tele} telemetry features" in ptxt, f"paper states the number of telemetry features ({n_tele})")
    check(f"\\emph{{telemetry+profile}} ({n_tele + n_prof})" in ptxt, "paper states the size of the telemetry+profile set")
    check(f"\\emph{{exposure}} ({len(EXPOSURE)} " in ptxt and f"\\emph{{exposure+profile}} ({len(EXPOSURE) + n_prof})" in ptxt,
          "paper states the sizes of the exposure feature sets")
    var = variants(load_attack_config())
    n_whole = sum(v["window"] == "whole" for v in var)
    n_stress = sum(v["role"] == "stress" for v in var)
    n_hide = sum(v["role"] == "evasion_only" for v in var)
    check(f"clean + {len(var)} bounded" in ptxt, f"Fig. 1 states {len(var)} perturbation variants")
    check(f"give {n_stress} variants" in ptxt, f"paper states {n_stress} stress variants")
    check(f"the {n_whole} whole-session variants ({n_whole - n_hide} stress scenarios and {n_hide} hiding" in ptxt,
          "paper states the adaptive candidate set")
    check(int(MAC.get("AttAucNVariants", -1)) == n_whole, "Table of threshold-free robustness: number of whole-session variants")
    proto = json.loads((REVISION_ROOT / "configs" / "protocol.json").read_text())
    s0 = proto["split_seed"]
    check(f"outer seed {s0}; inner seeds {s0 + 1}--{s0 + proto['k_outer']}" in ptxt, "paper states the split seeds")
    # Results V-B: best primary-model ROC-AUC (HGB, then RF) and PR-AUC (DQN) as stated in the text
    ms = pd.read_csv(RESULTS / "tables" / "metrics_summary.csv")
    ms = ms[(ms.rule == "D1_min_cost") & ms.model.isin(list(MKEY))]
    check(list(ms.sort_values("roc_auc_mean", ascending=False).model[:2]) == ["HGB", "RF"], "best primary ROC-AUC: HGB, then RF")
    check(ms.loc[ms.pr_auc_mean.idxmax(), "model"] == "DQN", "best primary PR-AUC: DQN")
    # cost curves: the summary numbers quoted in the text
    cc = pd.read_csv(RESULTS / "tables" / "posthoc" / "cost_curves.csv")
    best = cc.loc[cc.relative_cost.idxmin()]
    check(close(PH["PHCcMinAll"], best.relative_cost, 0.006) and best.model == "RF"
          and float(PH["PHCcMinAllRatio"]) == best.ratio, "lowest relative cost over all models and ratios")
    r20 = cc[cc.ratio == cc.ratio.max()].set_index("model").relative_cost
    check(r20["E-DDQN"] > 1 and r20["DQN"] > 1 and r20["RF"] < 1, "relative costs at the largest ratio (text: E-DDQN, DQN above 1)")
    # reward ratio 5:1 reproduces the main E-DDQN run (only when the per-job run files are present)
    rdir = RESULTS / "runs" / "final"
    if (rdir / "RATIO 5").exists():
        import pickle
        same = True
        for p in sorted((rdir / "RATIO 5").glob("*.pkl")):
            a, b = (pickle.loads(x.read_bytes()) for x in (p, rdir / "E-DDQN" / p.name))
            same &= all(np.array_equal(a[k], b[k]) for k in ("val_score", "test_score"))
        check(same, "ratio-5 runs identical to the main E-DDQN runs")
    # review round 2: within-fold ROC-AUC, sign-flip tests, feature-set association, search-space sizes
    import itertools
    import json as _json
    wf = {}
    for m in list(MKEY) + ["Time-LR", "TimeGame-HGB"]:
        df = pd.read_csv(RESULTS / "predictions" / f"{m}.csv.gz", dtype={"seed": str})
        sd_ = df[df.seed != "ens"]
        wf[m] = np.mean([np.mean([roc_auc_score(h.y, h.score) for _, h in g.groupby("outer")]) for _, g in sd_.groupby("seed")])
    check(all(close(PH[f"PHWf{k}Auc"], wf[m], 0.0006) for m, k in list(MKEY.items()) + [("Time-LR", "TimeLR"), ("TimeGame-HGB", "TimeHGB")]),
          "within-fold ROC-AUC macros")
    order = sorted(wf, key=wf.get, reverse=True)
    check(order[:3] == ["RF", "Time-LR", "HGB"] and order[-1] == "E-DDQN", "within-fold ROC-AUC ranking stated in V-C")
    ens = {m: pd.read_csv(RESULTS / "predictions" / f"{m}.csv.gz", dtype={"seed": str}).query("seed == 'ens'")
           .sort_values(["outer", "session_id", "step"]).reset_index(drop=True) for m in ("E-DDQN", "RF")}
    yv, gv = ens["E-DDQN"].y.to_numpy(), ens["E-DDQN"].group_id.to_numpy()
    cvec = {m: 5 * ((e.pred_D1_min_cost.to_numpy() == 0) & (yv == 1)) + ((e.pred_D1_min_cost.to_numpy() == 1) & (yv == 0))
            for m, e in ens.items()}
    D = pd.Series(cvec["E-DDQN"] - cvec["RF"]).groupby(gv).sum().to_numpy(float)
    stats_ = np.array([abs(np.dot(s, D)) for s in itertools.product((1, -1), repeat=len(D))]) if len(D) <= 16 else None
    if stats_ is None:   # exact enumeration in blocks (2^21 patterns) without the shared helper
        head, tail = D[:11], D[11:]
        hs = np.array([np.dot(s, head) for s in itertools.product((1, -1), repeat=len(head))])
        ts = np.array([np.dot(s, tail) for s in itertools.product((1, -1), repeat=len(tail))])
        p_sf = float((np.abs(hs[:, None] + ts[None, :]) >= abs(D.sum()) - 1e-9).mean())
    else:
        p_sf = float((stats_ >= abs(D.sum()) - 1e-9).mean())
    check(close(PH["PHSfRFP"], p_sf, 0.0006), "exact sign-flip p (E-DDQN vs RF), independent enumeration")
    sfl = pd.read_csv(RESULTS / "tables" / "posthoc" / "signflip_tests.csv")
    oth = sfl[(sfl.comparison == "E-DDQN vs model") & sfl.B.isin(["E-CB", "DQN", "CS-MLP", "LogReg", "HGB"])]
    check(close(PH["PHSfECBP"], oth.p_signflip.min(), 0.0006), "smallest sign-flip p among the other five comparisons is E-CB's")
    pfold = pd.read_csv(RESULTS / "tables" / "metrics_per_outer_fold_D1.csv").set_index(["model", "outer"])
    n_worse = sum(pfold.loc[("E-DDQN", k), "expected_cost"] > pfold.loc[("RF", k), "expected_cost"] for k in range(5))
    check(n_worse == 5 and PH["PHFoldsEDDQNWorseRF"] == "5", "E-DDQN cost above RF in every outer fold")
    selj = _json.loads((RESULTS / "selected_configs.json").read_text())
    fsets = [(m, k, v["config"]["feature_set"]) for m in MKEY for k, v in selj[m].items()]
    check(int(PH["PHFsTotal"]) == len(fsets) and int(PH["PHFsProfile"]) == sum("profile" in f for _, _, f in fsets)
          and int(PH["PHFsExposure"]) == sum(f.startswith("exposure") for _, _, f in fsets), "feature-set counts")
    check(int(PH["PHECBNoProfileFolds"]) == sum("profile" not in v["config"]["feature_set"] for v in selj["E-CB"].values()),
          "E-CB folds without questionnaire indicators")
    proto_sp = proto["search_spaces"]
    n_rf = int(np.prod([len(v) for v in proto_sp["RF"].values()]))
    n_ed = int(np.prod([len(v) for k, v in {**proto_sp["_neural_common"], **proto_sp["_agent_common"], **proto_sp["E-DDQN"]}.items()]))
    check(PH["PHSpaceRF"] == f"{n_rf:,}" and PH["PHSpaceEDDQN"] == f"{n_ed:,}", "search-space sizes")
    # review round 3: search draw, baseline sign-flip, fold differences, pre-registration and README statements
    hpo = pd.read_csv(RESULTS / "hpo_results.csv")
    h0 = hpo[hpo.outer == 0]
    for fam, k in (("E-DDQN", "EDDQN"), ("E-CB", "ECB"), ("DQN", "DQN")):
        g = h0[h0.family == fam]
        check(int(PH[f"PHDrawExposure{k}"]) == int((g.cfg_feature_set == "exposure").sum())
              and int(PH[f"PHDrawQ{k}"]) == int(g.cfg_feature_set.str.contains("profile").sum()), f"search draw counts {fam}")
    he = hpo[hpo.family == "E-DDQN"]
    n_lower = sum(gk[gk.cfg_feature_set.str.contains("profile")].pooled_oof_min_cost.min()
                  < gk[~gk.cfg_feature_set.str.contains("profile")].pooled_oof_min_cost.min() for _, gk in he.groupby("outer"))
    check(int(PH["PHDrawFoldsQLowerEDDQN"]) == n_lower, "E-DDQN folds where questionnaire candidates had lower validation cost")
    fdiff = [pfold.loc[("E-DDQN", k), "expected_cost"] - pfold.loc[("RF", k), "expected_cost"] for k in range(5)]
    check(close(PH["PHFoldDiffEDDQNRFMin"], min(fdiff), 0.0006) and close(PH["PHFoldDiffEDDQNRFMax"], max(fdiff), 0.0006),
          "per-fold E-DDQN minus RF cost range")
    tl = pd.read_csv(RESULTS / "predictions" / "Time-LR.csv.gz", dtype={"seed": str}).query("seed == 'ens'") \
        .sort_values(["outer", "session_id", "step"]).reset_index(drop=True)
    ctl = 5 * ((tl.pred_D1_min_cost.to_numpy() == 0) & (yv == 1)) + ((tl.pred_D1_min_cost.to_numpy() == 1) & (yv == 0))
    D2 = pd.Series(ctl - cvec["RF"]).groupby(gv).sum().to_numpy(float)
    hs2 = np.array([np.dot(s, D2[:11]) for s in itertools.product((1, -1), repeat=11)])
    ts2 = np.array([np.dot(s, D2[11:]) for s in itertools.product((1, -1), repeat=len(D2) - 11)])
    p2 = float((np.abs(hs2[:, None] + ts2[None, :]) >= abs(D2.sum()) - 1e-9).mean())
    check(close(PH["PHSfTimeLRvsRFP"], p2, 0.0006), "exact sign-flip p (Time-LR vs RF), independent enumeration")
    readme = (REVISION_ROOT / "README.md").read_text()
    for k in ("PHTimeLRRocAucMean", "PHWfRFAuc", "PHWfTimeLRAuc", "PHTimeLRvsRFCostP", "PHSfTimeLRvsRFP", "PHHolmRF", "PHSfRFHolm"):
        check(PH[k] in readme, f"README quotes {k} = {PH[k]}")
    sp_txt = (REVISION_ROOT / "paper" / "supplement" / "sections" / "s_posthoc.tex").read_text()
    check("cost curves (S5.5) were committed" in sp_txt and "without prior commitment" in sp_txt,
          "Supplement S5 distinguishes pre-committed from later analyses")
    # wording corrected in the deep audit must not come back
    body = "\n".join(t.read_text() for t in (REVISION_ROOT / "paper").rglob("*.tex") if "generated" not in t.parts)
    for bad in ("participants are not shared", "sessions and participants are not shared", "calibrated-probability",
                "21 whole-session", "every curve approaches 1", "exactly as Eq", "explain E-DDQN's under-performance",
                "because the detectors hardly use those channels", "comparable budgets", "excludes leakage",
                "no information can pass", "samples rather than participants", "using exposure features (Section",
                "which was committed before they were run, and are produced", "committed before those analyses were run",
                "explains the inflated results", "predicted exactly once",
                "higher than always alarming)", "close to chance", "ranks much better", "ranks last of"):
        check(bad not in body, f"paper contains corrected wording: '{bad}'")
    # bootstrap p-values between 0.01 and 0.05 are read as approximate (Section III-G): a main-text
    # paragraph that quotes one must say so or report the comparison as not significant
    pv = {**MAC, **PH}
    zone = [k for k, v in pv.items() if re.search(r"(Pboot|P|Holm)$", k) and not k.startswith("PHSf")
            and re.fullmatch(r"0\.\d+", str(v)) and 0.01 <= float(v) <= 0.05]
    n_zone = 0
    for tex in sorted((REVISION_ROOT / "paper" / "sections").glob("*.tex")):
        for para in re.split(r"\n\s*\n", tex.read_text()):
            for k in zone:
                if re.search(r"\\" + k + r"(?![A-Za-z])", para):
                    n_zone += 1
                    check(re.search(r"approximate|not significant|suggestive", para) is not None,
                          f"{tex.name}: p = {pv[k]} (\\{k}) quoted without the approximate / not-significant caveat")
    check(n_zone >= 3, f"approximate-zone p-values found in the main text: {n_zone}")
    res_txt = (REVISION_ROOT / "paper" / "sections" / "s5_results.tex").read_text()
    for k in ("PHTimeLRvsEDDQNAucP", "PHTimeHGBvsEDDQNAucP", "PHAlwEDDQNGrpP", "EDDQNCIRocAucLo"):
        check("\\" + k in res_txt, f"Results quote \\{k} (baselines vs E-DDQN, E-DDQN vs always alarm, E-DDQN ROC-AUC CI)")
    # every macro used in the new paper and its supplement is defined
    pdef = defined | set(PH)
    for tex in (REVISION_ROOT / "paper").rglob("*.tex"):
        if "generated" in tex.parts:
            continue
        for name in re.findall(r"\\([A-Z][A-Za-z]+)(?![A-Za-z])", tex.read_text()):
            if re.match(r"^(PH|EDDQN|ECB|DQN|CSMLP|LR|HGB|RF|Leak|Orig|Pair|Ratio|Always|Shap|HPO|Att|DOne|Abl)", name):
                check(name in pdef, f"paper/{tex.name}: macro \\{name} not defined")
    # stale numbers of the earlier version may appear only where that version is named
    for pdf in (REVISION_ROOT / "paper" / "main.pdf", REVISION_ROOT / "paper" / "supplement" / "supplement.pdf"):
        if not pdf.exists():
            continue
        txt = re.sub(r"\s+", " ", subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout)
        hits = []
        for st in ("96.88", "99.53", "14,680", "20,972"):
            for mt in re.finditer(re.escape(st), txt):
                ctx = txt[max(0, mt.start() - 200): mt.end() + 40]
                ok = "earlier" in ctx.lower()
                hits.append({"number": st, "named_as_earlier_version": ok, "context": ctx})
                check(ok, f"{pdf.name}: {st} outside a passage naming the earlier version")
        check("submitted" not in txt.lower(), f"{pdf.name}: the word 'submitted' appears")
        paper_hits[pdf.name] = hits
    (QC / "paper_stale_number_contexts.json").write_text(json.dumps(paper_hits, indent=1))
    # author inputs still to be completed (listed, not counted as failures)
    pending = []
    for tex in sorted((REVISION_ROOT / "paper").rglob("*.tex")):
        if "generated" in tex.parts:
            continue
        body = "\n".join(l for l in tex.read_text().splitlines() if not l.lstrip().startswith("%"))
        for mt in re.finditer(r"\\authorinput\{([^}]*)\}", body):
            if not mt.group(0).startswith("\\authorinput}"):
                pending.append(f"{tex.relative_to(REVISION_ROOT)}: {mt.group(1)}")
    pending = [x for x in pending if not x.endswith(": #1")]

report = {"checks": checks, "failures": fails,
          "pending_author_inputs": pending if PH_JSON.exists() else [], "macros_defined": len(defined), "macros_used_in_text": len(used),
          "stale_number_occurrences": {k: len(v) for k, v in pdf_hits.items()},
          "note": "stale-number occurrences are listed with context in stale_number_contexts.json; each must be either inside an explicitly labelled description of the submitted version or a coincidental substring of a different number (e.g. 8.8 inside 98.8)"}
(QC / "consistency_report.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1)[:3000])
sys.exit(1 if fails else 0)
