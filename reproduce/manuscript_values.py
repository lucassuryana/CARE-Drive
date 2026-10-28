"""
Values reported in the manuscript (TRC submission, version dated 28 Oct 2026),
transcribed once here so the verification script and the tests compare against
a single copy. Numbers are given at the precision printed in the paper.
"""

# Table 4 -- Stage 1 Step 1 screening: overtake counts out of 30 runs.
# 12 configurations = 4 prompt configurations x 3 models.
TABLE4 = {
    ("Role", "gpt-4.1"): 0, ("Role", "gpt-4.1-mini"): 0, ("Role", "gpt-4.1-nano"): 0,
    ("Role + HR", "gpt-4.1"): 20, ("Role + HR", "gpt-4.1-mini"): 15, ("Role + HR", "gpt-4.1-nano"): 0,
    ("Role + HR + CoT", "gpt-4.1"): 30, ("Role + HR + CoT", "gpt-4.1-mini"): 28, ("Role + HR + CoT", "gpt-4.1-nano"): 8,
    ("Role + HR + ToT", "gpt-4.1"): 30, ("Role + HR + ToT", "gpt-4.1-mini"): 25, ("Role + HR + ToT", "gpt-4.1-nano"): 11,
}

# Table 5 -- Stage 1 Step 2: (scenario, prompt, regime) -> (time s, overtake %).
TABLE5 = {
    ("Scenario-1 None", "Role + HR + CoT", "no-limit"): (18.037, 50.00),
    ("Scenario-1 None", "Role + HR + ToT", "no-limit"): (16.600, 76.67),
    ("Scenario-1 None", "Role + HR + CoT", "few-sentences"): (3.950, 96.67),
    ("Scenario-1 None", "Role + HR + ToT", "few-sentences"): (4.468, 96.67),
    ("Scenario-2 Oncoming", "Role + HR + CoT", "no-limit"): (18.000, 30.00),
    ("Scenario-2 Oncoming", "Role + HR + ToT", "no-limit"): (19.568, 93.33),
    ("Scenario-2 Oncoming", "Role + HR + CoT", "few-sentences"): (5.221, 0.00),
    ("Scenario-2 Oncoming", "Role + HR + ToT", "few-sentences"): (5.630, 0.00),
    ("Scenario-3 Follow", "Role + HR + CoT", "no-limit"): (19.900, 16.67),
    ("Scenario-3 Follow", "Role + HR + ToT", "no-limit"): (17.558, 40.00),
    ("Scenario-3 Follow", "Role + HR + CoT", "few-sentences"): (4.212, 10.00),
    ("Scenario-3 Follow", "Role + HR + ToT", "few-sentences"): (4.350, 3.33),
}

# Stage 2 design (Section 3.4.1): 5 TTC x 2 B x 2 U x 3 F x 2 L x 30 runs.
STAGE2_N = 3600
STAGE2_CELLS = 120

# Table 6 -- specification screen, ToT, no-limit, TTC >= 3.4 s.
# label in the analysis output -> (k_params, AIC, lack-of-fit deviance, df, p)
# p = None means the paper prints "p < 0.001".
TABLE6 = {
    "additive linear TTC & F": (5, 1748.5, 115.7, 43, None),
    "additive categorical": (8, 1715.2, 76.4, 40, None),
    "categorical + TTC x F": (14, 1695.3, 44.6, 34, 0.106),
    "categorical + TTC x F + B x U": (15, 1697.3, 44.5, 33, 0.087),
}

# Tables 7 (ToT) and 8 (ToT vs CoT): odds ratio and 95% bootstrap CI.
_T = "C(Tc, Treatment(3.4))[T.{}]"
ODDS_RATIOS = {
    "ToT": {
        _T.format(5.1): (2.67, 1.39, 4.80),
        _T.format(6.8): (4.01, 2.08, 7.43),
        _T.format(8.5): (4.01, 2.09, 7.84),
        "B": (3.95, 3.15, 5.24),
        "Uh": (0.42, 0.33, 0.52),
    },
    "CoT": {
        _T.format(5.1): (2.49, 0.88, 6.64),
        _T.format(6.8): (6.78, 1.67, 26.52),
        _T.format(8.5): (10.06, 3.34, 30.54),
        "B": (1.16, 0.76, 1.67),
        "Uh": (0.12, 0.07, 0.17),
    },
}

# Section 4.2.3 -- pooled strategy comparison (CoT vs ToT reference).
STRATEGY_INTERACTIONS = {
    "B:C(strategy, Treatment('ToT'))[T.CoT]": -1.24,
    "Uh:C(strategy, Treatment('ToT'))[T.CoT]": -1.15,
}

# Table 9 -- overtakes / generations per prompt condition and TTC.
TABLE9 = {
    "gpt": {c: {1.7: (0, 120), 8.5: (0, 120)} for c in
            ["A_000_baseline", "B_001_safety_only", "C_100_reasons_only", "D_110_reasons_principles"]}
    | {"E_111_full_prompt": {1.7: (0, 120), 8.5: (75, 120)}},
    "qwen": {c: {1.7: (0, 40), 8.5: (0, 40)} for c in
             ["A_000_baseline", "B_001_safety_only", "C_100_reasons_only",
              "D_110_reasons_principles", "E_111_full_prompt"]},
}
QWEN_TOTAL = 400

# Fig. 6b / Section 4.2.4 -- Condition E at TTC 8.5 s, (B, U) -> overtakes of 30.
FIG6B = {(0, 0): 18, (0, 1): 11, (1, 0): 26, (1, 1): 20}

# Table A.12 -- mean speed offset (km/h), (headway s, traffic km/h).
TABLE_A12 = {
    "A_baseline": {(1.0, 70): 0.0, (1.0, 90): 0.0, (2.5, 70): 0.0, (2.5, 90): 0.0},
    "E_care_drive": {(1.0, 70): 6.0, (1.0, 90): 10.0, (2.5, 70): 1.9, (2.5, 90): 0.5},
}
# Section 4.2.6 -- aggregated over traffic speed, and zero-offset frequencies.
A12_BY_HEADWAY = {1.0: 8.0, 2.5: 1.2}
A12_ZERO_COUNTS = {(2.5, 70): 13, (2.5, 90): 19}  # out of 20

# Section 3.3.1 -- "approximately five-fold" shorter few-sentences explanations.
LENGTH_RATIO_APPROX = 5.0
