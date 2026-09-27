# CARE-Drive

> **CARE-Drive: A Method for Evaluating Reason-Responsiveness of 
> Vision–Language Models in Automated Driving**  
> Lucas Elbert Suryana, Farah Bierenga, Sanne van Buuren, Pepijn Kooij, 
> Elsefien Tulleners, Federico Scari, Simeon Craig Calvert, Bart van Arem, Arkady Zgonnikov  
> *Under review — Transportation Research Part C: Emerging Technologies*  
> Preprint available on arXiv: [2602.15645](https://arxiv.org/pdf/2602.15645)  
> Delft University of Technology
---

## Overview

CARE-Drive is a model-agnostic method for evaluating **reason-responsiveness** in vision–language models (VLMs) applied to automated driving. It addresses a key limitation of existing evaluation methods: while most methods assess outcome-based metrics (e.g., collision rates, trajectory accuracy), they do not determine whether model decisions appropriately reflect human-relevant normative considerations — or whether explanations are merely post-hoc rationalizations.

CARE-Drive operationalizes the **tracking condition** of Meaningful Human Control (MHC), which requires that automated systems respond appropriately to the human-relevant reasons that justify their decisions.

The method is applied to a cyclist overtaking scenario in which an automated vehicle (AV) must decide whether to overtake a cyclist on a road where crossing double solid centerlines is legally prohibited, creating a normative trade-off between safety, legality, efficiency, and comfort. Beyond the core two-stage pipeline below, the study also runs a prompt-component ablation (isolating which parts of the CARE-Drive prompt drive the effect), a cross-model check against Qwen3-VL-8B-Instruct, and a held-out speed-offset evaluation to test whether reason-responsiveness generalizes beyond the binary overtake/stay-behind decision.

---

## Framework

CARE-Drive is structured as a **two-stage evaluation pipeline**:

### Stage 1 — Exploratory Configuration Screening
Compares candidate model $M$ and thought-strategy $T$ configurations under fixed screening conditions, based on output consistency, acknowledgement of the normative conflict, and agreement with an expert-reference decision. Step 1 screens $(M, T)$ under a fixed baseline scenario; Step 2 evaluates the retained configurations' sensitivity across three driving scenarios and both explanation-length regimes. This stage explains why a configuration is selected — it does not show that the configuration will also agree with experts in other driving situations.

### Stage 2 — Contextual (Reasons) Evaluation
Holds the retained configuration $(M^*, T^*)$ fixed and systematically varies observable driving context — time-to-collision with an oncoming vehicle, presence of a following vehicle, passenger urgency, and following time behind the cyclist — together with the explanation-length regime, to evaluate how sensitively reason-augmented VLM decisions respond to these contextual changes.

**Retained configuration:** Stage 1 retains $(M^*, T^*) = ($`gpt-4.1`$,$ Tree-of-Thought$)$ for Stage 2.

### Further analyses on top of Stage 2

- **Prompt-component ablation** (Fig. 6, Table 9) — removes/combines the baseline, safety, human-reasons, and principles components of the prompt to check whether the context-sensitivity found in Stage 2 requires the full CARE-Drive prompt or is driven by a subset of it.
- **Cross-model check** (Table 9) — repeats the ablation with Qwen3-VL-8B-Instruct to see whether the effect is specific to `gpt-4.1`.
- **Held-out speed-offset evaluation** (Fig. A.8, Table A.12, Appendix A) — holds the Stage 1 configuration fixed and tests reason-responsiveness on a continuous speed-adjustment decision it was not selected on, rather than the binary overtake/stay-behind decision.

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
│   │   ├── Results_Parameter_Combinations_ToT.xlsx
│   │   ├── ROLE + CoT + HR One Run.py         # CoT sensitivity check (Sec. 3.4.4)
│   │   ├── Results_Parameter_Combinations_CoT.xlsx
│   │   ├── care_drive_stage2_figures.py       # Draws Fig. 5 (ToT + CoT), with Wilson 95% CI error bars
│   │   └── stage2_condition_proportions_wilson.csv  # Per-condition rate + Wilson interval behind Fig. 5
│   │
│   ├── figure_06/                             # Prompt-component ablation (GPT-4.1 only, per its caption)
│   │   ├── GPT4_ToT_Component_Ablation.py     # GPT-4.1, conditions A-E (1,200 obs)
│   │   ├── Results_Parameter_Combinations.xlsx
│   │   └── overtaking_rate_figure_rev.ipynb   # Draws Fig. 6 (two-panel)
│   │
│   └── figure_A8/                         # Held-out speed-offset evaluation (Sec. 3.4.7, App. A) --
│       │                                   # GPT-4.1 only, matching both Fig. A.8 and Table A.12
│       ├── GPT4_ToT_SpeedCompliance_Ablation.py
│       ├── GPT4_ToT_Baseline_vs_CAREDrive.xlsx
│       └── GPT4_speed_offset_figure.ipynb      # Draws Fig. A.8
│
├── tables/
│   │
│   ├── table_04/                          # Stage 1 Step 1 screening (paper's Table 4) -- not
│   │   │                                   # touched/verified in the reproducibility pass above
│   │   ├── BB + Role + HR.py
│   │   ├── BB + Role + CoT + HR.py
│   │   └── BB + Role + ToT + HR.py
│   │
│   ├── table_05/                          # Stage 1 Step 2 sensitivity (paper's Table 5) -- same caveat
│   │   ├── ROLE + HR.py
│   │   ├── ROLE + CoT + HR.py
│   │   └── ROLE + ToT + HR.py
│   │
│   ├── table_06-08/           # Section 4.2 statistics (Tables 6-8)
│   │   ├── care_drive_stage2_analysis.py  # Reads figures/figure_05/*.xlsx directly, no data copy
│   │   └── logit.ipynb                    # Early prototype, superseded -- see Statistical analysis
│   │
│   ├── table_09/                          # Cross-model ablation comparison (Sec. 4.2.5) -- the Qwen
│   │   │                                   # half; the GPT-4.1 half lives in figures/figure_06/
│   │   ├── Qwen_ToT_Component_Ablation.py
│   │   ├── Results_Parameter_Combinations_Qwen.xlsx
│   │   ├── qwen_tot_ablation.sbatch         # DAIC cluster job for the script above
│   │   ├── overtaking_rate_figure_qwen.ipynb    # Qwen-only two-panel view (not itself in the paper)
│   │   └── overtaking_two_panel_qwen.png/.pdf/.svg
│   │
│   └── table_A12/                         # Qwen counterpart to the speed-offset eval -- note that,
│       │                                   # unlike Table 9, the paper's actual Table A.12 has no
│       │                                   # Qwen column; this whole folder is exploratory
│       ├── Qwen_ToT_SpeedCompliance_Ablation.py
│       ├── Qwen_ToT_Baseline_vs_CAREDrive.xlsx
│       └── QWEN_speed_offset_figure.ipynb
│
├── secrets/
│   └── openai_api_key.txt                 # Shared, gitignored OpenAI key used by every GPT-4.1 script
│
└── final_results_table_3_4_5_6.xlsx       # Manually compiled source data behind the paper's published
                                            # Table 4 and Table 5 -- not produced by a script, and the
                                            # only existing record to verify tables/table_04/table_05
                                            # against, since those two haven't been re-verified yet
```

Neither Table 9 nor Table A.12 has a script that assembles the actual table layout -- the paper's
numbers are a direct, un-transformed read of the underlying `.xlsx` files. For Table 9 that means
`figures/figure_06/Results_Parameter_Combinations.xlsx` (GPT-4.1) and
`tables/table_09/Results_Parameter_Combinations_Qwen.xlsx` (Qwen) side by side; for Table A.12,
`figures/figure_A8/GPT4_ToT_Baseline_vs_CAREDrive.xlsx` alone (Table A.12 has no Qwen column in the
paper -- see `tables/table_A12/` above). Each relevant notebook computes the same grouped summary
internally, right before plotting it.

---

## Setup

### Requirements

```bash
pip install openai openpyxl pandas numpy matplotlib
pip install torch transformers  # for the local Qwen3-VL-8B scripts
pip install statsmodels scipy   # for the Section 4.2 statistical analysis
```

### API Key

This project uses the OpenAI API. **Never hardcode your API key** in source files. Every GPT-4.1
script checks the `OPENAI_API_KEY` environment variable first, then falls back to a local,
gitignored key file -- pick whichever is more convenient:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

To make this permanent, add the line above to your `~/.zshrc` or `~/.bashrc`. Or, simpler for local
use: create `secrets/openai_api_key.txt` containing just your key on one line -- that file is
`.gitignore`d, doesn't ship with a fresh clone, and can never be committed by accident.

---

## Running the Experiments

All scripts are designed to be run from the **project root directory** so that relative image paths
resolve correctly, even though the scripts themselves live inside `figures/<name>/` or
`tables/<name>/`. Each figure script writes its output Excel file next to itself, in the same folder.

**Stage 1 — Exploratory Configuration Screening (Tables 4-5, legacy, unverified this pass):**
```bash
python "tables/table_04/BB + Role + CoT + HR.py"
python "tables/table_04/BB + Role + ToT + HR.py"
python "tables/table_05/ROLE + CoT + HR.py"
python "tables/table_05/ROLE + ToT + HR.py"
```

**Figure 5 (Stage 2 contextual evaluation):**
```bash
python "figures/figure_05/ROLE + ToT + HR One Run.py"   # primary (3,600 obs)
python "figures/figure_05/ROLE + CoT + HR One Run.py"   # sensitivity check (3,600 obs)
python "figures/figure_05/care_drive_stage2_figures.py" # draws Fig. 5 with Wilson 95% CIs
```

**Figure 6 (prompt-component ablation, GPT-4.1):**
```bash
python "figures/figure_06/GPT4_ToT_Component_Ablation.py"
```

**Table 9 (cross-model comparison, Sec. 4.2.5) -- Qwen half:**
```bash
python "tables/table_09/Qwen_ToT_Component_Ablation.py"   # run locally
```

**Figure A.8 / Table A.12 (held-out speed-offset evaluation, Sec. 3.4.7, Appendix A):**
```bash
python "figures/figure_A8/GPT4_ToT_SpeedCompliance_Ablation.py"
```

**Table A.12 folder, Qwen counterpart (not in the paper):** the Appendix A speed-offset evaluation
has no Qwen column in the paper (unlike Table 9, which does) -- this is exploratory work done
alongside it.
```bash
python "tables/table_A12/Qwen_ToT_SpeedCompliance_Ablation.py"   # run locally
```

**Tables 6-8 (Section 4.2 statistical analysis):**

```bash
python "tables/table_06-08/care_drive_stage2_analysis.py"
```

Reads `Results_Parameter_Combinations_ToT.xlsx` (ToT) and `Results_Parameter_Combinations_CoT.xlsx` (CoT)
directly from `figures/figure_05/` -- no separate copy of the data is kept next to the table code.
Reproduces, per reasoning strategy: Wilson 95% CIs per condition, complete-separation screening
(TTC = 1.7 s), the AIC/deviance specification screen (Table 6), the final grouped-binomial model with
clustered SEs and a dispersion parameter, a 2,000-replicate condition-level bootstrap for odds-ratio CIs
(Tables 7-8), predicted probabilities at named contextual profiles, and the pooled Strategy × Context
comparison (Sec. 4.2.3, Sec. 5.1). Verified to reproduce the paper's reported AIC values, odds ratios,
bootstrap CIs, and Strategy × {Rear-vehicle, Urgency} interaction coefficients exactly, run either from
the repo root or from inside its own folder. Requires `statsmodels` and `scipy` in addition to the base
requirements below. Writes CSV outputs to `tables/table_06-08/stage2_analysis_output/`
(regenerable, not tracked in the repo).

`tables/table_06-08/logit.ipynb` is an earlier, abandoned prototype (individual-level/
mixed-effects logistic regression on raw decisions) that does not implement this methodology -- kept
for history, not needed for reproduction, and its internal data path was not updated to match (it
never worked for this purpose to begin with).

Tables 9 and A.12 have no dedicated table-assembling script. For Table 9, its GPT-4.1 half is
computed inline in `figures/figure_06/overtaking_rate_figure_rev.ipynb` and its Qwen half inline in
`tables/table_09/overtaking_rate_figure_qwen.ipynb` (each notebook's `panel_a`/`panel_b` dataframe,
just before plotting) -- the two need to be placed side by side by hand to get Table 9's layout. For
Table A.12, open `figures/figure_A8/`'s notebook and read the same kind of grouped dataframe there.

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

- `gpt-4.1 + ToT` shows selective, context-sensitive reason-responsiveness in Stage 2: overtaking probability moves with $TTC_o$ and rear-vehicle presence in the directions expert reasoning would predict.
- Time-to-collision ($TTC_o$) is the strongest predictor of overtaking, with odds ratios of roughly 2.7–4.0 for $TTC_o \geq 6.8$ s vs. the 3.4 s reference; rear-vehicle presence has an odds ratio of 3.95. Passenger urgency *reduces* overtaking probability (odds ratio 0.42), contrary to the direction human-driver findings would suggest.
- The prompt-component ablation (Fig. 6, Table 9) shows this responsiveness depends on the complete CARE-Drive prompt — no single component (e.g., the human-reasons list alone) reproduces it.
- The cross-model check (Table 9) shows Qwen3-VL-8B-Instruct does not replicate this behavior: it stays behind the cyclist across all ablation conditions, unlike `gpt-4.1`.
- The held-out speed-offset evaluation (Fig. A.8, Table A.12) shows the complete CARE-Drive prompt produces positive speed deviations from the posted limit where the baseline prompt does not, suggesting the effect generalizes beyond the binary overtake decision.
- Constrained explanation length ("few-sentences") suppresses overtaking relative to "no-limit" explanations across the factorial design.
- Exact figures (odds ratios, bootstrap CIs, AIC/deviance values) are reproduced by `tables/table_06-08/care_drive_stage2_analysis.py` — see Tables 6-8 in the paper.

---

## CARLA Simulation

The retained CARE-Drive configuration `(gpt-4.1, Tree-of-Thought)` was integrated into the CARLA simulator as a proof-of-concept, to confirm that its decisions translate into physically executable AV behavior. A video demonstration is available at: https://doi.org/10.4121/ed2fd9ef-3814-4beb-a888-75f267974297

---

## Citation

If you use this code or method in your research, please cite:

```bibtex
@article{suryana2026caredrive,
  title={CARE-Drive: A Method for Evaluating Reason-Responsiveness 
         of Vision–Language Models in Automated Driving},
  author={Suryana, Lucas Elbert and Bierenga, Farah and van Buuren, Sanne 
          and Kooij, Pepijn and Tulleners, Elsefien and Scari, Federico 
          and Calvert, Simeon Craig and van Arem, Bart and Zgonnikov, Arkady},
  journal={arXiv preprint arXiv:2602.15645},
  year={2026},
  note={Under review at Transportation Research Part C: Emerging Technologies}
}
```

---

## License

This project is intended for academic research purposes.
