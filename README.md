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

```
CARE-Drive/
│
├── Images/
│   ├── scenario 1.jpg                     # Dashboard view: baseline and vehicle-behind scenarios
│   ├── scenario 2.jpg                     # Dashboard view: oncoming vehicle scenario
│   ├── Distance oncoming vehicle to AV.png
│   └── TTCOncoming.png                    # Time-to-collision diagram for overtaking maneuver
│
├── Table 3/                               # Stage 1 calibration: model and thought strategy screening
│   ├── BB + Role + HR.py                  # Baseline + Role + Human Reasons (No-Thought)
│   ├── BB + Role + CoT + HR.py            # Baseline + Role + Chain-of-Thought + Human Reasons
│   └── BB + Role + ToT + HR.py            # Baseline + Role + Tree-of-Thought + Human Reasons
│
├── Table 4, 5, 6/                         # Stage 1 robustness: varied scenarios and explanation length
│   ├── ROLE + HR.py
│   ├── ROLE + CoT + HR.py
│   └── ROLE + ToT + HR.py
│
├── Table 7/                               # Stage 2 contextual evaluation (Fig. 5, Tables 6-8)
│   ├── ROLE + ToT + HR One Run.py         # Primary ToT full-factorial run (3,600 obs)
│   ├── Results_Parameter_Combinations.xlsx
│   ├── ROLE + CoT + HR One Run.py         # CoT sensitivity check (Sec. 3.4.4, Table 8; 3,600 obs)
│   ├── Results_Parameter_Combinations_CoT.xlsx
│   ├── overtaking_rate_calculation.ipynb  # ToT overtaking-rate computation and visualization
│   ├── overtaking_rate_calculation_CoT.ipynb  # CoT counterpart of the above
│   ├── logit.ipynb                        # Early prototype, superseded -- see Statistical analysis
│   └── care_drive_stage2_analysis.py      # Section 4.2 statistical analysis (Tables 6-8)
│
├── Supplementary_R3.2/                    # Prompt-component ablation (Table 3, Fig. 6, Table 9)
│   ├── GPT4_ToT_Component_Ablation.py     # GPT-4.1, conditions A-E (1,200 obs)
│   ├── Qwen_ToT_Component_Ablation.py     # Qwen3-VL-8B-Instruct cross-model check (400 obs)
│   ├── GPT4_ToT_SpeedCompliance_Ablation.py   # Held-out speed-offset eval (Sec. 3.4.7, App. A)
│   ├── Qwen_ToT_SpeedCompliance_Ablation.py   # Same eval on Qwen -- exploratory, not in the paper
│   └── qwen_tot_ablation.sbatch           # DAIC cluster job for the Qwen ablation
│
├── Result Table 3 New/                    # Ablation results and plotting notebooks (GPT-4.1 + Qwen)
│   ├── Results_Parameter_Combinations.xlsx        # GPT-4.1, matches Table 9's GPT-4.1 column
│   └── Results_Parameter_Combinations_Qwen.xlsx   # Qwen3-VL-8B, matches Table 9's Qwen column
│
├── Result Speed Offset Held-Out Evaluation/
│   ├── GPT4_ToT_Baseline_vs_CAREDrive.xlsx        # Matches Table A.12 / Fig. A.8 exactly
│   └── Qwen_ToT_Baseline_vs_CAREDrive.xlsx        # Exploratory Qwen counterpart, not in the paper
│
└── final_results_table_3_4_5_6.xlsx       # Aggregated results from Stage 1
```

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

All scripts are designed to be run from the **project root directory** so that relative image paths resolve correctly.

**Stage 1 — Prompt Calibration (Tables 3, 4, 5, 6):**
```bash
python "Table 3/BB + Role + CoT + HR.py"
python "Table 3/BB + Role + ToT + HR.py"
```

**Stage 2 — Contextual Evaluation (Table 7, Fig. 5):**
```bash
python "Table 7/ROLE + ToT + HR One Run.py"        # primary configuration (Tables 6-7)
python "Table 7/ROLE + CoT + HR One Run.py"        # reasoning-strategy sensitivity check (Table 8)
```

**Prompt-component ablation (Table 3, Fig. 6, Table 9):**
```bash
python Supplementary_R3.2/GPT4_ToT_Component_Ablation.py
python Supplementary_R3.2/Qwen_ToT_Component_Ablation.py     # cross-model check, run locally
```

**Held-out speed-offset evaluation (Sec. 3.4.7, Appendix A):**
```bash
python Supplementary_R3.2/GPT4_ToT_SpeedCompliance_Ablation.py
```

**Statistical analysis (Section 4.2, Tables 6-8):**

```bash
cd "Table 7"
python care_drive_stage2_analysis.py
```

Reads `Results_Parameter_Combinations.xlsx` (ToT) and `Results_Parameter_Combinations_CoT.xlsx` (CoT)
from the current directory. Reproduces, per reasoning strategy: Wilson 95% CIs per condition,
complete-separation screening (TTC = 1.7 s), the AIC/deviance specification screen (Table 6), the final
grouped-binomial model with clustered SEs and a dispersion parameter, a 2,000-replicate condition-level
bootstrap for odds-ratio CIs (Tables 7-8), predicted probabilities at named contextual profiles, and the
pooled Strategy × Context comparison (Sec. 4.2.3, Sec. 5.1). Verified to reproduce the paper's reported
AIC values, odds ratios, bootstrap CIs, and Strategy × {Rear-vehicle, Urgency} interaction coefficients
exactly. Requires `statsmodels` and `scipy` in addition to the base requirements below. Writes CSV
outputs to `Table 7/stage2_analysis_output/` (regenerable, not tracked in the repo).

`Table 7/logit.ipynb` is an earlier, abandoned prototype (individual-level/mixed-effects logistic
regression on raw decisions) that does not implement this methodology -- kept for history, not needed
for reproduction.

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
