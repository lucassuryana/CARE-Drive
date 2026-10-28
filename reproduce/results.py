"""
Recompute the reported CARE-Drive results from the archived experiment data.

Everything here reads the saved workbooks only -- no API calls, no model
inference. Each function returns a pandas DataFrame (or a small dict) that
`reproduce_all.py` and the tests in `tests/` compare against the values
printed in the manuscript (see `manuscript_values.py`).

Decision coding follows the experiment scripts: the first match of
r"decision:\\s*case\\s*[12]" (case-insensitive) in the response decides the
run; "case 2" = overtake (1), "case 1" = stay behind (0), no match =
"Unclear", API failure = "Error".
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DATA = {
    # Stage 1 (Tables 4-5): manually compiled aggregate record, no per-run data
    "stage1_record": ROOT / "final_results_table_3_4_5_6.xlsx",
    # Stage 2 (Fig. 5, Tables 6-8)
    "stage2_ToT": ROOT / "figures/figure_05/Results_Parameter_Combinations_ToT.xlsx",
    "stage2_CoT": ROOT / "figures/figure_05/Results_Parameter_Combinations_CoT.xlsx",
    # Prompt-component ablation (Fig. 6, Table 9)
    "ablation_gpt": ROOT / "figures/figure_06/Results_Parameter_Combinations.xlsx",
    "ablation_qwen": ROOT / "tables/table_09/Results_Parameter_Combinations_Qwen.xlsx",
    # Held-out speed-offset evaluation (Fig. A.8, Table A.12)
    "speed_gpt": ROOT / "figures/figure_A8/GPT4_ToT_Baseline_vs_CAREDrive.xlsx",
    "speed_qwen": ROOT / "tables/table_A12/Qwen_ToT_Baseline_vs_CAREDrive.xlsx",
}

DECISION_RE = re.compile(r"decision:\s*case\s*[12]", re.IGNORECASE)
CONDITIONS = ["A_000_baseline", "B_001_safety_only", "C_100_reasons_only",
              "D_110_reasons_principles", "E_111_full_prompt"]


def parse_decision(text):
    m = DECISION_RE.search(str(text))
    if not m:
        return "Unclear"
    return 1 if "case 2" in m.group().lower() else 0


def _encode(df):
    """Factor encoding shared by every overtaking workbook.

    Traffic_Behind / Passenger_Hurry are free text when present and blank when
    absent; the blank values ("None", "") are read by pandas as NaN.
    """
    df = df.copy()
    df["B"] = df["Traffic_Behind"].notna().astype(int)
    df["U"] = df["Passenger_Hurry"].notna().astype(int)
    df["decision_str"] = df["Decision"].astype(str)
    df["Y"] = (df["decision_str"] == "1").astype(int)
    if "Text_Version" in df:
        df["L"] = np.where(df["Text_Version"] == "Limited", "few-sentences", "no-limit")
    return df


def _counts(s):
    s = s.astype(str)
    return pd.Series({"overtake": int((s == "1").sum()), "stay": int((s == "0").sum()),
                      "unclear": int((s == "Unclear").sum()), "error": int((s == "Error").sum()),
                      "n": len(s)})


# ----------------------------------------------------------------------------
# Stage 1 (Tables 4-5) -- manual record only
# ----------------------------------------------------------------------------
def stage1_record():
    """Parse final_results_table_3_4_5_6.xlsx into Table 4 and Table 5 frames.

    This workbook is a hand-compiled summary (no per-run responses), so the
    Stage 1 numbers can be checked against it but not recomputed from raw data.
    """
    raw = pd.read_excel(DATA["stage1_record"], header=None, dtype=str)
    t4, t5, scenario = [], [], None
    for _, r in raw.iterrows():
        a, b, c, d = r[0], r[1], r[2], r[3]
        if isinstance(c, str) and c.startswith("gpt-4.1") and str(b).isdigit():
            t4.append({"prompt": a.replace("COT", "CoT").replace("TOT", "ToT"),
                       "model": c, "overtake": int(b),
                       "avg_time_s": float(d) if isinstance(d, str) else np.nan})
        g, h = r[6], r[7]
        if isinstance(g, str) and g.startswith("Scenario"):
            scenario = g
        if isinstance(h, str) and h.startswith("Role + HR"):
            for L, (ti, pi) in {"no-limit": (8, 9), "few-sentences": (10, 11)}.items():
                t5.append({"scenario": scenario,
                           "prompt": h.replace("COT", "CoT").replace("TOT", "ToT"),
                           "L": L, "time_s": float(r[ti]), "overtake_pct": float(r[pi])})
    return pd.DataFrame(t4), pd.DataFrame(t5)


# ----------------------------------------------------------------------------
# Stage 2 (Fig. 5, Tables 6-8)
# ----------------------------------------------------------------------------
def load_stage2(strategy):
    return _encode(pd.read_excel(DATA[f"stage2_{strategy}"]))


def stage2_integrity(strategy):
    df = load_stage2(strategy)
    cells = df.groupby(["Following_Time", "TTC", "L", "B", "U"]).size()
    return {
        "n": len(df),
        "n_cells": len(cells),
        "cell_sizes": sorted(cells.unique().tolist()),
        "decisions": _counts(df["Decision"]).to_dict(),
        "reparse_mismatches": int((df["Response"].map(parse_decision).astype(str)
                                   != df["decision_str"]).sum()),
    }


def stage2_cells(strategy):
    """Per-condition overtaking counts behind Fig. 5 (Wilson CIs are drawn
    by figures/figure_05/care_drive_stage2_figures.py)."""
    df = load_stage2(strategy)
    return (df.groupby(["L", "Following_Time", "TTC", "B", "U"])["Y"]
              .agg(k="sum", n="size").reset_index()
              .assign(p=lambda g: g.k / g.n))


def stage2_floor(strategy):
    """Overtaking totals by explanation regime x TTC (separation screen)."""
    df = load_stage2(strategy)
    return df.groupby(["L", "TTC"])["Y"].agg(k="sum", n="size").reset_index()


def stage2_length_ratio(strategy):
    """Mean response length, no-limit / few-sentences (characters and words)."""
    df = load_stage2(strategy)
    chars = df["Response"].astype(str).str.len().groupby(df["L"]).mean()
    words = df["Response"].astype(str).str.split().str.len().groupby(df["L"]).mean()
    return {"chars": chars["no-limit"] / chars["few-sentences"],
            "words": words["no-limit"] / words["few-sentences"]}


# ----------------------------------------------------------------------------
# Prompt-component ablation and cross-model comparison (Fig. 6, Table 9)
# ----------------------------------------------------------------------------
def stage2_condition_E():
    """Condition E as reported in the manuscript: the 240 Stage 2 ToT
    generations matching the ablation design (F = 24 s, no-limit,
    TTC in {1.7, 8.5}, all B x U), per Section 3.4.5."""
    df = load_stage2("ToT")
    return df[(df.Following_Time == 24) & (df.L == "no-limit") & df.TTC.isin([1.7, 8.5])]


def ablation_table(model):
    """Table 9 counts. For GPT-4.1, Condition E is taken from Stage 2 (as in
    the manuscript); the separately generated E rows in the ablation
    workbook are reported by `ablation_file_condition_E` instead."""
    df = _encode(pd.read_excel(DATA[f"ablation_{model}"]))
    if model == "gpt":
        e = stage2_condition_E().assign(Condition="E_111_full_prompt")
        df = pd.concat([df[df.Condition != "E_111_full_prompt"], e], ignore_index=True)
    t = df.groupby(["Condition", "TTC"])["Decision"].apply(_counts).unstack()
    return t.reset_index()


def ablation_E_breakdown(model):
    """Condition E at TTC = 8.5 s by rear vehicle (B) x urgency (U) (Fig. 6b)."""
    if model == "gpt":
        e = stage2_condition_E()
    else:
        df = _encode(pd.read_excel(DATA["ablation_qwen"]))
        e = df[df.Condition == "E_111_full_prompt"]
    e = e[e.TTC == 8.5]
    return e.groupby(["B", "U"])["Y"].agg(k="sum", n="size").reset_index()


def ablation_file_condition_E():
    """The E rows stored in the GPT-4.1 ablation workbook (not used in the
    paper; generated by GPT4_ToT_Component_Ablation.py)."""
    df = _encode(pd.read_excel(DATA["ablation_gpt"]))
    e = df[df.Condition == "E_111_full_prompt"]
    return e.groupby(["TTC", "B", "U"])["Y"].agg(k="sum", n="size").reset_index()


def ablation_integrity(model):
    df = _encode(pd.read_excel(DATA[f"ablation_{model}"]))
    cells = df.groupby(["Condition", "TTC", "B", "U"]).size()
    return {
        "n": len(df),
        "n_cells": len(cells),
        "cell_sizes": sorted(cells.unique().tolist()),
        "following_time": sorted(df.Following_Time.unique().tolist()),
        "regimes": sorted(df.L.unique().tolist()),
        "decisions": _counts(df["Decision"]).to_dict(),
        "reparse_mismatches": int((df["Response"].map(parse_decision).astype(str)
                                   != df["decision_str"]).sum()),
    }


# ----------------------------------------------------------------------------
# Held-out speed-offset evaluation (Fig. A.8, Table A.12)
# ----------------------------------------------------------------------------
def speed_offset_table(model="gpt"):
    df = pd.read_excel(DATA[f"speed_{model}"])
    rows = []
    for (cond, hw, v), s in df.groupby(["Condition", "Rear_Time_Headway",
                                        "Surrounding_Traffic_Speed"])["Speed_Offset"]:
        rows.append({"Condition": cond, "Rear_Time_Headway": hw, "Surrounding_Traffic_Speed": v,
                     "n": len(s), "mean": s.mean(), "n_zero": int((s == 0).sum()),
                     "distribution": {int(k): int(c) for k, c in s.value_counts().sort_index().items()}})
    return pd.DataFrame(rows)


def speed_offset_by_headway(model="gpt"):
    df = pd.read_excel(DATA[f"speed_{model}"])
    return (df.groupby(["Condition", "Rear_Time_Headway"])["Speed_Offset"]
              .mean().reset_index(name="mean"))


def speed_offset_directional_agreement(model="gpt"):
    """Agreement of the parsed ACTION with the script's predefined
    Expected_Direction, per cell (see the reproducibility report)."""
    df = pd.read_excel(DATA[f"speed_{model}"])
    return (df.groupby(["Condition", "Rear_Time_Headway", "Surrounding_Traffic_Speed"])
              .agg(expected=("Expected_Direction", "first"),
                   agree=("Directional_Agreement", lambda s: int((s == True).sum())),  # noqa: E712
                   n=("Run_Number", "size"))
              .reset_index())
