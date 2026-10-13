"""Post-hoc baselines and sensitivity analyses (configs/posthoc.json).

These were specified after the frozen primary analysis had been completed and
reported.  They reuse the frozen splits, selection rule, checkpoint and
threshold rules, cross-fitting recipe and seeds of configs/protocol.json and
never touch an outer-test fold before the final stage.  No primary result,
table or macro is changed; outputs go to results/tables/posthoc/ and
results/figures/posthoc_*.

Usage:
  python scripts/11_posthoc.py run [--workers N]   # hpo + select + final for the post-hoc families
  python scripts/11_posthoc.py analyze              # all post-hoc statistics, tables, figures, macros
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from eddqn import CONFIGS, RESULTS  # noqa: E402
from eddqn.metrics import (BAYES_THRESHOLD, binary_metrics, cluster_bootstrap, cost_of,  # noqa: E402
                           min_cost_value, paired_cluster_bootstrap_diff, ranking_metrics, sweep)


def _module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod          # pool workers pickle functions by module name
    spec.loader.exec_module(mod)
    return mod


RP = _module("run_protocol", "03_run_protocol.py")
AG = _module("aggregate", "04_aggregate.py")
PROTOCOL = RP.PROTOCOL
POSTHOC = json.loads((CONFIGS / "posthoc.json").read_text())
PH_FAMS = list(POSTHOC["families"])
MAIN = AG.MAIN
OUT = RESULTS / "tables" / "posthoc"
OUT.mkdir(parents=True, exist_ok=True)
SEL_PATH = RESULTS / "selected_configs_posthoc.json"
NB = POSTHOC["n_boot"]
KO, KI, SEEDS = AG.KO, AG.KI, AG.SEEDS


# ------------------------------------------------------------------ run
def configs_for(fam):
    f = POSTHOC["families"][fam]
    from eddqn.experiment import sample_configs
    return sample_configs(f["search_space"], {"feature_set": f["feature_set"]}, f["budget"], f["hpo_seed"])


def run(workers):
    from eddqn.data import build_datasets, fold_frames, split_tables
    long, _, _ = build_datasets()
    tables = split_tables(long, PROTOCOL)
    saved = pd.read_csv(RP.PROCESSED / "outer_folds.csv")
    assert saved[["group_id", "fold"]].sort_values("group_id").values.tolist() == \
        tables["outer"][["group_id", "fold"]].sort_values("group_id").values.tolist(), "split drift"
    RP.configs_for = configs_for                     # HPO with the post-hoc spaces and seeds
    RP.stage_hpo(long, tables, PH_FAMS, workers)
    # selection: identical rule to the primary analysis (pooled inner-OOF min 5:1 cost, tie PR-AUC)
    sel, rows = {}, []
    for fam in PH_FAMS:
        sel[fam] = {}
        for k in range(KO):
            ys = [fold_frames(long, tables, k, j)[1]["y"].to_numpy() for j in range(KI)]
            y = np.concatenate(ys)
            best = None
            for ci, cfg in enumerate(configs_for(fam)):
                parts = [RP.load(RP.RUNS / "hpo" / fam / f"o{k}_c{ci:02d}_i{j}.pkl") for j in range(KI)]
                s = np.concatenate([p["val_score"] for p in parts])
                crit, rk = min_cost_value(s, y), ranking_metrics(s, y)
                rows.append({"family": fam, "outer": k, "config_id": ci, "pooled_oof_min_cost": crit,
                             "pooled_oof_pr_auc": rk["pr_auc"], "pooled_oof_roc_auc": rk["roc_auc"],
                             **{f"cfg_{a}": b for a, b in cfg.items()}})
                key = (crit, -rk["pr_auc"])
                if best is None or key < best[0]:
                    best = (key, ci, cfg)
            sel[fam][str(k)] = {"config_id": best[1], "config": best[2],
                                "pooled_oof_min_cost": best[0][0], "pooled_oof_pr_auc": -best[0][1]}
    SEL_PATH.write_text(json.dumps(sel, indent=2, default=str))
    pd.DataFrame(rows).to_csv(RESULTS / "hpo_results_posthoc.csv", index=False)
    # final stage: cross-fitted models, every seed; clean and perturbed outer-test folds scored once
    RP._final_cache(long, tables, with_attacks=True)
    jobs = []
    for fam in PH_FAMS:
        jobs += RP.final_jobs(fam, sel[fam])
    RP.run_jobs(jobs, workers)


# -------------------------------------------------------------- helpers
def holm(p):
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj


def threshold_min_cost_ratio(score, y, R):
    """D1 at an arbitrary FN:FP ratio R (validation only); ties broken towards
    the Bayes cut-off 1/(1+R) (identical to the primary rule at R = 5)."""
    t, tp, fp, fn, tn = sweep(score, y)
    cost = R * fn + fp
    best = np.flatnonzero(cost == cost.min())
    target = BAYES_THRESHOLD if R == 5 else 1.0 / (1.0 + R)
    return float(t[best[np.argmin(np.abs(t[best] - target))]])


def ens(pred):
    return pred[pred.seed == "ens"].sort_values(["outer", "session_id", "step"]).reset_index(drop=True)


def paired_auc_diff(sa, sb, y, groups, n_boot, seed):
    from sklearn.metrics import roc_auc_score
    uniq = np.unique(groups)
    idx_of = {g: np.flatnonzero(groups == g) for g in uniq}
    rng = np.random.default_rng(seed)
    obs = roc_auc_score(y, sa) - roc_auc_score(y, sb)
    d = []
    for _ in range(n_boot):
        idx = np.concatenate([idx_of[g] for g in rng.choice(uniq, len(uniq), replace=True)])
        if y[idx].min() == y[idx].max():
            continue
        d.append(roc_auc_score(y[idx], sa[idx]) - roc_auc_score(y[idx], sb[idx]))
    d = np.asarray(d)
    p = 2 * min((d <= 0).mean(), (d >= 0).mean())
    return {"diff": float(obs), "ci_low": float(np.percentile(d, 2.5)), "ci_high": float(np.percentile(d, 97.5)),
            "p_boot_two_sided": float(min(1.0, p))}


# -------------------------------------------------------------- analyze
def analyze():
    F = AG.Frames()
    sel = json.loads(SEL_PATH.read_text())
    runs = {t: AG.collect(t, F) for t in MAIN + PH_FAMS}
    preds = {}
    for t in MAIN:                                   # primary predictions are read, never rewritten
        preds[t] = pd.read_csv(AG.PRED / f"{t}.csv.gz", dtype={"seed": str})
    for t in PH_FAMS:
        preds[t] = AG.predictions_for(t, runs[t], F)
    E = {t: ens(p) for t, p in preds.items()}
    ref = E["E-DDQN"]
    for t, g in E.items():
        assert (g[["session_id", "step"]].values == ref[["session_id", "step"]].values).all(), t
    y, grp, ses = ref.y.to_numpy(), ref.group_id.to_numpy(), ref.session_id.to_numpy()
    always = np.ones_like(y)

    # 1. post-hoc baselines: metric summary (same columns as the primary summary)
    mt = pd.concat([AG.metric_table(t, preds[t]) for t in PH_FAMS])
    mt.to_csv(OUT / "metrics_per_seed_posthoc.csv", index=False)
    summ = AG.summarise(mt)
    summ.to_csv(OUT / "metrics_summary_posthoc.csv", index=False)
    cis = {t: AG.bootstrap_cis(t, preds[t]) for t in PH_FAMS}
    (OUT / "bootstrap_cis_D1_posthoc.json").write_text(json.dumps(cis, indent=1))
    sel_rows = [{"model": f, "outer": int(k), **v["config"], "pooled_oof_min_cost": v["pooled_oof_min_cost"]}
                for f, d in sel.items() for k, v in d.items()]
    pd.DataFrame(sel_rows).to_csv(OUT / "selected_configs_posthoc.csv", index=False)

    # 2. post-hoc baselines vs RF (best primary model) and vs E-DDQN: paired cost and ROC-AUC
    rows = []
    for a in PH_FAMS:
        for b in ("RF", "HGB", "E-DDQN"):
            ca = paired_cluster_bootstrap_diff(cost_of, E[a].pred_D1_min_cost.to_numpy(), E[b].pred_D1_min_cost.to_numpy(),
                                               y, grp, n_boot=NB, seed=5)
            au = paired_auc_diff(E[a].score.to_numpy(), E[b].score.to_numpy(), y, grp, NB, seed=6)
            rows.append({"A": a, "B": b, "cost_A_minus_B": ca["diff"], "cost_ci_low": ca["ci_low"], "cost_ci_high": ca["ci_high"],
                         "cost_p": ca["p_boot_two_sided"], "auc_A_minus_B": au["diff"], "auc_ci_low": au["ci_low"],
                         "auc_ci_high": au["ci_high"], "auc_p": au["p_boot_two_sided"]})
    pd.DataFrame(rows).to_csv(OUT / "posthoc_vs_primary.csv", index=False)

    # 3. Holm adjustment of the primary paired comparisons (E-DDQN vs the six other primary models)
    hl = []
    for rule in ("D1_min_cost", "D0_bayes_1_6", "recall>=0.95"):
        pt = pd.read_csv(RESULTS / "tables" / f"paired_tests_{rule.replace('>=', 'ge')}.csv")
        pt = pt[pt.B.isin(MAIN)].copy()
        pt["p_holm"] = holm(pt.cost_diff_p_cluster_bootstrap.to_numpy())
        pt["rule"] = rule
        hl.append(pt[["rule", "A", "B", "cost_A_minus_B", "cost_diff_ci_low", "cost_diff_ci_high",
                      "cost_diff_p_cluster_bootstrap", "p_holm"]])
    pd.concat(hl).to_csv(OUT / "paired_tests_holm.csv", index=False)

    # 4. every model vs always alarm (D1), groups and sessions as resampling units
    rows = []
    for t in MAIN + PH_FAMS:
        p = E[t].pred_D1_min_cost.to_numpy()
        for unit, g in (("group", grp), ("session", ses)):
            r = paired_cluster_bootstrap_diff(cost_of, p, always, y, g, n_boot=NB, seed=7)
            rows.append({"model": t, "unit": unit, "cost_model_minus_always": r["diff"], "ci_low": r["ci_low"],
                         "ci_high": r["ci_high"], "p": r["p_boot_two_sided"]})
    va = pd.DataFrame(rows)
    for unit in ("group", "session"):          # Holm over all models for each resampling unit
        m = va.unit == unit
        va.loc[m, "p_holm"] = holm(va.loc[m, "p"].to_numpy())
    va.to_csv(OUT / "vs_always_alarm.csv", index=False)

    # 5. grouping sensitivity of the primary paired comparisons: sessions as units + Holm
    rows = []
    for b in [m for m in MAIN if m != "E-DDQN"] + PH_FAMS:
        r = paired_cluster_bootstrap_diff(cost_of, E["E-DDQN"].pred_D1_min_cost.to_numpy(), E[b].pred_D1_min_cost.to_numpy(),
                                          y, ses, n_boot=NB, seed=5)
        rows.append({"A": "E-DDQN", "B": b, "unit": "session", "cost_A_minus_B": r["diff"], "ci_low": r["ci_low"],
                     "ci_high": r["ci_high"], "p": r["p_boot_two_sided"]})
    sd = pd.DataFrame(rows)
    prim = sd.B.isin(MAIN)
    sd.loc[prim, "p_holm_primary"] = holm(sd.loc[prim, "p"].to_numpy())
    sd.to_csv(OUT / "paired_tests_session_units.csv", index=False)

    # 6. leave-one-group-out jackknife: cost of each model and E-DDQN-minus-B differences
    groups = np.unique(grp)
    jk = []
    for g in groups:
        keep = grp != g
        rec = {"left_out_group": g, "n_left_out": int((~keep).sum())}
        for t in MAIN + PH_FAMS:
            rec[f"cost_{t}"] = cost_of(E[t].pred_D1_min_cost.to_numpy()[keep], y[keep])
        rec["cost_Always alarm"] = cost_of(always[keep], y[keep])
        jk.append(rec)
    jk = pd.DataFrame(jk)
    jk.to_csv(OUT / "jackknife_leave_one_group_out.csv", index=False)
    js = []
    full = {t: cost_of(E[t].pred_D1_min_cost.to_numpy(), y) for t in MAIN + PH_FAMS}
    full["Always alarm"] = cost_of(always, y)
    for b in [m for m in MAIN if m != "E-DDQN"] + PH_FAMS + ["Always alarm"]:
        d = jk["cost_E-DDQN"] - jk[f"cost_{b}"]
        js.append({"A": "E-DDQN", "B": b, "full_diff": full["E-DDQN"] - full[b], "jk_min": d.min(), "jk_max": d.max(),
                   "sign_flips": int(((d > 0) != (full["E-DDQN"] - full[b] > 0)).sum())})
    for t in MAIN + PH_FAMS:
        d = jk[f"cost_{t}"] - jk["cost_Always alarm"]
        js.append({"A": t, "B": "Always alarm", "full_diff": full[t] - full["Always alarm"], "jk_min": d.min(),
                   "jk_max": d.max(), "sign_flips": int(((d > 0) != (full[t] - full["Always alarm"] > 0)).sum())})
    js = pd.DataFrame(js)
    js.to_csv(OUT / "jackknife_summary.csv", index=False)

    # 7. validation-chosen cost curves across FN:FP ratios (all models)
    ratios = POSTHOC["cost_curves"]["fn_fp_ratios"]
    rows = []
    for t in MAIN + PH_FAMS:
        for R in ratios:
            fn = fp = 0
            for k in range(KO):
                oof = np.mean([runs[t][(k, s)]["oof"]["score"].to_numpy() for s in SEEDS], axis=0)
                yo = runs[t][(k, SEEDS[0])]["oof"]["y"].to_numpy()
                thr = threshold_min_cost_ratio(oof, yo, R)
                te = np.mean([runs[t][(k, s)]["test"] for s in SEEDS], axis=0)
                yt = F.test[k].y.to_numpy()
                m = binary_metrics((te >= thr).astype(int), yt)
                fn += m["FN"]
                fp += m["FP"]
            n, pos = len(y), int(y.sum())
            c = (R * fn + fp) / n
            triv = min((n - pos) / n, R * pos / n)
            rows.append({"model": t, "ratio": R, "cost": c, "trivial_cost": triv, "relative_cost": c / triv,
                         "recall": 1 - fn / pos, "fpr": fp / (n - pos)})
    cc = pd.DataFrame(rows)
    cc.to_csv(OUT / "cost_curves.csv", index=False)
    # consistency: R = 5 must reproduce the primary D1 seed-ensemble cost
    for t in MAIN + PH_FAMS:
        c5 = cc[(cc.model == t) & (cc.ratio == 5)].cost.iloc[0]
        assert abs(c5 - full[t]) < 1e-12, (t, c5, full[t])
    plot_cost_curves(cc)

    # 8. perturbation invariance of the post-hoc baselines (inputs are not attackable channels)
    att = AG.attack_auc({t: runs[t] for t in PH_FAMS}, F)
    att.to_csv(OUT / "attack_threshold_free_posthoc.csv", index=False)
    # restore the primary attack table (attack_auc writes a fixed filename)
    AG.attack_auc({t: runs[t] for t in MAIN}, F)

    # 9. ROC/PR figure including the post-hoc baselines
    plot_roc_with_time(E)
    macros(summ, cis, cc, jk, js, sd)


def plot_cost_curves(cc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    style = {"E-DDQN": dict(lw=2.4, color="#c0392b"), "Time-LR": dict(lw=2.0, ls="--", color="black"),
             "TimeGame-HGB": dict(lw=2.0, ls="-.", color="#555555")}
    fig, ax = plt.subplots(figsize=(3.5, 3.0))   # one journal column
    for t, g in cc.groupby("model", sort=False):
        ax.plot(g.ratio, g.relative_cost, marker="o", ms=3, label=t, **style.get(t, dict(lw=1.2)))
    ax.axhline(1.0, color="k", ls=":", lw=1)
    ax.axvline(5.0, color="#999999", ls=":", lw=1)
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 5, 10, 20], ["1", "2", "5", "10", "20"])
    ax.set_xlabel("FN:FP cost ratio R", fontsize=8)
    ax.set_ylabel("cost / cost of best trivial policy", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.5, ncol=2, frameon=False, handlelength=2.2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(RESULTS / "figures" / f"posthoc_cost_curves.{ext}", dpi=220)
    plt.close(fig)


def plot_roc_with_time(E):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_auc_score, roc_curve
    fig, ax = plt.subplots(figsize=(3.5, 3.3))   # one journal column
    for t, g in E.items():
        fpr, tpr, _ = roc_curve(g.y, g.score)
        st = dict(lw=2.4, color="#c0392b") if t == "E-DDQN" else (dict(lw=2.0, ls="--", color="black") if t == "Time-LR" else
                                                                     dict(lw=2.0, ls="-.", color="#555555") if t == "TimeGame-HGB" else dict(lw=1.1))
        ax.plot(fpr, tpr, label=f"{t} ({roc_auc_score(g.y, g.score):.3f})", **st)
    ax.plot([0, 1], [0, 1], "k:", lw=0.8)
    ax.set_xlabel("False-positive rate", fontsize=8)
    ax.set_ylabel("Recall", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.5, loc="lower right", frameon=False, title="ROC-AUC", title_fontsize=6.5)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(RESULTS / "figures" / f"posthoc_roc.{ext}", dpi=220)
    plt.close(fig)


# --------------------------------------------------------------- tables
LABEL = {"Time-LR": "Time-LR (elapsed time)", "TimeGame-HGB": "Time+game HGB"}


def main_table_with_posthoc(summ):
    """Primary Table (rule D1) with the post-hoc baselines inserted as a separate
    block above the trivial policies; primary rows are copied verbatim."""
    src = (RESULTS.parent / "manuscript" / "generated" / "tab_main_D1.tex").read_text().splitlines()
    cut = max(i for i, l in enumerate(src) if l.strip() == "\\midrule")
    d1 = summ[summ.rule == "D1_min_cost"].set_index("model")

    def ms(r, m, scale, nd):
        return f"{scale * r[f'{m}_mean']:.{nd}f}$\\pm${scale * r[f'{m}_std']:.{nd}f}"
    rows = ["\\midrule", "\\multicolumn{12}{l}{\\emph{Post-hoc exposure-time baselines (added after the primary analysis)}} \\\\"]
    for t in PH_FAMS:
        r = d1.loc[t]
        cells = [LABEL[t]] + [ms(r, m, 100, 1) for m in ("recall", "specificity", "precision", "f1", "balanced_accuracy")] + \
                [ms(r, m, 1, 3) for m in ("mcc", "expected_cost", "roc_auc", "pr_auc")] + [f"{int(r.ens_FN):,}", f"{int(r.ens_FP):,}"]
        rows.append(" & ".join(cells) + " \\\\")
    out = src[:cut] + rows + src[cut:]
    (OUT / "tab_main_D1_with_posthoc.tex").write_text("\n".join(out) + "\n")


# --------------------------------------------------------------- macros
KEY = {"Time-LR": "TimeLR", "TimeGame-HGB": "TimeHGB", "E-DDQN": "EDDQN", "E-CB": "ECB", "DQN": "DQN",
       "CS-MLP": "CSMLP", "LogReg": "LR", "HGB": "HGB", "RF": "RF", "Always alarm": "Always"}


def macros(summ, cis, cc, jk, js, sd):
    M = {}

    def put(k, v):
        assert k.isalpha(), k
        M["PH" + k] = v

    def pc(x):
        return f"{100 * x:.1f}"

    def pv(p):
        return "<0.001" if p < 0.001 else f"{p:.3f}"

    def sgn(x, d=3):
        return f"{x:+.{d}f}".replace("-", "$-$")

    d1 = summ[summ.rule == "D1_min_cost"].set_index("model")
    for t in PH_FAMS:
        r, k = d1.loc[t], KEY[t]
        for m, name, f in (("recall", "Recall", pc), ("specificity", "Spec", pc), ("precision", "Prec", pc),
                           ("f1", "Fone", pc), ("balanced_accuracy", "BalAcc", pc)):
            put(k + name + "Mean", f(r[f"{m}_mean"]))
            put(k + name + "Sd", f(r[f"{m}_std"]))
        for m, name in (("mcc", "MCC"), ("expected_cost", "Cost"), ("roc_auc", "RocAuc"), ("pr_auc", "PrAuc")):
            put(k + name + "Mean", f"{r[f'{m}_mean']:.3f}")
            put(k + name + "Sd", f"{r[f'{m}_std']:.3f}")
        put(k + "FN", f"{int(r.ens_FN):,}")
        put(k + "FP", f"{int(r.ens_FP):,}")
        ci = cis[t]["expected_cost"]
        put(k + "CostCILow", f"{ci['ci_low']:.3f}")
        put(k + "CostCIHigh", f"{ci['ci_high']:.3f}")
        ci = cis[t]["roc_auc"]
        put(k + "AucCILow", f"{ci['ci_low']:.3f}")
        put(k + "AucCIHigh", f"{ci['ci_high']:.3f}")
    vp = pd.read_csv(OUT / "posthoc_vs_primary.csv")
    for r in vp.itertuples():
        k = KEY[r.A] + "vs" + KEY[r.B]
        put(k + "Cost", sgn(r.cost_A_minus_B))
        put(k + "CostLow", sgn(r.cost_ci_low))
        put(k + "CostHigh", sgn(r.cost_ci_high))
        put(k + "CostP", pv(r.cost_p))
        put(k + "Auc", sgn(r.auc_A_minus_B))
        put(k + "AucLow", sgn(r.auc_ci_low))
        put(k + "AucHigh", sgn(r.auc_ci_high))
        put(k + "AucP", pv(r.auc_p))
    hl = pd.read_csv(OUT / "paired_tests_holm.csv")
    for r in hl[hl.rule == "D1_min_cost"].itertuples():
        put("Holm" + KEY[r.B], pv(r.p_holm))
    put("HolmNsig", str(int((hl[hl.rule == "D1_min_cost"].p_holm < 0.05).sum())))
    va = pd.read_csv(OUT / "vs_always_alarm.csv")
    for r in va.itertuples():
        k = "Alw" + KEY[r.model] + ("Grp" if r.unit == "group" else "Ses")
        put(k, sgn(r.cost_model_minus_always))
        put(k + "Low", sgn(r.ci_low))
        put(k + "High", sgn(r.ci_high))
        put(k + "P", pv(r.p))
        put(k + "Holm", pv(r.p_holm))
    for r in sd.itertuples():
        k = "Ses" + KEY[r.B]
        put(k + "Low", sgn(r.ci_low))
        put(k + "High", sgn(r.ci_high))
        put(k + "P", pv(r.p))
        if r.B in MAIN:
            put(k + "Holm", pv(r.p_holm_primary))
    for r in js.itertuples():
        k = "Jk" + KEY[r.A] + "vs" + KEY[r.B]
        put(k + "Min", sgn(r.jk_min))
        put(k + "Max", sgn(r.jk_max))
        put(k + "Flips", str(r.sign_flips))
    put("JkGroups", str(len(jk)))
    for t in MAIN + PH_FAMS:
        g = cc[cc.model == t].set_index("ratio")
        for R in (1, 2, 5, 10, 20):
            put("Cc" + KEY[t] + {1: "One", 2: "Two", 5: "Five", 10: "Ten", 20: "Twenty"}[R], f"{g.loc[R, 'relative_cost']:.3f}")
        put("Cc" + KEY[t] + "Below", str(int((g.relative_cost < 1).sum())))
    put("CcNratios", str(cc.ratio.nunique()))
    main_table_with_posthoc(summ)
    (OUT / "posthoc_macros.json").write_text(json.dumps(M, indent=1))
    tex = ["% generated by scripts/11_posthoc.py -- do not edit"] + \
          [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(M.items())]
    (OUT / "posthoc_macros.tex").write_text("\n".join(tex) + "\n")
    print(f"{len(M)} post-hoc macros written")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["run", "analyze"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    run(a.workers) if a.stage == "run" else analyze()
