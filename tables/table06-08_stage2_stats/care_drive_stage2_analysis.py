"""
CARE-Drive - Stage 2 statistical analysis (revised specification)
=================================================================

Implements the revised Stage 2 analysis:

  1. Condition-level proportions with Wilson 95% binomial confidence intervals
  2. Floor / complete-separation screening
  3. Specification screening: all two-way interactions vs. the saturated
     condition-level model (lack-of-fit deviance + AIC)
  4. Final grouped-binomial logistic regression with
        - model-based standard errors
        - standard errors clustered by experimental condition
        - grouped-binomial dispersion parameter phi
  5. Joint Wald test of the TTC x F interaction block
  6. Condition-level nonparametric bootstrap (resamples conditions, not
     individual generations)
  7. Model-predicted probabilities at named contextual profiles
  8. Pooled thought-strategy comparison model

Inputs : the two Stage 2 result workbooks (ToT and CoT).
Outputs: console tables + CSV files written to OUTDIR.

Requires: pandas, numpy, scipy, statsmodels, openpyxl
"""

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.proportion import proportion_confint
from scipy import stats

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
FILES = {
    "ToT": "Results_Parameter_Combinations.xlsx",
    "CoT": "Results_Parameter_Combinations_CoT.xlsx",
}
# Reads the ToT/CoT Stage-2 workbooks straight from figures/figure_05/, so the
# raw data has a single home instead of a copy living next to the table code.
_HERE = os.path.dirname(os.path.abspath(__file__))
INDIR = os.path.join(_HERE, "..", "..", "figures", "figure_05")
OUTDIR = os.path.join(_HERE, "stage2_analysis_output")

# TTC = 1.7 s produced no overtaking decisions in any condition -> complete
# separation. Excluded from estimation, reported descriptively.
TTC_EXCLUDED = 1.7

# Reference levels for the categorical factors.
TTC_REF, F_REF = 3.4, 12.0

N_BOOT = 2000
ALPHA = 0.05
SEED = 20260903

# Final specification. Both continuous factors are categorical; the TTC x F
# interaction is retained (see manuscript Section 3.4.2).
FORMULA_FINAL = "Y ~ C(Tc, Treatment(%r))*C(Fc, Treatment(%r)) + B + Uh" % (TTC_REF, F_REF)
FORMULA_ADDITIVE = "Y ~ C(Tc, Treatment(%r)) + C(Fc, Treatment(%r)) + B + Uh" % (TTC_REF, F_REF)

os.makedirs(OUTDIR, exist_ok=True)
rng = np.random.default_rng(SEED)


# ----------------------------------------------------------------------------
# 1. Data loading and factor encoding
# ----------------------------------------------------------------------------
def load(path, strategy):
    """Read a Stage 2 workbook and encode the experimental factors.

    Traffic_Behind and Passenger_Hurry are stored as free text when the factor
    is present and blank when absent, so presence is encoded via notna().
    """
    df = pd.read_excel(path, usecols=[
        "Following_Time", "TTC", "Text_Version",
        "Traffic_Behind", "Passenger_Hurry", "Decision",
    ])
    df["B"] = df["Traffic_Behind"].notna().astype(int)    # vehicle behind
    df["Uh"] = df["Passenger_Hurry"].notna().astype(int)  # passenger urgency
    df["L"] = (df["Text_Version"] == "Limited").astype(int)  # 1 = few-sentences
    df["Tc"] = df["TTC"].astype(float)                    # TTC_o (s)
    df["Fc"] = df["Following_Time"].astype(float)         # following time (s)
    df["Y"] = df["Decision"].astype(int)                  # 1 = overtake
    df["strategy"] = strategy
    # experimental condition identifier (clustering unit)
    df["cond"] = [
        f"{t}_{f}_{l}_{b}_{u}"
        for t, f, l, b, u in zip(df.Tc, df.Fc, df.L, df.B, df.Uh)
    ]
    return df


def estimation_sample(df, regime=0):
    """No-limit regime, excluding the complete-separation TTC level."""
    return df[(df.L == regime) & (df.Tc != TTC_EXCLUDED)].copy()


# ----------------------------------------------------------------------------
# 2. Condition-level proportions with Wilson 95% intervals
# ----------------------------------------------------------------------------
def condition_proportions(df, strategy):
    """k_c / n_c per condition with a Wilson binomial confidence interval.

    The Wilson interval is used rather than the Wald interval because many
    conditions sit at or near 0 and 1, where the Wald interval is degenerate.
    """
    g = (df.groupby(["L", "Fc", "Tc", "B", "Uh"])["Y"]
           .agg(k="sum", n="count").reset_index())
    lo, hi = proportion_confint(g["k"], g["n"], alpha=ALPHA, method="wilson")
    g["p_hat"] = g["k"] / g["n"]
    g["wilson_lo"], g["wilson_hi"] = lo, hi
    g["strategy"] = strategy
    g["regime"] = np.where(g["L"] == 1, "few-sentences", "no-limit")
    return g


# ----------------------------------------------------------------------------
# 3. Floor / separation screening
# ----------------------------------------------------------------------------
def separation_report(df, strategy):
    rows = []
    for L in (0, 1):
        for T in sorted(df.Tc.unique()):
            s = df[(df.L == L) & (df.Tc == T)]
            rows.append({
                "strategy": strategy,
                "regime": "few-sentences" if L else "no-limit",
                "TTC_s": T, "k": int(s.Y.sum()), "n": len(s),
                "n_conditions": s.cond.nunique(),
                "n_zero_conditions": int((s.groupby("cond")["Y"].sum() == 0).sum()),
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 4. Specification screening
# ----------------------------------------------------------------------------
INTERACTIONS = {
    "TTC x F":  "C(Tc, Treatment(%r)):C(Fc, Treatment(%r))" % (TTC_REF, F_REF),
    "TTC x B":  "C(Tc, Treatment(%r)):B" % TTC_REF,
    "TTC x U":  "C(Tc, Treatment(%r)):Uh" % TTC_REF,
    "F x B":    "C(Fc, Treatment(%r)):B" % F_REF,
    "F x U":    "C(Fc, Treatment(%r)):Uh" % F_REF,
    "B x U":    "B:Uh",
}


def specification_screen(d, strategy):
    """Compare candidate specifications against the saturated condition model.

    The saturated model fits one parameter per experimental condition, so the
    deviance difference is a pure lack-of-fit test of the candidate.
    """
    sat = smf.glm("Y ~ C(cond)", data=d, family=sm.families.Binomial()).fit()
    add = smf.glm(FORMULA_ADDITIVE, data=d, family=sm.families.Binomial()).fit()

    rows = []

    def record(label, m):
        lof_dev = m.deviance - sat.deviance
        lof_df = int(m.df_resid - sat.df_resid)
        lr = add.deviance - m.deviance
        lr_df = int(add.df_resid - m.df_resid)
        rows.append({
            "strategy": strategy, "specification": label,
            "k_params": int(len(m.params)), "AIC": m.aic,
            "dAIC_vs_additive": m.aic - add.aic,
            "LR_vs_additive": lr if lr_df > 0 else np.nan,
            "LR_df": lr_df if lr_df > 0 else np.nan,
            "LR_p": stats.chi2.sf(lr, lr_df) if lr_df > 0 else np.nan,
            "lackoffit_dev": lof_dev, "lackoffit_df": lof_df,
            "lackoffit_p": stats.chi2.sf(lof_dev, lof_df) if lof_df > 0 else np.nan,
        })

    # linear-in-value specification (the original Equation 5 form)
    record("additive linear TTC & F",
           smf.glm("Y ~ Tc + Fc + B + Uh", data=d,
                   family=sm.families.Binomial()).fit())
    record("additive categorical", add)
    for label, term in INTERACTIONS.items():
        record("categorical + " + label,
               smf.glm(FORMULA_ADDITIVE + " + " + term, data=d,
                       family=sm.families.Binomial()).fit())
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 5. Final model: model-based SE, clustered SE, dispersion
# ----------------------------------------------------------------------------
def fit_final(d):
    naive = smf.glm(FORMULA_FINAL, data=d, family=sm.families.Binomial()).fit()
    clust = smf.glm(FORMULA_FINAL, data=d, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": d["cond"]})
    return naive, clust


def dispersion(d):
    """Grouped-binomial Pearson dispersion phi = X^2 / df_resid.

    Fitted on the aggregated (k_c, n_c) table, which is the grouped form of the
    same model; phi > 1 indicates extra-binomial variation between conditions.
    """
    g = (d.groupby(["Tc", "Fc", "B", "Uh"])["Y"]
           .agg(k="sum", n="count").reset_index())
    f = FORMULA_FINAL.replace("Y ~", "k + I(n - k) ~")
    m = smf.glm(f, data=g, family=sm.families.Binomial()).fit()
    return float(m.pearson_chi2 / m.df_resid), int(m.df_resid)


def interaction_wald(clust):
    """Joint Wald test of the TTC x F interaction block."""
    terms = [t for t in clust.params.index if ":" in t]
    ft = clust.f_test([f"{t} = 0" for t in terms])
    return float(ft.statistic), len(terms), float(ft.pvalue)


def coef_table(naive, clust, strategy):
    t = pd.DataFrame({
        "strategy": strategy,
        "beta": clust.params,
        "se_model": naive.bse,
        "se_cluster": clust.bse,
        "z": clust.tvalues,
        "p": clust.pvalues,
    })
    t["OR"] = np.exp(t["beta"])
    z = stats.norm.ppf(1 - ALPHA / 2)
    t["OR_lo"] = np.exp(t["beta"] - z * t["se_cluster"])
    t["OR_hi"] = np.exp(t["beta"] + z * t["se_cluster"])
    t["se_inflation"] = t["se_cluster"] / t["se_model"]
    return t.reset_index(names="term")


# ----------------------------------------------------------------------------
# 6. Condition-level bootstrap
# ----------------------------------------------------------------------------
def bootstrap(d, strategy, n_boot=N_BOOT):
    """Resample experimental conditions, stratified by TTC x F.

    Resampling conditions rather than individual generations preserves the
    repeated-measures structure. Stratifying by TTC x F keeps the factorial
    design balanced so that the specification stays estimable in every
    replicate.
    """
    strata = {key: [g for _, g in sub.groupby("cond")]
              for key, sub in d.groupby(["Tc", "Fc"])}
    draws, used = [], 0
    for _ in range(n_boot):
        parts = []
        for conds in strata.values():
            idx = rng.integers(0, len(conds), len(conds))
            parts.extend(conds[i] for i in idx)
        rep = pd.concat(parts, ignore_index=True)
        try:
            m = smf.glm(FORMULA_FINAL, data=rep,
                        family=sm.families.Binomial()).fit()
        except Exception:
            continue
        # discard replicates that hit separation
        if not np.isfinite(m.params).all() or np.abs(m.params).max() > 15:
            continue
        draws.append(m.params)
        used += 1
    draws = pd.DataFrame(draws)
    out = pd.DataFrame({
        "strategy": strategy,
        "term": draws.columns,
        "OR_boot_lo": np.exp(draws.quantile(ALPHA / 2).values),
        "OR_boot_hi": np.exp(draws.quantile(1 - ALPHA / 2).values),
        "n_replicates": used,
    })
    return out


# ----------------------------------------------------------------------------
# 7. Predicted probabilities at named profiles
# ----------------------------------------------------------------------------
PROFILES = [
    ("Reference (TTC 3.4 s, F 12 s, no rear, no urgency)", 3.4, 12.0, 0, 0),
    ("Large safety margin (TTC 8.5 s, F 12 s)",            8.5, 12.0, 0, 0),
    ("Rear vehicle present (TTC 3.4 s, F 12 s)",           3.4, 12.0, 1, 0),
    ("Passenger urgency (TTC 3.4 s, F 12 s)",              3.4, 12.0, 0, 1),
    ("Long following (TTC 3.4 s, F 24 s)",                 3.4, 24.0, 0, 0),
    ("Large margin + long following (TTC 8.5 s, F 24 s)",  8.5, 24.0, 0, 0),
]


def predicted_probabilities(clust, d, strategy):
    rows = []
    for label, T, F, B, Uv in PROFILES:
        nd = pd.DataFrame({"Tc": [T], "Fc": [F], "B": [B], "Uh": [Uv]})
        pr = clust.get_prediction(nd).summary_frame(alpha=ALPHA)
        obs = d[(d.Tc == T) & (d.Fc == F) & (d.B == B) & (d.Uh == Uv)]["Y"]
        rows.append({
            "strategy": strategy, "profile": label,
            "p_pred": pr["mean"][0],
            "p_lo": pr["mean_ci_lower"][0], "p_hi": pr["mean_ci_upper"][0],
            "p_observed": obs.mean(), "k": int(obs.sum()), "n": len(obs),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 8. Pooled thought-strategy comparison
# ----------------------------------------------------------------------------
def strategy_comparison(frames, reference="ToT"):
    """Pool strategies and interact the binary contextual factors with strategy.

    The TTC and F structure is held common across strategies; only the
    rear-vehicle and urgency effects are allowed to differ, since those are the
    effects under test.
    """
    d = pd.concat([estimation_sample(f) for f in frames], ignore_index=True)
    d["sc"] = d["strategy"] + "_" + d["cond"]
    f = (FORMULA_FINAL.replace(" + B + Uh", "")
         + ' + (B + Uh)*C(strategy, Treatment(%r))' % reference)
    m = smf.glm(f, data=d, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": d["sc"]})
    t = pd.DataFrame({"beta": m.params, "se": m.bse, "z": m.tvalues,
                      "p": m.pvalues}).reset_index(names="term")
    t["is_strategy_term"] = t["term"].str.contains("strategy")
    return t, d["sc"].nunique()


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    data = {s: load(os.path.join(INDIR, f), s) for s, f in FILES.items()}

    props, seps, screens, coefs, boots, preds = [], [], [], [], [], []

    for strategy, df in data.items():
        print("=" * 74)
        print(f"STRATEGY: {strategy}   (N = {len(df)} generations, "
              f"{df.cond.nunique()} conditions)")
        print("=" * 74)

        props.append(condition_proportions(df, strategy))
        sep = separation_report(df, strategy)
        seps.append(sep)
        print("\n-- Floor / separation screening --")
        print(sep.to_string(index=False))

        d = estimation_sample(df)
        print(f"\n-- Estimation sample: n = {len(d)}, "
              f"conditions = {d.cond.nunique()} --")

        sc = specification_screen(d, strategy)
        screens.append(sc)
        print("\n-- Specification screening --")
        print(sc.drop(columns="strategy").round(4).to_string(index=False))

        naive, clust = fit_final(d)
        phi, phi_df = dispersion(d)
        stat, k, p = interaction_wald(clust)
        print(f"\n-- Final model --")
        print(f"   grouped-binomial dispersion phi = {phi:.3f} (df = {phi_df})")
        print(f"   joint Wald test, TTC x F block: stat = {stat:.3f}, "
              f"df = {k}, p = {p:.4f}")
        ct = coef_table(naive, clust, strategy)
        coefs.append(ct)
        print(ct.drop(columns="strategy").round(3).to_string(index=False))

        print(f"\n-- Condition-level bootstrap ({N_BOOT} replicates) --")
        bt = bootstrap(d, strategy)
        boots.append(bt)
        print(bt.round(3).to_string(index=False))

        pp = predicted_probabilities(clust, d, strategy)
        preds.append(pp)
        print("\n-- Predicted probabilities --")
        print(pp.drop(columns="strategy").round(3).to_string(index=False))
        print()

    print("=" * 74)
    print("THOUGHT-STRATEGY COMPARISON (pooled, no-limit regime)")
    print("=" * 74)
    comp, n_clusters = strategy_comparison(list(data.values()))
    print(f"clusters (strategy x condition): {n_clusters}")
    print(comp[comp.is_strategy_term].drop(columns="is_strategy_term")
              .round(4).to_string(index=False))

    for name, frame in [
        ("condition_proportions_wilson", pd.concat(props)),
        ("separation_screen", pd.concat(seps)),
        ("specification_screen", pd.concat(screens)),
        ("final_model_coefficients", pd.concat(coefs)),
        ("bootstrap_intervals", pd.concat(boots)),
        ("predicted_probabilities", pd.concat(preds)),
        ("strategy_comparison", comp),
    ]:
        frame.to_csv(os.path.join(OUTDIR, name + ".csv"), index=False)
    print(f"\nCSV outputs written to {OUTDIR}/")


if __name__ == "__main__":
    main()
