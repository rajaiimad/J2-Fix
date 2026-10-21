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
SD_JSON = RESULTS / "tables" / "search_draw" / "sd_macros.json"
SD = json.loads(SD_JSON.read_text()) if SD_JSON.exists() else {}
SS_JSON = RESULTS / "tables" / "score_scale" / "ss_macros.json"
SS = json.loads(SS_JSON.read_text()) if SS_JSON.exists() else {}
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
    fig1 = (REVISION_ROOT / "paper" / "figs_src" / "pipeline_tikz.tex").read_text()   # Fig. 1 source (shared by both layouts)
    check(f"clean + {len(var)} bounded" in fig1, f"Fig. 1 states {len(var)} perturbation variants")
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
                "higher than always alarming)", "close to chance", "ranks much better", "ranks last of",
                "E-DDQN's under-performance is more consistent", "Why E-DDQN Under-Performs: Exploratory",
                "does not outperform the standard DQN, with its primary search draw", "confirmed that E-DDQN does not outperform",
                "every model's score estimates", "the Bayes cut-off is $1/6$ for every model", "all clipped to the ranges observed",
                "barely change any detector", "does not have a lower 5:1 cost", "each agent was better in one draw",
                "each agent ranked seconds better in one draw", "Rendering manipulations that induce sickness are documented",
                "untuned Bayes cut-off", "its implied cut-off is $1/(1+R)$", "implementation are guarded against by the unit tests",
                "Holm-adjusted over models.", "the highest pooled values of all models", "both $p$-values are approximate",
                "verify the 5:1 regret ratio and bounded Q-values", "lists the same parameters fitted",
                "because here no model significantly outperformed", "PyTorch 2.14.1 (CPU)",
                "ranking metrics do not depend on the scale", "all ranking metrics are unaffected", "whose rewards span 0.6",
                "rule D1 and all ranking metrics do not", "with the additivity check enabled;", "each agent was significantly better in one draw",
                "part of this difference reflects the class mix", "spike and frame-drop thresholds fitted",
                "In this and the following tables the name of the proposed model",
                "which differs from this version only in these reproducibility statements"):
        check(bad not in body, f"paper contains corrected wording: '{bad}'")
    # bootstrap p-values between 0.01 and 0.05 are read as approximate (Section III-G): a main-text
    # paragraph that quotes one must say so or report the comparison as not significant
    pv = {**MAC, **PH, **SD}
    zone = [k for k, v in pv.items() if re.search(r"(Pboot|P|Holm)$", k) and "Sf" not in k
            and re.fullmatch(r"0\.\d+", str(v)) and 0.01 <= float(v) <= 0.05]
    n_zone = 0
    for tex in sorted((REVISION_ROOT / "paper" / "sections").glob("*.tex")) + sorted((REVISION_ROOT / "paper" / "sections_v2").glob("*.tex")):
        for para in re.split(r"\n\s*\n", tex.read_text()):
            for k in zone:
                if re.search(r"\\" + k + r"(?![A-Za-z])", para):
                    n_zone += 1
                    check(re.search(r"approximate|not significant|suggestive", para) is not None,
                          f"{tex.name}: p = {pv[k]} (\\{k}) quoted without the approximate / not-significant caveat")
    check(n_zone >= 3, f"approximate-zone p-values found in the main text: {n_zone}")
    # the IEEE Access version must use exactly the same section files as the working version
    _inp = lambda t: re.findall(r"\\input\{(sections/[^}]+)\}", t)
    _m, _a = (REVISION_ROOT / "paper" / "main.tex").read_text(), (REVISION_ROOT / "paper" / "main_access.tex")
    if _a.exists():
        check(_inp(_m) == _inp(_a.read_text()), f"main_access.tex inputs the same section files as main.tex ({_inp(_m)} vs {_inp(_a.read_text())})")
        _ma = (REVISION_ROOT / "paper" / "main_access.pdf")
        check(_ma.exists() and _ma.stat().st_mtime >= max(t.stat().st_mtime for t in (REVISION_ROOT / "paper" / "sections").glob("*.tex")),
              "main_access.pdf is newer than every section file")
    abs_txt = (REVISION_ROOT / "paper" / "sections" / "abstract.tex").read_text()
    check("\\begin{IEEEkeywords}" in abs_txt and "Cybersickness, virtual reality" in abs_txt, "abstract.tex contains the index terms (keywords)")
    res_txt = (REVISION_ROOT / "paper" / "sections" / "s5_results.tex").read_text()
    for k in ("PHTimeLRvsEDDQNAucP", "PHTimeHGBvsEDDQNAucP", "PHAlwEDDQNGrpP", "EDDQNCIRocAucLo"):
        check("\\" + k in res_txt, f"Results quote \\{k} (baselines vs E-DDQN, E-DDQN vs always alarm, E-DDQN ROC-AUC CI)")
    # every macro used in the new paper and its supplement is defined
    pdef = defined | set(PH) | set(SD) | set(SS)
    for tex in (REVISION_ROOT / "paper").rglob("*.tex"):
        if "generated" in tex.parts:
            continue
        for name in re.findall(r"\\([A-Z][A-Za-z]+)(?![A-Za-z])", tex.read_text()):
            if re.match(r"^(PH|SD|SS|EDDQN|ECB|DQN|CSMLP|LR|HGB|RF|Leak|Orig|Pair|Ratio|Always|Shap|HPO|Att|DOne|Abl)", name):
                check(name in pdef, f"paper/{tex.name}: macro \\{name} not defined")
    # stale numbers of the earlier version may appear only where that version is named
    for pdf in (REVISION_ROOT / "paper" / "main.pdf", REVISION_ROOT / "paper" / "main_access.pdf", REVISION_ROOT / "paper" / "supplement" / "supplement.pdf",
                REVISION_ROOT / "paper" / "main_access_v2.pdf", REVISION_ROOT / "paper" / "supplement" / "supplement_v2.pdf"):
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

# ------------------------------- 5. search-draw sensitivity (configs/posthoc.json)
if SD:
    import itertools
    spec = json.loads((REVISION_ROOT / "configs" / "posthoc.json").read_text())["search_draw_sensitivity"]
    skey = {"E-DDQN": "EDDQNDrawOne", "E-DDQN-draw2": "EDDQNDrawTwo", "E-DDQN-draw3": "EDDQNDrawThree",
            "E-DDQN-exposure": "EDDQNExposure", "DQN": "DQNDrawOne", "DQN-draw2": "DQNDrawTwo",
            "DQN-draw3": "DQNDrawThree", "DQN-exposure": "DQNExposure"}
    hs = pd.read_csv(RESULTS / "hpo_results_search_draw.csv")
    hp = pd.read_csv(RESULTS / "hpo_results.csv")
    ssel = json.loads((RESULTS / "selected_configs_search_draw.json").read_text())
    check(sorted(ssel) == sorted(v["name"] for v in spec["variants"]), "search draw: every pre-specified variant was run")
    st, sens = {}, {}
    for name, k in skey.items():
        h = hs[hs.family == name] if name in ssel else hp[hp.family == name]
        check(h.groupby("outer").config_id.nunique().eq(16).all() and h.outer.nunique() == 5, f"search draw {name}: 16 candidates x 5 folds")
        check(int(SD[f"SD{k}ExpCand"]) == int((h[h.outer == 0].cfg_feature_set == "exposure").sum()),
              f"search draw {name}: exposure-only candidates")
        if name in ssel:
            v = next(v for v in spec["variants"] if v["name"] == name)
            if v["feature_set"]:
                check((h.cfg_feature_set == v["feature_set"]).all(), f"{name}: every candidate uses {v['feature_set']}")
            for kk, gk in h.groupby("outer"):
                best = gk.sort_values(["pooled_oof_min_cost", "pooled_oof_pr_auc", "config_id"], ascending=[True, False, True]).iloc[0]
                check(int(best.config_id) == ssel[name][str(kk)]["config_id"], f"{name} fold {kk}: selection rule reproduced")
        df = pd.read_csv(RESULTS / "predictions" / f"{name}.csv.gz", dtype={"seed": str})
        cost, wfa = [], []
        for _, g in df[df.seed != "ens"].groupby("seed"):
            tn, fp, fn, tp = confusion_matrix(g.y, g.pred_D1_min_cost, labels=[0, 1]).ravel()
            cost.append((5 * fn + fp) / len(g))
            wfa.append(np.mean([roc_auc_score(h2.y, h2.score) for _, h2 in g.groupby("outer")]))
        e = df[df.seed == "ens"].sort_values(["outer", "session_id", "step"]).reset_index(drop=True)
        tn, fp, fn, tp = confusion_matrix(e.y, e.pred_D1_min_cost, labels=[0, 1]).ravel()
        st[name] = {"cost": np.mean(cost), "wf": np.mean(wfa), "ens": (5 * fn + fp) / len(e)}
        sens[name] = e
        check(close(SD[f"SD{k}Cost"], st[name]["cost"], 0.0006), f"search draw {name}: seed-mean cost")
        check(close(SD[f"SD{k}WfAuc"], st[name]["wf"], 0.0006), f"search draw {name}: within-fold ROC-AUC")
        check(close(SD[f"SD{k}EnsCost"], st[name]["ens"], 0.0006), f"search draw {name}: ensemble cost")
    # draw 1 is the primary analysis, unchanged
    check(SD["SDEDDQNDrawOneCost"] == MAC["EDDQNCostCostMean"] and SD["SDDQNDrawOneCost"] == MAC["DQNCostCostMean"]
          and SD["SDEDDQNDrawOneWfAuc"] == PH["PHWfEDDQNAuc"] and SD["SDDQNDrawOneWfAuc"] == PH["PHWfDQNAuc"]
          and SD["SDPairOneDiff"] == MAC["PairDOneDQNCostDiff"] and SD["SDPairOneP"] == MAC["PairDOneDQNPboot"],
          "search draw: draw 1 reproduces the primary E-DDQN and DQN results")
    pkey = {"draw 1 (primary)": "One", "draw 2": "Two", "draw 3": "Three", "exposure only": "Exposure"}
    for a, b, label in spec["pairs"]:
        ea, eb = sens[a], sens[b]
        check((ea[["session_id", "step"]].values == eb[["session_id", "step"]].values).all(), f"search draw pair {label}: aligned samples")
        check(close(SD[f"SDPair{pkey[label]}Diff"], st[a]["ens"] - st[b]["ens"], 0.0006), f"search draw pair {label}: cost difference")
        check(close(SD[f"SDPair{pkey[label]}AucDiff"], roc_auc_score(ea.y, ea.score) - roc_auc_score(eb.y, eb.score), 0.0006),
              f"search draw pair {label}: ROC-AUC difference")
        yv2, gv2 = ea.y.to_numpy(), ea.group_id.to_numpy()
        ca = 5 * ((ea.pred_D1_min_cost.to_numpy() == 0) & (yv2 == 1)) + ((ea.pred_D1_min_cost.to_numpy() == 1) & (yv2 == 0))
        cb = 5 * ((eb.pred_D1_min_cost.to_numpy() == 0) & (yv2 == 1)) + ((eb.pred_D1_min_cost.to_numpy() == 1) & (yv2 == 0))
        D3 = pd.Series(ca - cb).groupby(gv2).sum().to_numpy(float)
        hs3 = np.array([np.dot(s, D3[:11]) for s in itertools.product((1, -1), repeat=11)])
        ts3 = np.array([np.dot(s, D3[11:]) for s in itertools.product((1, -1), repeat=len(D3) - 11)])
        p3 = float((np.abs(hs3[:, None] + ts3[None, :]) >= abs(D3.sum()) - 1e-9).mean())
        pm = SD[f"SDPair{pkey[label]}SfP"]
        check((p3 < 0.001) if pm.startswith("$<$") else close(pm, p3, 0.0006), f"search draw pair {label}: exact sign-flip p (independent enumeration)")
    g2 = [ssel["E-DDQN-draw2"][str(kk)]["config"]["gamma"] for kk in range(5)]
    check(int(SD["SDEDDQNDrawTwoStrongGammaFolds"]) == sum(abs(g - 0.99) < 1e-12 for g in g2), "E-DDQN draw 2: folds selecting gamma = 0.99")
    check(max(st[n]["wf"] for n in ("E-DDQN", "E-DDQN-draw2", "E-DDQN-draw3", "E-DDQN-exposure")) == st["E-DDQN-draw2"]["wf"],
          "E-DDQN draw 2 has the highest within-fold ROC-AUC of the E-DDQN variants (stated in V-G)")
    check(SD["SDEDDQNWfMin"] == PH["PHWfEDDQNAuc"] and float(SD["SDEDDQNWfMax"]) <= float(PH["PHWfRFAuc"]),
          "E-DDQN draw range: lowest primary model up to (not above) the random forest")
    check(float(SD["SDEDDQNCostMin"]) > float(MAC["RFCostCostMean"]), "E-DDQN's cost in every draw stays above the random forest's (stated in VII)")
    for f, ks in (("abstract.tex", ("SDEDDQNWfMin", "SDEDDQNWfMax")), ("s5_results.tex", ("SDCostPMin", "SDPairTwoAucP", "SDExposureGap")),
                  ("s6_discussion.tex", ("SDEDDQNWfMax",)), ("s7_conclusion.tex", ("SDEDDQNCostMin",))):
        t = (REVISION_ROOT / "paper" / "sections" / f).read_text()
        for kk in ks:
            check("\\" + kk in t, f"{f} reports the search-draw result (\\{kk})")
    t = (REVISION_ROOT / "paper" / "supplement" / "sections" / "s_posthoc.tex").read_text()
    check(all("\\" + kk in t for kk in ("SDROne", "SDRTwo", "SDRThree")) and "%SD-OUTCOME%" not in t, "S5.11 reports R1-R3")
    readme_sd = (REVISION_ROOT / "README.md").read_text()
    for kk in ("SDEDDQNWfMin", "SDEDDQNWfMax", "SDEDDQNCostMin", "SDEDDQNCostMax", "SDDQNWfMin", "SDDQNWfMax", "SDDQNCostMin",
               "SDDQNCostMax", "SDCostPMin", "SDPairOneAucP", "SDPairTwoAucP", "SDExposureGap"):
        check(SD[kk] in readme_sd, f"README quotes {kk} = {SD[kk]}")
    check(SD["SDCostDiffMin"].replace("$-$", "\u2212") in readme_sd and SD["SDCostDiffMax"] in readme_sd, "README quotes the cost-difference range")
    # pre-specified decision rules recomputed
    pr = pd.read_csv(RESULTS / "tables" / "search_draw" / "pairs.csv")
    r1 = bool(((pr.cost_A_minus_B < 0) & (pr.ci_high < 0)).any())
    eds = ["E-DDQN", "E-DDQN-draw2", "E-DDQN-draw3"]
    span_c = max(st[n]["cost"] for n in eds) - min(st[n]["cost"] for n in eds)
    span_w = max(st[n]["wf"] for n in eds) - min(st[n]["wf"] for n in eds)
    gap = st["DQN-exposure"]["wf"] - st["E-DDQN-exposure"]["wf"]
    r3 = "supported" if abs(gap) <= 0.03 else ("insufficient" if gap > 0.05 else "inconclusive")   # spec: "within 0.03 of DQN's"
    check(SD["SDROne"] == ("yes" if r1 else "no"), "search draw: rule R1 recomputed")
    check(SD["SDRTwo"] == ("yes" if (span_c > 0.05 or span_w > 0.05) else "no"), "search draw: rule R2 recomputed")
    check(SD["SDRThree"] == r3 and close(SD["SDExposureGap"], gap, 0.0006), "search draw: rule R3 recomputed")

# ------------------------------- 6. score scale of rule D0 (scripts/14_score_scale.py)
if SS:
    from eddqn.data import build_datasets as _bd, fold_frames as _ff, split_tables as _st
    _proto = json.loads((REVISION_ROOT / "configs" / "protocol.json").read_text())
    _long, _, _ = _bd()
    _tabs = _st(_long, _proto)
    _sel = json.loads((RESULTS / "selected_configs.json").read_text())
    cuts = {"E-DDQN": [], "E-CB": [], "CS-MLP": []}
    for kk in range(5):
        for j in range(3):
            pi = float(_ff(_long, _tabs, kk, j)[0]["y"].mean())
            for fam in ("E-DDQN", "E-CB"):
                rho = float(_sel[fam][str(kk)]["config"]["rho"])   # share of non-events per minibatch
                cuts[fam].append(rho * pi / (rho * pi + 5 * (1 - rho) * (1 - pi)))   # = 1 / (1 + 5k)
            if _sel["CS-MLP"][str(kk)]["config"].get("sampling") == "balanced":
                cuts["CS-MLP"].append(0.5 * pi / (0.5 * pi + 5 * 0.5 * (1 - pi)))
    for fam, key in (("E-DDQN", "EDDQN"), ("E-CB", "ECB"), ("CS-MLP", "CSMLP")):
        check(close(SS[f"SS{key}CutMin"], min(cuts[fam]), 0.0006) and close(SS[f"SS{key}CutMax"], max(cuts[fam]), 0.0006),
              f"score scale: effective D0 cut-off range for {fam} (independent formula)")
    allc = cuts["E-DDQN"] + cuts["E-CB"] + cuts["CS-MLP"]
    check(close(SS["SSShiftCutMin"], min(allc), 0.006) and close(SS["SSShiftCutMax"], max(allc), 0.006), "score scale: overall shifted range")
    check(SS["SSDQNHuberCut"] == "0.25", "score scale: Huber +-1 cut-off is exactly 1/4 at gamma = 0 (analytic)")
    check(int(SS["SSDQNGammaZeroFolds"]) == sum(float(_sel["DQN"][str(kk)]["config"]["gamma"]) == 0 for kk in range(5)), "score scale: DQN folds with gamma = 0")
    for g, d in _long.groupby("game"):
        d1 = d[d.step > 0]
        check(int(SS[f"SSFps{g}Min"]) == int(d1.GameFps.min()) and int(SS[f"SSFps{g}Max"]) == int(d1.GameFps.max()), f"frame-rate range {g}")
    check(int(SS["SSFpsFlightMin"]) > 60, "the 60- and 45-fps caps lie below every Flight frame rate (stated in III-H and S4.1)")
    check(sum(_sel["E-DDQN"][str(kk)]["config"]["warmup"] == 0 for kk in range(5)) == 4, "E-DDQN selected no warm-up in four folds (stated in V-H)")
    for f, ks in (("paper/sections/s3_method.tex", ("SSEDDQNCutMin", "SSDQNHuberCut", "SSFpsFlightMin")),
                  ("paper/sections/s5_results.tex", ("SSEDDQNCutMin", "PHAlwRFSesHolm")),
                  ("paper/sections/s5c_ratio.tex", ("SSEDDQNKMin",)),
                  ("paper/supplement/sections/s_posthoc.tex", ("SSDQNHuberCut", "PHAlwRFSesHolm")),
                  ("paper/supplement/sections/s_attacks.tex", ("SSFpsFlightMin",))):
        t = (REVISION_ROOT / f).read_text()
        for kk in ks:
            check("\\" + kk in t, f"{f} quotes \\{kk}")
    readme_ss = (REVISION_ROOT / "README.md").read_text()
    for kk in ("SSShiftCutMin", "SSShiftCutMax", "SSDQNHuberCut"):
        check(SS[kk].lstrip("0") in readme_ss or SS[kk] in readme_ss, f"README quotes {kk} = {SS[kk]}")
    check(PH["PHAlwRFSesP"] in readme_ss and PH["PHAlwRFSesHolm"] in readme_ss, "README quotes the session-level always-alarm result")
    sens_path = RESULTS / "tables" / "score_scale" / "rescaling_sensitivity.csv"
    check(sens_path.exists(), "rescaling sensitivity computed")
    if sens_path.exists():
        sv = pd.read_csv(sens_path).set_index("family")
        for fam, key in (("E-DDQN", "EDDQN"), ("E-CB", "ECB"), ("CS-MLP", "CSMLP")):
            check(close(MAC[f"{key}CostCostMean"], sv.loc[fam, "cost_pipeline"], 0.0006) and close(MAC[f"{key}CostRocAucMean"], sv.loc[fam, "pooled_auc_pipeline"], 0.0006)
                  and close(PH[f"PHWf{key}Auc"], sv.loc[fam, "within_fold_auc_pipeline"], 0.0006), f"rescaling sensitivity: unchanged pipeline reproduces the published {fam} results")
        check(close(SS["SSSensMaxChanged"], 100 * sv.decisions_changed.max(), 0.06) and close(SS["SSSensMaxCostDelta"], (sv.cost_rescaled - sv.cost_pipeline).abs().max(), 0.0006)
              and close(SS["SSSensMaxAucDelta"], (sv.pooled_auc_rescaled - sv.pooled_auc_pipeline).abs().max(), 0.0006), "rescaling sensitivity macros")
        for v in (SS["SSSensMaxChanged"], SS["SSSensMaxCostDelta"], SS["SSSensMaxAucDelta"]):
            check(v in readme_ss, f"README quotes the rescaling sensitivity value {v}")

# ---- review round 4: verification on the real folds, primary/sensitivity inference, causal wording
pv_json = QC / "pipeline_verification.json"
check(pv_json.exists(), "pipeline verification (scripts/15_pipeline_verification.py) has been run")
if pv_json.exists():
    pv = json.loads(pv_json.read_text())
    PV = dict(re.findall(r"\\newcommand\{\\(PV\w+)\}\{([^}]*)\}",
                         (RESULTS / "tables" / "pipeline_verification" / "pv_macros.tex").read_text()))
    n_ok = sum(c["pass"] for c in pv["checks"])
    check(n_ok == len(pv["checks"]) and PV["PVChecksPass"] == str(n_ok) and PV["PVChecks"] == str(len(pv["checks"])),
          "pipeline verification: every check passes and the quoted counts match")
    check(PV["PVTransitions"].replace(",", "") == str(sum(r["transitions_checked"] for r in pv["info"]["replay"])),
          "pipeline verification: quoted number of replay transitions")
    t_m = (REVISION_ROOT / "paper" / "sections" / "s3_method.tex").read_text()
    t_s = (REVISION_ROOT / "paper" / "supplement" / "sections" / "s_verify.tex").read_text()
    check("\\PVTransitions" in t_m and "Supplementary Sec.~S8" in t_m and "\\PVNNTestMin" in t_s,
          "pipeline verification quoted in III-B/III-E and Supplementary S8")
    check("not participant independence" in t_m.replace("\n", " ") and "participant-independent" in t_s,
          "verification text states that participant independence is not established")
_all_paper = "".join(f.read_text() for f in (REVISION_ROOT / "paper" / "sections").glob("*.tex"))
for phrase in ("largely a consequence", "the answer is no", "reflects its search draw", "reflects that draw"):
    check(phrase not in _all_paper and phrase not in (REVISION_ROOT / "README.md").read_text()
          and phrase not in (REVISION_ROOT / "submission" / "cover_letter_template.md").read_text(),
          f"no causal overstatement: '{phrase}'")
_abs = (REVISION_ROOT / "paper" / "sections" / "abstract.tex").read_text()
check("\\PHEnsEDDQNCost" in _abs and "\\PHEnsRFCost" in _abs and "mean over seeds" in _abs and "sensitivity test" in _abs,
      "abstract labels seed-mean and seed-ensemble costs and names the sensitivity test")
check("sensitivity analysis of these $p$-values" in t_m if pv_json.exists() else False,
      "methods name the primary inferential procedure and the sensitivity analysis")
_words = len(re.sub(r"\\[A-Za-z]+(\{\})?", "X", _abs.split("\\begin{abstract}")[1].split("\\end{abstract}")[0]).split())
check(_words <= 252, f"abstract length ({_words} tokens, IEEE Access limit 250 words)")

# ---- shortened IEEE Access version (main_access_v2.tex, sections_v2/, supplement_v2.tex)
V2 = REVISION_ROOT / "paper" / "sections_v2"
if V2.exists():
    v2 = {f.name: f.read_text() for f in V2.glob("*.tex")}
    v2all = "".join(v2.values())
    _flat = lambda t: re.sub(r"\s+", " ", t)
    _absonly = lambda t: t.split("\\end{abstract}")[0]
    check(_absonly(v2["abstract.tex"]) == _absonly((REVISION_ROOT / "paper" / "sections" / "abstract.tex").read_text()),
          "v2 abstract is identical to the full-length abstract")
    _kw = v2["abstract.tex"].split("\\begin{IEEEkeywords}")[1].split("\\end{IEEEkeywords}")[0].strip().rstrip(".")
    _kwl = [k.strip() for k in _kw.split(",")]
    check(_kwl == sorted(_kwl, key=str.lower) and len(_kwl) >= 4, f"v2 index terms in alphabetical order ({len(_kwl)} terms)")
    _intro = _flat(v2["s1_introduction.tex"])
    for ab, full in (("E-DDQN", "enhanced Double Deep Q-Network (E-DDQN)"), ("E-CB", "(E-CB)"), ("CS-MLP", "CS-MLP;"),
                     ("HGB", "histogram gradient boosting, HGB"), ("ROC-AUC", "(ROC-AUC)"), ("RL", "(RL)"), ("DQN", "(DQNs)")):
        check(full in _intro, f"v2 defines {ab} in the Introduction")
    _m = _flat(v2["s3_method.tex"])
    for full in ("(PR-AUC)", "(MCC)", "(CIs)", "(SHapley Additive exPlanations)", "(SD)"):
        check(full in _m, f"v2 defines {full} at first use in Methods")
    for phrase in ("largely a consequence", "the answer is no", "reflects its search draw", "reflects that draw",
                   "participant-independent evaluation", "robust to attack", "outperforms the baselines"):
        check(phrase not in v2all, f"v2: no overstatement '{phrase}'")
    check("sensitivity analysis" in _flat(v2["s3_method.tex"]) and "firmly established only if it is significant under both procedures" in _flat(v2["s3_method.tex"]),
          "v2 methods state the primary procedure, the sensitivity analysis and the decision rule")
    for f in ("s1_introduction.tex", "s5_results.tex", "s6_discussion.tex", "s7_conclusion.tex"):
        check("not firmly established" in _flat(v2[f]), f"v2 {f}: E-DDQN vs random forest reported as not firmly established")
    for f in ("s1_introduction.tex", "s5_results.tex", "s6_discussion.tex", "s7_conclusion.tex"):
        check(re.search(r"stress test", _flat(v2[f])) is not None, f"v2 {f}: perturbations labelled a stress test")
    check("not participant independence" in _flat(v2["s3_method.tex"]) and "not participant independence" in _flat(v2["s6_discussion.tex"]),
          "v2 states that participant independence is not established")
    check("suggest" in _flat(v2["s5_results.tex"]).split("Why E-DDQN Under-Performs")[1] and "do not isolate a single cause" in _flat(v2["s5_results.tex"]),
          "v2 search-draw diagnosis worded as suggestive, without a single isolated cause")
    check("lowered rather than raised" in _flat(v2["s6_discussion.tex"]), "v2 discussion: no benefit of the asymmetric reward claimed")
    # every equation, figure, table and algorithm of the full-length method is still present
    for lab in ("eq:reward", "eq:decomp", "eq:margin", "eq:regret", "eq:phat", "eq:ddqn", "eq:unweight", "alg:eddqn",
                "fig:workflow", "fig:arch", "fig:protocol", "tab:settings", "tab:main", "tab:paired", "tab:leak", "tab:ablation"):
        check("\\label{" + lab + "}" in v2all, f"v2 keeps \\label{{{lab}}}")
    # settings table agrees with the frozen protocol
    proto = json.loads((REVISION_ROOT / "configs" / "protocol.json").read_text())
    ss = proto["search_spaces"]
    tab = _flat(v2["s3_method.tex"].split("label{tab:settings}")[1].split("end{tabular}")[0])
    for item in ("0.005, 0.01, 0.05", "0.4, 0.5, 0.6", "0, 0.5, 0.9, 0.99", "10, 100, 500", "0.90, 0.95, 0.97", "0, 4,000",
                 "1, 2, 4", "64--64, 128--128, 256--256, 256--512--256", "50, 100, 200, 400", "4, 8, 16, 31", "20, 100, 300",
                 "3, 5, 8, none", "5, 25, 100, 300", "sqrt, 0.5, 1.0", "300 trees", "buffer 50,000", "40 epochs", "20261012", "seed 777", "1000--1004"):
        check(item in tab, f"v2 settings table contains '{item}'")
    check(ss["E-DDQN"]["tau"] == [0.005, 0.01, 0.05] and ss["E-DDQN"]["rho"] == [0.4, 0.5, 0.6] and ss["DQN"]["hard_every"] == [10, 100, 500]
          and ss["_agent_common"]["eps_decay"] == [0.9, 0.95, 0.97] and ss["RF"]["n_estimators"] == [300]
          and ss["HGB"]["max_iter"] == [50, 100, 200, 400] and proto["fixed_training"]["agents"]["buffer"] == 50000
          and proto["fixed_training"]["agents"]["epochs"] == 40 and proto["fixed_training"]["agents"]["learn_every"] == 2
          and proto["hpo_seed"] == 777 and proto["split_seed"] == 20261012, "v2 settings table values match configs/protocol.json")
    # figures: the workflow names Fig. 2 for E-DDQN; that must be the architecture figure
    aux = (REVISION_ROOT / "paper" / "main_access_v2.aux")
    if aux.exists():
        at = aux.read_text()
        check(re.search(r"newlabel\{fig:arch\}\{\{2\}", at) is not None and "Fig.~2" in (REVISION_ROOT / "paper" / "figs_src" / "v2_workflow_tikz.tex").read_text(),
              "v2: Fig. 1 refers to the architecture figure as Fig. 2, and it is Fig. 2")
        lg = (REVISION_ROOT / "paper" / "main_access_v2.log").read_text()
        check("undefined references" not in lg and "Citation" not in lg.split("undefined")[0][-200:] if "undefined" in lg else True,
              "v2: no undefined references or citations")
    # supplementary sections cited by the v2 text exist in supplement_v2
    sm = (REVISION_ROOT / "paper" / "supplement" / "sections_v2" / "s_moved.tex").read_text()
    n_sub = sm.count("\\subsection{")
    for ref in set(re.findall(r"S9\.(\d+)", v2all)):
        check(1 <= int(ref) <= n_sub, f"v2 cites Supplementary Sec. S9.{ref}, which exists")
    for ref in set(re.findall(r"Sec\.~(S[1-8](?:\.\d+)?)", v2all)):
        check(ref in ("S1.4", "S2.1", "S3.1", "S4.1", "S4.3", "S5", "S5.6", "S5.9", "S5.10", "S5.11", "S5.12", "S8"), f"v2 cites Supplementary Sec. {ref} (known section)")
    pv2 = REVISION_ROOT / "paper" / "main_access_v2.pdf"
    if pv2.exists():
        npg = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pv2)], capture_output=True, text=True).stdout).group(1))
        check(npg <= 16, f"v2 length: {npg} pages (target 15-16 or fewer)")
        check(pv2.stat().st_mtime >= max(t.stat().st_mtime for t in V2.glob("*.tex")), "main_access_v2.pdf is newer than every v2 section file")

# ---- threshold-scale sensitivity (scripts/16_threshold_scale.py; posthoc.json key committed before the run)
_ts = RESULTS / "tables" / "threshold_scale" / "threshold_scale.csv"
check(_ts.exists() and "threshold_scale_sensitivity" in json.loads((REVISION_ROOT / "configs" / "posthoc.json").read_text()),
      "threshold-scale check specified in posthoc.json and run")
if _ts.exists():
    tsd = pd.read_csv(_ts, index_col=0)
    TS = json.loads((RESULTS / "tables" / "threshold_scale" / "ts_macros.json").read_text())
    for fam, key in (("E-DDQN", "EDDQN"), ("E-CB", "ECB"), ("DQN", "DQN"), ("CS-MLP", "CSMLP"), ("LogReg", "LR"), ("HGB", "HGB"), ("RF", "RF")):
        check(close(MAC[f"{key}CostCostMean"], tsd.loc[fam, "pipe_cost"], 0.0006), f"threshold-scale check reproduces the published {fam} cost")
    _num = lambda v: float(str(v).replace("$-$", "-"))
    check(close(_num(TS["TSEDDQNDeltaCost"]), tsd.loc["E-DDQN", "delta_cost"], 0.0006)
          and close(_num(TS["TSNeuralDeltaCostMax"]), tsd.loc[["E-DDQN", "E-CB", "DQN", "CS-MLP"], "delta_cost"].max(), 0.0006)
          and close(_num(TS["TSTreeLRDeltaCostMin"]), tsd.loc[["LogReg", "HGB", "RF"], "delta_cost"].min(), 0.0006), "threshold-scale macros match the table")
    same = list(tsd.pipe_cost.sort_values().index) == list(tsd.single_cost.sort_values().index)
    check(TS["TSRankUnchanged"] == ("unchanged" if same else "changed"), "threshold-scale ranking statement matches the data")
    if V2.exists():
        check("\\TSEDDQNDeltaCost" in v2["s6_discussion.tex"] and "S9.10" in v2["s3_method.tex"], "v2 reports the threshold-scale check")

report = {"checks": checks, "failures": fails,
          "pending_author_inputs": pending if PH_JSON.exists() else [], "macros_defined": len(defined), "macros_used_in_text": len(used),
          "stale_number_occurrences": {k: len(v) for k, v in pdf_hits.items()},
          "note": "stale-number occurrences are listed with context in stale_number_contexts.json; each must be either inside an explicitly labelled description of the submitted version or a coincidental substring of a different number (e.g. 8.8 inside 98.8)"}
(QC / "consistency_report.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1)[:3000])
sys.exit(1 if fails else 0)
