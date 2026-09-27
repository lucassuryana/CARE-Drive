# CARE-Drive

> **CARE-Drive: A Framework for Evaluating Reason-Responsiveness of 
> Vision–Language Models in Automated Driving**  
> Lucas Elbert Suryana, Farah Bierenga, Sanne van Buuren, Pepijn Kooij, 
> Elsefien Tulleners, Federico Scari, Simeon Calvert, Bart van Arem, Arkady Zgonnikov  
> *Under review — Transportation Research Part C: Emerging Technologies*  
> Preprint available on arXiv: [2602.15645](https://arxiv.org/pdf/2602.15645)  
> Delft University of Technology
---

## Overview

CARE-Drive is a model-agnostic framework for evaluating **reason-responsiveness** in vision–language models (VLMs) applied to automated driving. It addresses a key limitation of existing evaluation methods: while most frameworks assess outcome-based metrics (e.g., collision rates, trajectory accuracy), they do not determine whether model decisions appropriately reflect human-relevant normative considerations — or whether explanations are merely post-hoc rationalizations.

CARE-Drive operationalizes the **tracking condition** of Meaningful Human Control (MHC), which requires that automated systems respond appropriately to the human-relevant reasons that justify their decisions.

The framework is applied to a cyclist overtaking scenario in which an automated vehicle (AV) must decide whether to overtake a cyclist on a road where crossing double solid centerlines is legally prohibited, creating a normative trade-off between safety, legality, efficiency, and comfort.

---

## Framework

CARE-Drive is structured as a **two-stage evaluation pipeline**:

### Stage 1 — Prompt Calibration
Identifies the model $M$ and thought strategy $T$ that produce stable, interpretable, and expert-aligned decisions under a fixed normatively challenging driving situation. This stage isolates prompt-level effects before any context-sensitivity analysis is performed.

### Stage 2 — Contextual Reasons Evaluation
Uses the calibrated configuration $(M^*, T^*)$ to systematically vary observable driving context variables — time-to-collision with oncoming vehicles, presence of a following vehicle, passenger urgency, and following duration behind the cyclist — and measures how sensitively human-augmented VLM decisions respond to these contextual changes.

**Calibration result:** The optimal configuration identified is `gpt-4.1` with Tree-of-Thought (ToT) prompting.

---

## Prompting Strategies

The file names encode the combination of prompting techniques used in each experiment:

| Abbreviation | Meaning |
|---|---|
| **Baseline** | Minimal prompt with no additional structure or reasoning guidance |
| **Role** | The LLM is assigned a specific role as a decision-making component within an AV system |
| **HR** | Human Reasons — the LLM is provided 11 expert-derived normative reasons to consider (e.g., safety, legality, efficiency, fairness, comfort), with safety assigned the highest priority |
| **CoT** | Chain of Thought — the LLM is prompted to reason step by step before reaching a decision |
| **ToT** | Tree of Thought — the LLM is prompted to explore multiple reasoning branches (overtake vs. stay behind) before converging on a decision |

---

## Project Structure

Everything produced by code lives under `figures/` or `tables/` -- one folder per figure, one
folder per table (or set of tables produced by a single script). A figure folder holds only what's
needed to draw that figure: the data-generating script, the resulting `.xlsx`, and the plotting
notebook. Where a table is computed from data that a figure folder already owns, the table's
folder holds just the analysis code and reads that data from its figure folder rather than keeping
a second copy.

```
CARE-Drive/
│
├── Images/                                # Input photos/diagrams fed to the VLM (not code output)
│   ├── scenario 1.jpg                     # Dashboard view: baseline and vehicle-behind scenarios
│   ├── scenario 2.jpg                     # Dashboard view: oncoming vehicle scenario
│   ├── scenario_addition.png              # Held-out speed-offset scenario view
│   ├── Distance oncoming vehicle to AV.png
│   └── TTCOncoming.png                    # Time-to-collision diagram for overtaking maneuver
│
├── figures/
│   │
│   ├── figure_05/                             # Stage 2 full-factorial evaluation
│   │   ├── ROLE + ToT + HR One Run.py         # Primary ToT run (3,600 obs)
│   │   ├── Results_Parameter_Combinations.xlsx
│   │   ├── ROLE + CoT + HR One Run.py         # CoT sensitivity check (Sec. 3.4.4)
│   │   ├── Results_Parameter_Combinations_CoT.xlsx
│   │   ├── overtaking_rate_calculation.ipynb      # Draws Fig. 5 (ToT)
│   │   └── overtaking_rate_calculation_CoT.ipynb  # CoT counterpart
│   │
│   ├── figure_06/                             # Prompt-component ablation, cross-model
│   │   ├── GPT4_ToT_Component_Ablation.py     # GPT-4.1, conditions A-E (1,200 obs)
│   │   ├── Results_Parameter_Combinations.xlsx
│   │   ├── Qwen_ToT_Component_Ablation.py     # Qwen3-VL-8B-Instruct cross-model check (400 obs)
│   │   ├── Results_Parameter_Combinations_Qwen.xlsx
│   │   ├── qwen_tot_ablation.sbatch            # DAIC cluster job for the Qwen script above
│   │   ├── overtaking_rate_figure_rev.ipynb    # Draws Fig. 6 (GPT-4.1, two-panel)
│   │   ├── overtaking_rate_figure_qwen.ipynb   # Qwen counterpart panel (not in the paper)
│   │   └── overtaking_rate_figure.ipynb        # Earlier alternative layout, superseded by *_rev
│   │
│   └── figure_A8/                         # Held-out speed-offset evaluation (Sec. 3.4.7, App. A)
│       ├── GPT4_ToT_SpeedCompliance_Ablation.py
│       ├── GPT4_ToT_Baseline_vs_CAREDrive.xlsx
│       ├── GPT4_speed_offset_figure.ipynb      # Draws Fig. A.8
│       ├── Qwen_ToT_SpeedCompliance_Ablation.py    # Exploratory Qwen counterpart, not in the paper
│       ├── Qwen_ToT_Baseline_vs_CAREDrive.xlsx
│       └── QWEN_speed_offset_figure.ipynb
│
├── tables/
│   │
│   └── table06-08_stage2_stats/           # Section 4.2 statistics (Tables 6-8)
│       ├── care_drive_stage2_analysis.py  # Reads figures/figure_05/*.xlsx directly, no data copy
│       └── logit.ipynb                    # Early prototype, superseded -- see Statistical analysis
│
├── Supplementary_R3.2/
│   └── openai_api_key.txt                 # Shared, gitignored OpenAI key used by every GPT-4.1 script
│
├── Table 3/                               # Stage 1 Step 1 screening (paper's Table 4) -- legacy,
│   │                                       # not touched/verified in the reproducibility pass above
│   ├── BB + Role + HR.py
│   ├── BB + Role + CoT + HR.py
│   └── BB + Role + ToT + HR.py
│
├── Table 4, 5, 6/                         # Stage 1 Step 2 sensitivity (paper's Table 5) -- same caveat
│   ├── ROLE + HR.py
│   ├── ROLE + CoT + HR.py
│   └── ROLE + ToT + HR.py
│
└── final_results_table_3_4_5_6.xlsx       # Manually aggregated summary, not produced by a script
```

Tables 9 and A.12 don't have a dedicated table-generating script -- the paper's numbers there are a
direct, un-transformed read of `figures/figure_06/Results_Parameter_Combinations*.xlsx` and
`figures/figure_A8/*_Baseline_vs_CAREDrive.xlsx` respectively (each figure's own notebook computes
the same grouped summary internally before plotting it).

---

## Setup

### Requirements

```bash
pip install openai openpyxl pandas numpy matplotlib
pip install torch transformers  # for the local Qwen3-VL-8B scripts
pip install statsmodels scipy   # for the Section 4.2 statistical analysis
```

### API Key

This project uses the OpenAI API. **Never hardcode your API key** in source files. Set it as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

To make this permanent, add the line above to your `~/.zshrc` or `~/.bashrc`.

---

## Running the Experiments

All scripts are designed to be run from the **project root directory** so that relative image paths
resolve correctly, even though the scripts themselves live inside `figures/<name>/` or
`tables/<name>/`. Each figure script writes its output Excel file next to itself, in the same folder.

**Stage 1 — Prompt Calibration (Tables 3, 4, 5, 6, legacy, unverified this pass):**
```bash
python "Table 3/BB + Role + CoT + HR.py"
python "Table 3/BB + Role + ToT + HR.py"
```

**Figure 5 (Stage 2 contextual evaluation):**
```bash
python "figures/figure_05/ROLE + ToT + HR One Run.py"   # primary (3,600 obs)
python "figures/figure_05/ROLE + CoT + HR One Run.py"   # sensitivity check (3,600 obs)
```

**Figure 6 (prompt-component ablation, cross-model):**
```bash
python "figures/figure_06/GPT4_ToT_Component_Ablation.py"
python "figures/figure_06/Qwen_ToT_Component_Ablation.py"   # run locally
```

**Figure A.8 (held-out speed-offset evaluation, Sec. 3.4.7, Appendix A):**
```bash
python "figures/figure_A8/GPT4_ToT_SpeedCompliance_Ablation.py"
```

**Tables 6-8 (Section 4.2 statistical analysis):**

```bash
python "tables/table06-08_stage2_stats/care_drive_stage2_analysis.py"
```

Reads `Results_Parameter_Combinations.xlsx` (ToT) and `Results_Parameter_Combinations_CoT.xlsx` (CoT)
directly from `figures/figure_05/` -- no separate copy of the data is kept next to the table code.
Reproduces, per reasoning strategy: Wilson 95% CIs per condition, complete-separation screening
(TTC = 1.7 s), the AIC/deviance specification screen (Table 6), the final grouped-binomial model with
clustered SEs and a dispersion parameter, a 2,000-replicate condition-level bootstrap for odds-ratio CIs
(Tables 7-8), predicted probabilities at named contextual profiles, and the pooled Strategy × Context
comparison (Sec. 4.2.3, Sec. 5.1). Verified to reproduce the paper's reported AIC values, odds ratios,
bootstrap CIs, and Strategy × {Rear-vehicle, Urgency} interaction coefficients exactly, run either from
the repo root or from inside its own folder. Requires `statsmodels` and `scipy` in addition to the base
requirements below. Writes CSV outputs to `tables/table06-08_stage2_stats/stage2_analysis_output/`
(regenerable, not tracked in the repo).

`tables/table06-08_stage2_stats/logit.ipynb` is an earlier, abandoned prototype (individual-level/
mixed-effects logistic regression on raw decisions) that does not implement this methodology -- kept
for history, not needed for reproduction, and its internal data path was not updated to match (it
never worked for this purpose to begin with).

Tables 9 and A.12 have no separate script -- open the corresponding figure's notebook in
`figures/figure_06/` or `figures/figure_A8/` and read the `panel_a`/`panel_b` (or equivalent grouped)
dataframe it computes just before plotting.

Each script runs 30 independent stochastic trials per experimental condition (10 for the Qwen cross-model
check, 20 for the speed-offset evaluation) and saves results incrementally to an Excel file.

---

## Experimental Variables (Stage 2)

| Variable | Description | Values |
|---|---|---|
| $TTC_o$ | Time-to-collision with oncoming vehicle | 1.7, 3.4, 5.1, 6.8, 8.5 s |
| $B$ | Vehicle behind indicator | 0 (absent), 1 (present) |
| $U$ | Passenger urgency indicator | 0 (none), 1 (in a hurry) |
| $F$ | Following time behind cyclist | 12, 18, 24 s |
| $L$ | Explanation length regime | No-Limit, Few-Sentences |

---

## Key Results

- Without explicit human reasons, the VLM **always stays behind** the cyclist (0% overtaking across all models and strategies), defaulting to strict legal compliance.
- Injecting human reasons shifts model behavior significantly: `gpt-4.1 + ToT` achieves **100% alignment** with expert recommendations in the baseline calibration scenario.
- Time-to-collision ($TTC_o$) is the strongest predictor of overtaking (odds ratio: 20.4), followed by rear-vehicle presence (odds ratio: 3.8).
- Constrained explanation length strongly suppresses overtaking, reducing probability from ~74% to near 0%.
- Passenger urgency unexpectedly *reduces* overtaking probability, contrary to human driver findings.
- Following time does not significantly influence overtaking decisions after controlling for other variables.

---

## CARLA Simulation

Selected conditions were validated in the CARLA simulator to confirm that calibrated decisions translate into physically executable AV behavior. A video demonstration is available at: https://elsefientulleners.wixsite.com/bep9

---

## Citation

If you use this code or framework in your research, please cite:

```bibtex
@article{suryana2026caredrive,
  title={CARE-Drive: A Framework for Evaluating Reason-Responsiveness 
         of Vision–Language Models in Automated Driving},
  author={Suryana, Lucas Elbert and Bierenga, Farah and van Buuren, Sanne 
          and Kooij, Pepijn and Tulleners, Elsefien and Scari, Federico 
          and Calvert, Simeon and van Arem, Bart and Zgonnikov, Arkady},
  journal={arXiv preprint arXiv:2602.15645},
  year={2025},
  note={Under review at Transportation Research Part C: Emerging Technologies}
}
```

---

## License

This project is intended for academic research purposes.
