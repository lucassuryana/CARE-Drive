# CARE-Drive

**CARE-Drive** (Context-Aware Reasons Evaluation for Driving) is the official implementation for the paper:

> **CARE-Drive: A Framework for Evaluating Reason-Responsiveness of Vision–Language Models in Automated Driving**  
> Lucas Elbert Suryana, Farah Bierenga, Sanne van Buuren, Pepijn Kooij, Elsefien Tulleners, Federico Scari, Simeon Calvert, Bart van Arem, Arkady Zgonnikov  
> *Transportation Research Part C: Emerging Technologies*  
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
| **HR** | Human Reasons — the LLM is provided 13 expert-derived normative reasons to consider (e.g., safety, legality, efficiency, fairness, comfort), with safety assigned the highest priority |
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
├── Table 7/                               # Stage 2 contextual evaluation
│   ├── ROLE + ToT + HR One Run.py         # Full-factorial contextual sensitivity experiments
│   ├── Results_Parameter_Combinations.xlsx
│   ├── logit.ipynb                        # Binary logistic regression analysis
│   └── overtaking_rate_calculation.ipynb  # Overtaking rate computation and visualization
│
└── final_results_table_3_4_5_6.xlsx       # Aggregated results from Stage 1
```

---

## Setup

### Requirements

```bash
pip install openai openpyxl
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

**Stage 2 — Contextual Evaluation (Table 7):**
```bash
python "Table 7/ROLE + ToT + HR One Run.py"
```

**Statistical analysis:**

Open `Table 7/logit.ipynb` in Jupyter Notebook to run the binary logistic regression and reproduce the odds ratio and probability results.

Each script runs 30 independent stochastic trials per experimental condition and saves results incrementally to an Excel file.

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
  title={CARE-Drive: A Framework for Evaluating Reason-Responsiveness of Vision–Language Models in Automated Driving},
  author={Suryana, Lucas Elbert and Bierenga, Farah and van Buuren, Sanne and Kooij, Pepijn and Tulleners, Elsefien and Scari, Federico and Calvert, Simeon and van Arem, Bart and Zgonnikov, Arkady},
  journal={Transportation Research Part C: Emerging Technologies},
  year={2026}
}
```

---

## License

This project is intended for academic research purposes.