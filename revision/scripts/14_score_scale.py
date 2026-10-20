"""Effective position of the untuned cut-off p_hat >= 1/6 (rule D0) on P(y=1|s).

Descriptive and post hoc (added in the pre-submission cross-check; recorded in
configs/posthoc.json '_later_additions').  No model is trained: the computation
uses only the selected configurations and the class prevalence of each inner
training split.

* Class-balanced replay (E-DDQN, E-CB: a fraction rho of non-events in every
  minibatch) and class-balanced minibatches of the CS-MLP (50/50) train on a
  class mix other than the prevalence pi of the training rows.  The learned
  scores then estimate the posterior under that mix, whose odds are k times the
  odds of P(y=1|s), with k = ((1-rho)/rho) * ((1-pi)/pi)  (k = (1-pi)/pi for
  50/50 minibatches).  A cut-off of 1/6 on the score is therefore a cut-off of
  1/(1+5k) on P(y=1|s); for the reward-ratio runs (nominal cut-off 1/(1+R)) it
  is 1/(1+R k).
* The standard DQN's +-1 reward with the Huber loss (threshold 1): at gamma = 0
  the minimiser of the expected loss for a two-point target is
  Q(s,1) = (2p-1)/max(p,1-p) = -Q(s,0), so p_hat = 1/2 + (2p-1)/(2 max(p,1-p))
  and p_hat = 1/6 at p = 1/4.  For gamma > 0 there is no closed form.
* Models trained on the natural class mix with a class weight of 5 (logistic
  regression, HGB, random forest, CS-MLP with uniform minibatches) and unweighted
  by Eq. (7) keep the nominal cut-off 1/6.

It also records the observed frame-rate range of each game after the first
second (the logger writes 0 fps at start-up), which the paper uses to state
where the frame-rate caps of the perturbation scenarios lie.

Usage: python scripts/14_score_scale.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eddqn import CONFIGS, RESULTS  # noqa: E402
from eddqn.data import build_datasets, fold_frames, split_tables  # noqa: E402

PROTOCOL = json.loads((CONFIGS / "protocol.json").read_text())
OUT = RESULTS / "tables" / "score_scale"
FAMS = ["E-DDQN", "E-CB", "DQN", "CS-MLP", "LogReg", "HGB", "RF"]


def huber_pm1_phat(p):
    """Implied probability of the +-1 reward under the Huber loss (threshold 1) at gamma = 0."""
    p = np.asarray(p, float)
    return 0.5 + (2 * p - 1) / (2 * np.maximum(p, 1 - p))


def huber_cutoff():
    grid = np.linspace(1e-4, 1 - 1e-4, 200001)
    return float(grid[np.argmin(np.abs(huber_pm1_phat(grid) - 1 / 6))])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    long, _, _ = build_datasets()
    tables = split_tables(long, PROTOCOL)
    sel = json.loads((RESULTS / "selected_configs.json").read_text())
    p_huber = huber_cutoff()
    rows = []
    for k in range(PROTOCOL["k_outer"]):
        pis = [float(fold_frames(long, tables, k, j)[0]["y"].mean()) for j in range(PROTOCOL["k_inner"])]
        for fam in FAMS:
            c = sel[fam][str(k)]["config"]
            rho, regime, ks = None, "natural class mix, class weight 5", None
            if fam in ("E-DDQN", "E-CB"):
                rho = float(c["rho"])
                regime = "class-balanced replay"
                ks = [((1 - rho) / rho) * ((1 - pi) / pi) for pi in pis]
            elif fam == "CS-MLP" and c.get("sampling") == "balanced":
                regime = "class-balanced minibatches (50/50), class weight 5"
                ks = [(1 - pi) / pi for pi in pis]
            elif fam == "DQN":
                regime = "+-1 reward, Huber loss, uniform replay"
            if ks is not None:
                cut = [1 / (1 + 5 * kk) for kk in ks]
            elif fam == "DQN":
                cut = [p_huber] * len(pis) if float(c["gamma"]) == 0.0 else [np.nan] * len(pis)
            else:
                cut = [1 / 6] * len(pis)
            rows.append({"family": fam, "outer": k, "regime": regime, "rho": rho,
                         "gamma": c.get("gamma"), "train_prevalence_mean": float(np.mean(pis)),
                         "k_mean": float(np.mean(ks)) if ks is not None else np.nan,
                         "effective_cutoff_mean": float(np.mean(cut)) if not np.isnan(cut).all() else np.nan,
                         "effective_cutoff_min": float(np.min(cut)) if not np.isnan(cut).all() else np.nan,
                         "effective_cutoff_max": float(np.max(cut)) if not np.isnan(cut).all() else np.nan})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "effective_cutoffs.csv", index=False)
    fps = {g: (int(d[d.step > 0].GameFps.min()), int(d[d.step > 0].GameFps.max())) for g, d in long.groupby("game")}
    pd.DataFrame([{"game": g, "fps_min_after_first_second": a, "fps_max": b} for g, (a, b) in fps.items()]).to_csv(
        OUT / "frame_rate_range.csv", index=False)
    write_tables_and_macros(df, p_huber, fps)
    print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))


def write_tables_and_macros(df, p_huber, fps):
    def f3(x):
        return "--" if pd.isna(x) else f"{x:.3f}"
    name = {"E-DDQN": "E-DDQN", "E-CB": "E-CB", "DQN": "DQN", "CS-MLP": "CS-MLP"}
    body = ["\\begin{tabular}{llccccc}", "\\toprule",
            "Model & Training class mix (selected) & Fold & $\\rho$ & $\\pi$ & $k$ & Cut-off on $P(y=1\\mid s)$ \\\\", "\\midrule"]
    for fam in ("E-DDQN", "E-CB", "CS-MLP", "DQN"):
        for r in df[df.family == fam].itertuples():
            regime = r.regime if fam != "DQN" else f"$\\pm1$ reward, Huber loss ($\\gamma={r.gamma}$)"
            body.append(f"{name[fam]} & {regime} & {r.outer} & {f3(r.rho) if r.rho is not None and not pd.isna(r.rho) else '--'} & "
                        f"{r.train_prevalence_mean:.3f} & {f3(r.k_mean)} & {f3(r.effective_cutoff_mean)} \\\\")
        body.append("\\midrule")
    body[-1] = "\\bottomrule"
    body.append("\\end{tabular}")
    (OUT / "tab_ss_cutoffs.tex").write_text("\n".join(body) + "\n")
    M = {}

    def put(k, v):
        assert k.isalpha(), k
        M["SS" + k] = v
    for fam, key in (("E-DDQN", "EDDQN"), ("E-CB", "ECB")):
        d = df[df.family == fam]
        put(key + "CutMin", f"{d.effective_cutoff_min.min():.3f}")
        put(key + "CutMax", f"{d.effective_cutoff_max.max():.3f}")
        put(key + "KMin", f"{d.k_mean.min():.2f}")
        put(key + "KMax", f"{d.k_mean.max():.2f}")
    d = df[(df.family == "CS-MLP") & df.k_mean.notna()]
    put("CSMLPBalancedFolds", str(len(d)))
    put("CSMLPCutMin", f"{d.effective_cutoff_min.min():.3f}")
    put("CSMLPCutMax", f"{d.effective_cutoff_max.max():.3f}")
    shifted = df[df.k_mean.notna()]
    put("ShiftCutMin", f"{shifted.effective_cutoff_min.min():.2f}")
    put("ShiftCutMax", f"{shifted.effective_cutoff_max.max():.2f}")
    put("DQNHuberCut", f"{p_huber:.2f}")
    put("DQNGammaZeroFolds", str(int((df[df.family == "DQN"].gamma.astype(float) == 0).sum())))
    for g, (a, b) in fps.items():
        put(f"Fps{g}Min", str(a))
        put(f"Fps{g}Max", str(b))
    put("PrevMin", f"{df.train_prevalence_mean.min():.2f}")
    put("PrevMax", f"{df.train_prevalence_mean.max():.2f}")
    (OUT / "ss_macros.json").write_text(json.dumps(M, indent=1))
    (OUT / "ss_macros.tex").write_text("% generated by scripts/14_score_scale.py -- do not edit\n" +
                                       "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(M.items())) + "\n")


if __name__ == "__main__":
    main()
