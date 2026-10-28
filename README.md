# CARE-Drive

> **CARE-Drive: A Method for Evaluating Reason-Responsiveness of
> Vision–Language Models in Automated Driving**
> Lucas Elbert Suryana, Farah Bierenga, Sanne van Buuren, Pepijn Kooij,
> Elsefien Tulleners, Federico Scari, Simeon Craig Calvert, Bart van Arem, Arkady Zgonnikov
> *Under review — Transportation Research Part C: Emerging Technologies*
> Preprint: [arXiv 2602.15645](https://arxiv.org/pdf/2602.15645) · Delft University of Technology

This repository holds the experiment scripts, the archived model outputs, and
the analysis code behind the paper, plus a verification layer that recomputes
the reported numbers from the archived data without any API calls.

- **Reproduce the reported results:** [Quick start](#quick-start-reproduce-the-reported-results) (no API key, no GPU)
- **What maps to what:** [docs/experiments.md](docs/experiments.md) (every table and figure → data → script, with full experimental settings)
- **Audit findings and open discrepancies:** [docs/reproducibility_report.md](docs/reproducibility_report.md)

---

## What CARE-Drive does

Vision–language models (VLMs) used for driving decisions can produce plausible
explanations that are post-hoc rationalisations. CARE-Drive (Context-Aware Reasons
Evaluation for Driving) tests something different: whether the model's
*decisions* change systematically with observable context that is associated with
human-relevant reasons. This operationalises the tracking condition of Meaningful
Human Control as an input–output test that needs no access to model internals.

The method compares a baseline decision `D(0) = f(S, I(∅, T, L))` with a
reason-augmented decision `D(+R) = f(S, I(R, T, L))`. Here `S` = visual scene + observable
context, `R` = 11 expert-derived human reasons with conflict-resolution principles,
`T` = thought strategy, and `L` = explanation length.

The case study is a cyclist-overtaking scenario: an automated vehicle follows a
13 km/h cyclist on a road with double solid centre lines. Overtaking would violate
the rule but may be safe, more efficient and more comfortable.

**Stage 1 — exploratory configuration screening.**
- **Step 1 (Table 4)** screens 12 configurations under one fixed scene
  (Scenario 1, following time F = 24 s, Few-Sentences): 4 prompt configurations
  (Role; Role + HR; Role + HR + CoT; Role + HR + ToT) × 3 models (`gpt-4.1`,
  `-mini`, `-nano`), 30 runs each.
- **Step 2 (Table 5)** compares the retained `gpt-4.1` + CoT / ToT across three
  scenarios (none / oncoming / vehicle behind) and both explanation lengths.
- **Outcome:** (M\*, T\*) = (`gpt-4.1`, Tree-of-Thought).

**Stage 2 — contextual evaluation.** With (M\*, T\*) fixed, a full factorial varies
TTC to the oncoming vehicle, rear-vehicle presence, passenger urgency, following
time and explanation length: 120 cells × 30 = 3,600 generations (Fig. 5). These are
analysed with grouped-binomial logistic regression and a condition-level bootstrap
(Tables 6–8). The whole design is repeated with CoT as a sensitivity check.

**Further analyses.**
- **Prompt-component ablation** (Fig. 6, Table 9): five prompt conditions A–E remove the reason list, the principles and the planner safety assurance.
- **Cross-model check** with Qwen3-VL-8B-Instruct (Table 9).
- **Held-out speed-offset evaluation** (Fig. A.8, Table A.12).
- **CARLA proof of concept** (Table 10; its code is not in this repository).

### Prompt naming in file names

| Tag | Meaning |
|---|---|
| **Role** | Base role specification `Ibase`: "you are a modular decision-making component within an AV…" — present in every prompt |
| **HR** | Human Reasons `R`: the 11 reasons + key principles (system message) |
| **CoT / ToT** | Chain-of-Thought / Tree-of-Thought task instruction |
| `BB` (Table 4 scripts) | Historical prefix; these scripts all include HR |

The prompt text lives in the scripts themselves (string literals); there is no
separate prompt file.

---

## Repository structure

```
CARE-Drive/
├── Images/                         VLM inputs: scenario 1.jpg (Scen. 1/3), scenario 2.jpg +
│                                   TTCOncoming.png (Scen. 2, Stage 2, ablation),
│                                   scenario_addition.png (speed offset)
├── final_results_table_3_4_5_6.xlsx  Hand-compiled Stage 1 aggregates (Tables 4-5); the only
│                                   record of Stage 1 -- no per-run data exists
├── figures/
│   ├── figure_05/                  Stage 2: generator scripts (ToT, CoT), the two 3,600-row
│   │                               workbooks, care_drive_stage2_figures.py (Fig. 5 + CSV)
│   ├── figure_06/                  GPT-4.1 ablation: generator script, workbook (A-D used;
│   │                               see note on E), make_figure_06.py, original notebook
│   └── figure_A8/                  Speed offset: generator script, 160-row workbook, notebook
├── tables/
│   ├── table_04/                   Stage 1 Step 1 generator scripts (no archived output)
│   ├── table_05/                   Stage 1 Step 2 generator scripts (no archived output);
│   │                               ROLE + HR.py is an exploratory gpt-4.1-mini variant
│   ├── table_06-08/                care_drive_stage2_analysis.py + stage2_analysis_output/;
│   │                               logit.ipynb is an abandoned prototype kept for history
│   ├── table_09/                   Qwen ablation: script, 400-row workbook, SLURM job,
│   │                               Qwen-only figure (not in the paper)
│   └── table_A12/                  Qwen speed-offset run -- exploratory, NOT in the paper
├── reproduce/                      Recompute + verify every reported number (no API calls)
│   ├── results.py                  recomputation from the archived workbooks
│   ├── manuscript_values.py        the numbers printed in the paper
│   ├── verify.py, reproduce_all.py comparison and report
│   └── data_checksums.sha256       SHA-256 of all archived data and input images
├── tests/                          pytest regression tests (same checks)
├── docs/experiments.md             manuscript → data → script map + full protocols
├── docs/reproducibility_report.md  audit: verified / changed / unresolved
├── requirements.txt                analysis + verification (pinned, tested)
├── requirements-experiments.txt    + OpenAI / Qwen dependencies for rerunning
└── secrets/                        gitignored; put openai_api_key.txt here if you rerun
```

---

## Quick start: reproduce the reported results

Needs Python ≥ 3.10. Verified with Python 3.13.12 on Linux using the pinned
versions in `requirements.txt`. No API key, no GPU, no network.

```bash
git clone https://github.com/lucassuryana/CARE-Drive.git && cd CARE-Drive
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m reproduce.reproduce_all --stats   # ~1.5 min; all checks incl. Tables 6-8
pytest                                       # same checks as tests (~1.5 min)
pytest -m "not slow"                         # skip the regression/bootstrap (~10 s)
```

`reproduce_all` writes the recomputed tables and a check-by-check comparison with
the paper to `reproduce/output/verification.md`. Each check has one of four statuses:

| Status | Meaning |
|---|---|
| `MATCH` | Recomputed from per-generation data and equal at the printed precision |
| `RECORD_ONLY` | Equals the Stage 1 summary workbook, but there is no raw data to recompute it |
| `NOT_VERIFIABLE` | Neither raw data nor a record exists |
| `MISMATCH` | Differs from the paper; the three current ones are documented as D1–D3 in the [report](docs/reproducibility_report.md) |

The tests also check the archived data against `reproduce/data_checksums.sha256`, and
they pin the known mismatches. Any change to the data or to the reproduced numbers
therefore fails loudly.

### Individual figures and tables

Run from the repository root. Figure scripts write next to themselves.

| Output | Command |
|---|---|
| Fig. 5 (+ CoT counterpart, per-cell Wilson CSV) | `python figures/figure_05/care_drive_stage2_figures.py` |
| Tables 6–8, Sec. 4.2.3 | `python tables/table_06-08/care_drive_stage2_analysis.py` (CSVs → `tables/table_06-08/stage2_analysis_output/`) |
| Fig. 6 | `python figures/figure_06/make_figure_06.py` |
| Table 9 | `reproduce/output/table9_gpt.csv`, `table9_qwen.csv` (from `reproduce_all`) |
| Fig. A.8 | `pip install nbconvert ipykernel`, then `cd figures/figure_A8 && python -m jupyter nbconvert --to notebook --execute --output-dir /tmp GPT4_speed_offset_figure.ipynb` (the notebook must run from its own folder; it overwrites `speed_offset_two_panel.*` there) |
| Table A.12 | `reproduce/output/tableA12_gpt.csv` |
| Tables 4–5 | `reproduce/output/table4_stage1_record.csv`, `table5_stage1_record.csv` (record only) |

Notes on these outputs:
- The Stage 2 bootstrap is seeded (`SEED = 20260903`) and reproduces the published CIs exactly.
- **Fig. 6 / Table 9, Condition E** for GPT-4.1 is taken from the Stage 2 ToT data
  (F = 24 s, No-Limit, TTC ∈ {1.7, 8.5} s), as Sec. 3.4.5 describes. The E rows
  inside `figures/figure_06/Results_Parameter_Combinations.xlsx` come from a
  separate run and are not used in the paper (report, D1).
  `overtaking_rate_figure_rev.ipynb` hardcodes the E values;
  `make_figure_06.py` derives them and is the reproducible version.

---

## Rerunning the experiments (new API calls / GPU)

This is a separate workflow from the one above. A rerun draws a **new sample**:
- hosted models change over time;
- the OpenAI calls and the Qwen generation are not seeded;
- `gpt-4.1-nano` has been retired (it returned `404 model_not_found` on 2026-10-28).

Expect the same design, not the same responses or exactly the same rates.

```bash
pip install -r requirements-experiments.txt
export OPENAI_API_KEY=...        # or put the key in secrets/openai_api_key.txt (gitignored)
```

Run every script from the repository root (image paths are relative to it). New
results go to `<script folder>/reruns/` (gitignored), or to `$CARE_DRIVE_OUTPUT_DIR`,
so a rerun can never overwrite the archived workbooks.

| Experiment | Command | Calls |
|---|---|---|
| Table 4 (Role + HR, + CoT, + ToT) | `python "tables/table_04/BB + Role + HR.py"` (and `… CoT + HR.py`, `… ToT + HR.py`) | 90 each |
| Table 4 Role-only baseline | **no script in the repository** (report, D5) | — |
| Table 5 | `python "tables/table_05/ROLE + CoT + HR.py"`, `python "tables/table_05/ROLE + ToT + HR.py"` | 180 each |
| Stage 2 | `python "figures/figure_05/ROLE + ToT + HR One Run.py"` (and the CoT script) | 3,600 each |
| Ablation, GPT-4.1 | `RUNS_PER_COMBINATION=30 ONLY_CONDITION=A_000_baseline python figures/figure_06/GPT4_ToT_Component_Ablation.py`, likewise for B, C, D | 240 per condition |
| Ablation, Qwen | `python tables/table_09/Qwen_ToT_Component_Ablation.py` (or `sbatch tables/table_09/qwen_tot_ablation.sbatch`) | 400 local generations |
| Speed offset | `python figures/figure_A8/GPT4_ToT_SpeedCompliance_Ablation.py` | 160 |

Additional run controls and requirements:
- `MAX_RUNS=n` stops after n calls (smoke test).
- The Stage 2 and ablation scripts resume from `RESUME_FROM_RUN` (edit in the script).
- Qwen3-VL-8B-Instruct needs a CUDA GPU with roughly 20 GB of memory in bf16. The paper
  used an RTX 3090; the SLURM job targets an L40. It takes about 50–70 s per
  No-Limit generation.

Settings used by every overtaking experiment: temperature 0.1, top-p 0.9, and a
decision parsed by the first match of `decision:\s*case\s*[12]` (case 2 = overtake;
no match = `Unclear`). Per-experiment details (API, token limits, images,
contexts, output columns) are in [docs/experiments.md](docs/experiments.md).

---

## Interpreting the results

- **GPT-4.1 + ToT (Stage 2)** shows selective context sensitivity. Overtaking
  rises with TTC (OR 2.67–4.01 vs. 3.4 s at F = 12 s) and with a rear vehicle
  (OR 3.95). It falls with passenger urgency (OR 0.42), contrary to the
  human-behaviour motivation. TTC interacts with following time, and
  Few-Sentences responses almost never overtake.
- **CoT** reproduces the TTC and urgency directions, but not the rear-vehicle
  effect (OR 1.16). Reasoning strategy is part of the evaluated configuration.
- **Ablation:** under GPT-4.1, Conditions A–D never overtake (0/960). Overtaking
  appears only under the complete prompt and only at TTC 8.5 s. So the effect
  cannot be attributed to the reason list alone, nor to the safety assurance alone.
- **Qwen3-VL-8B-Instruct** never overtakes (0/400, one output unparseable). This
  shows a difference in observed action selection between the two models. It does
  **not** establish or rule out reason-responsiveness across model families, and
  it says nothing about which model is safer.
- **Speed offset:** the baseline prompt always holds the limit, while the complete
  prompt gives positive mean offsets, larger with a close rear vehicle. This is a
  limited held-out check (one scene, four contexts), not evidence of task
  generality.

## In the paper vs. exploratory

The paper uses everything mapped in [docs/experiments.md](docs/experiments.md)
§1. The following are **not** in the paper:
- `tables/table_A12/` (Qwen speed offset);
- `tables/table_09/overtaking_rate_figure_qwen.ipynb` and its figure files (a Qwen-only view; the paper reports Qwen only in Table 9);
- `tables/table_05/ROLE + HR.py`;
- the CoT version of Fig. 5 (`fig5_CoT_wilson.*`);
- `tables/table_06-08/logit.ipynb`;
- the Condition E rows inside the GPT-4.1 ablation workbook.

## Known limitations to reproducibility

- **Stage 1 (Tables 4–5):** only aggregate counts survive; no per-run responses.
  The Role-only baseline has no script, and `gpt-4.1-nano` is retired.
- **Stochasticity and drift:** reruns sample a possibly updated hosted model
  without a seed.
- **Implementation differences:** the paper's ablation Condition E (Responses API)
  and Conditions A–D (Chat Completions, `max_tokens` 2048) differ in API and
  minor prompt wording (report, D1).
- **CARLA demo:** not included.

Full details and the remaining manuscript discrepancies are in
[docs/reproducibility_report.md](docs/reproducibility_report.md).

---

## Citation

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

A video of the CARLA demonstration is at https://doi.org/10.4121/ed2fd9ef-3814-4beb-a888-75f267974297.

## License

This project is intended for academic research purposes.
