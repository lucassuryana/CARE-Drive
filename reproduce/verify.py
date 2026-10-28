"""
Compare the recomputed results (results.py) with the manuscript values
(manuscript_values.py). Used by reproduce_all.py and by the tests.

Each check is a dict with: id, ref (manuscript location), what, expected,
observed, status. Status is one of
  MATCH            recomputed from archived raw data and equal at the
                   precision printed in the paper
  MISMATCH         recomputed value differs from the paper
  RECORD_ONLY      equals the hand-compiled Stage 1 record, but no per-run
                   data exists to recompute it
  NOT_VERIFIABLE   neither raw data nor a record is available
"""

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from . import manuscript_values as mv
from . import results as r

ANALYSIS_SCRIPT = r.ROOT / "tables/table_06-08/care_drive_stage2_analysis.py"


def _check(checks, id_, ref, what, expected, observed, ok, status_if_ok="MATCH"):
    checks.append({"id": id_, "ref": ref, "what": what, "expected": expected,
                   "observed": observed, "status": status_if_ok if ok else "MISMATCH"})


def stage1_checks():
    checks = []
    t4, t5 = r.stage1_record()
    for (prompt, model), exp in mv.TABLE4.items():
        row = t4[(t4.prompt == prompt) & (t4.model == model)]
        obs = int(row.overtake.iloc[0]) if len(row) else None
        _check(checks, f"T4 {prompt} / {model}", "Table 4", "overtake count of 30",
               exp, obs, obs == exp, "RECORD_ONLY")
    _check(checks, "T4 configurations", "Table 4, Sec. 3.3.1",
           "number of screened configurations", 12, len(t4), len(t4) == 12, "RECORD_ONLY")
    for (scen, prompt, L), (t_exp, p_exp) in mv.TABLE5.items():
        row = t5[(t5.scenario == scen) & (t5.prompt == prompt) & (t5.L == L)]
        t_obs, p_obs = (float(row.time_s.iloc[0]), float(row.overtake_pct.iloc[0])) if len(row) else (None, None)
        ok = t_obs is not None and round(t_obs, 3) == t_exp and round(p_obs, 2) == p_exp
        _check(checks, f"T5 {scen} / {prompt} / {L}", "Table 5", "time (s), overtake (%)",
               (t_exp, p_exp), (t_obs, p_obs), ok, "RECORD_ONLY")
    checks.append({"id": "T5 legal acknowledgement", "ref": "Sec. 4.1.3",
                   "what": "all 180 CoT and 180 ToT outputs acknowledge the legal prohibition",
                   "expected": "360/360", "observed": "no per-run responses archived",
                   "status": "NOT_VERIFIABLE"})
    return checks


def stage2_descriptive_checks():
    checks = []
    for s in ("ToT", "CoT"):
        integ = r.stage2_integrity(s)
        ok = (integ["n"] == mv.STAGE2_N and integ["n_cells"] == mv.STAGE2_CELLS
              and integ["cell_sizes"] == [30] and integ["decisions"]["unclear"] == 0
              and integ["decisions"]["error"] == 0 and integ["reparse_mismatches"] == 0)
        _check(checks, f"Stage 2 {s} design", "Sec. 3.4.1, Table 2",
               "generations / cells / runs per cell / unparsed",
               (mv.STAGE2_N, mv.STAGE2_CELLS, 30, 0),
               (integ["n"], integ["n_cells"], integ["cell_sizes"],
                integ["decisions"]["unclear"] + integ["decisions"]["error"]), ok)
        floor = r.stage2_floor(s)
        k17 = int(floor[floor.TTC == 1.7].k.sum())
        _check(checks, f"Stage 2 {s} TTC 1.7 s", "Sec. 4.2.2",
               "overtakes at TTC = 1.7 s (complete separation)", 0, k17, k17 == 0)
    cot = r.stage2_floor("CoT")
    k = int(cot[cot.L == "few-sentences"].k.sum())
    _check(checks, "Stage 2 CoT few-sentences", "Sec. 3.4.4, 4.2.3",
           "overtakes under CoT few-sentences (floor)", 0, k, k == 0)
    cells = r.stage2_cells("ToT")
    nl = cells[cells.L == "no-limit"]
    _check(checks, "Stage 2 ToT no-limit range", "Sec. 4.2.1",
           "range of per-condition overtaking rates", (0.0, 1.0),
           (nl.p.min(), nl.p.max()), (nl.p.min(), nl.p.max()) == (0.0, 1.0))
    ratio = r.stage2_length_ratio("ToT")
    _check(checks, "Explanation length ratio", "Sec. 3.3.1",
           "no-limit / few-sentences response length (ToT, chars)",
           f"~{mv.LENGTH_RATIO_APPROX:.0f}x", f"{ratio['chars']:.1f}x (words {ratio['words']:.1f}x)",
           abs(ratio["chars"] - mv.LENGTH_RATIO_APPROX) < 0.75)
    return checks


def run_stage2_analysis(outdir):
    """Run tables/table_06-08/care_drive_stage2_analysis.py into `outdir`
    (takes ~1.5 min: two 2,000-replicate bootstraps)."""
    env = dict(os.environ, CARE_DRIVE_STAGE2_OUTDIR=str(outdir))
    subprocess.run([sys.executable, str(ANALYSIS_SCRIPT)], check=True, env=env,
                   stdout=subprocess.DEVNULL)
    return {name: pd.read_csv(Path(outdir) / f"{name}.csv") for name in
            ["specification_screen", "final_model_coefficients",
             "bootstrap_intervals", "strategy_comparison"]}


def stage2_statistics_checks(out):
    checks = []
    spec = out["specification_screen"]
    spec = spec[spec.strategy == "ToT"].set_index("specification")
    for label, (k, aic, dev, df, p) in mv.TABLE6.items():
        row = spec.loc[label]
        obs = (int(row.k_params), round(row.AIC, 1), round(row.lackoffit_dev, 1),
               int(row.lackoffit_df), round(row.lackoffit_p, 3))
        p_ok = (row.lackoffit_p < 0.001) if p is None else (round(row.lackoffit_p, 3) == p)
        ok = obs[:4] == (k, aic, dev, df) and p_ok
        _check(checks, f"T6 {label}", "Table 6", "params, AIC, LoF deviance, df, p",
               (k, aic, dev, df, p if p is not None else "<0.001"), obs, ok)

    coef = out["final_model_coefficients"].set_index(["strategy", "term"])
    boot = out["bootstrap_intervals"].set_index(["strategy", "term"])
    for s, terms in mv.ODDS_RATIOS.items():
        table = "Table 7/8" if s == "ToT" else "Table 8"
        for term, (or_, lo, hi) in terms.items():
            obs = (round(coef.loc[(s, term), "OR"], 2), round(boot.loc[(s, term), "OR_boot_lo"], 2),
                   round(boot.loc[(s, term), "OR_boot_hi"], 2))
            _check(checks, f"{s} OR {term}", table, "odds ratio [95% bootstrap CI]",
                   (or_, lo, hi), obs, obs == (or_, lo, hi))

    comp = out["strategy_comparison"].set_index("term")
    for term, beta in mv.STRATEGY_INTERACTIONS.items():
        obs = (round(comp.loc[term, "beta"], 2), comp.loc[term, "p"] < 0.001)
        _check(checks, f"Strategy x {term.split(':')[0]}", "Sec. 4.2.3",
               "pooled interaction beta (p < 0.001)", (beta, True), obs, obs == (beta, True))
    return checks


def ablation_checks():
    checks = []
    for model in ("gpt", "qwen"):
        t = r.ablation_table(model).set_index(["Condition", "TTC"])
        for cond, by_ttc in mv.TABLE9[model].items():
            for ttc, (k, n) in by_ttc.items():
                row = t.loc[(cond, ttc)]
                obs = (int(row.overtake), int(row.n))
                _check(checks, f"T9 {model} {cond} TTC {ttc}", "Table 9 / Fig. 6a",
                       "overtakes / generations", (k, n), obs, obs == (k, n))
    b = r.ablation_E_breakdown("gpt").set_index(["B", "U"])
    for (B, U), k in mv.FIG6B.items():
        obs = int(b.loc[(B, U), "k"])
        _check(checks, f"Fig6b B={B} U={U}", "Fig. 6b, Sec. 4.2.4",
               "Condition E overtakes of 30 at TTC 8.5 s (from Stage 2 ToT)", k, obs, obs == k)
    q = r.ablation_integrity("qwen")
    _check(checks, "Qwen generations", "Sec. 3.4.6, 4.2.5", "total generations, overtakes",
           (mv.QWEN_TOTAL, 0), (q["n"], q["decisions"]["overtake"]),
           (q["n"], q["decisions"]["overtake"]) == (mv.QWEN_TOTAL, 0))
    _check(checks, "Qwen unparsed outputs", "Sec. 4.2.5",
           "generations without a parseable decision (paper implies 0)", 0,
           q["decisions"]["unclear"] + q["decisions"]["error"],
           q["decisions"]["unclear"] + q["decisions"]["error"] == 0)
    fe = r.ablation_file_condition_E()
    k_file = int(fe[fe.TTC == 8.5].k.sum())
    _check(checks, "Ablation workbook E rows", "Sec. 3.4.5",
           "E at TTC 8.5 s in figure_06 workbook vs. paper (paper uses Stage 2 rows)",
           75, k_file, k_file == 75)
    return checks


def speed_offset_checks():
    checks = []
    t = r.speed_offset_table("gpt").set_index(["Condition", "Rear_Time_Headway", "Surrounding_Traffic_Speed"])
    for cond, cells in mv.TABLE_A12.items():
        for (hw, v), exp in cells.items():
            row = t.loc[(cond, hw, v)]
            # .1f matches the paper and the Fig. A.8 notebook (1.95 prints as 1.9)
            obs = float(f"{row['mean']:.1f}")
            _check(checks, f"A12 {cond} {hw}s/{v}", "Table A.12", "mean offset (km/h), n = 20",
                   exp, (obs, int(row.n)), obs == exp and int(row.n) == 20)
    hw = r.speed_offset_by_headway("gpt").set_index(["Condition", "Rear_Time_Headway"])
    for h, exp in mv.A12_BY_HEADWAY.items():
        obs = float(f"{hw.loc[('E_care_drive', h), 'mean']:.1f}")
        _check(checks, f"A12 E pooled {h}s", "Sec. 4.2.6", "mean offset pooled over traffic speed",
               exp, obs, obs == exp)
    for (h, v), exp in mv.A12_ZERO_COUNTS.items():
        obs = int(t.loc[("E_care_drive", h, v), "n_zero"])
        _check(checks, f"A12 E zeros {h}s/{v}", "Sec. 4.2.6", "zero-offset generations of 20",
               exp, obs, obs == exp)
    return checks


def all_checks(stats_outdir=None):
    checks = stage1_checks() + stage2_descriptive_checks() + ablation_checks() + speed_offset_checks()
    if stats_outdir is not None:
        checks += stage2_statistics_checks(run_stage2_analysis(stats_outdir))
    return pd.DataFrame(checks)
