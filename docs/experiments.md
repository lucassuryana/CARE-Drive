# Experiments: protocol and manuscript mapping

This page records, for every experiment in the manuscript, which script
generated it, which archived file holds its output, and the exact settings the
script uses. Where the archived data shows something the script does not (or
vice versa), it is noted here and discussed in
[reproducibility_report.md](reproducibility_report.md).

## 1. Manuscript → source mapping

| Manuscript item | Archived data | Generating script | Reproduced by | Status |
|---|---|---|---|---|
| Table 4 (Stage 1 Step 1, 12 configurations) | `final_results_table_3_4_5_6.xlsx` (hand-compiled aggregates, no per-run data) | `tables/table_04/BB + Role + HR.py`, `… + CoT + HR.py`, `… + ToT + HR.py`; **no script for the Role-only baseline** | `reproduce/results.py::stage1_record` | Matches record; not recomputable |
| Table 5 (Stage 1 Step 2) | `final_results_table_3_4_5_6.xlsx` (aggregates only) | `tables/table_05/ROLE + CoT + HR.py`, `ROLE + ToT + HR.py` | `stage1_record` | Matches record; not recomputable |
| Sec. 4.1.3 legal-acknowledgement check (180 + 180 outputs) | none | — | — | Not verifiable |
| Fig. 5 (Stage 2, ToT) | `figures/figure_05/Results_Parameter_Combinations_ToT.xlsx` (3,600 rows) | `figures/figure_05/ROLE + ToT + HR One Run.py` | `figures/figure_05/care_drive_stage2_figures.py` | Verified |
| Sec. 3.4.4 / Table 8 CoT sensitivity | `figures/figure_05/Results_Parameter_Combinations_CoT.xlsx` (3,600 rows) | `figures/figure_05/ROLE + CoT + HR One Run.py` | as above | Verified |
| Tables 6, 7, 8; Sec. 4.2.3 interactions | Stage 2 workbooks above | — | `tables/table_06-08/care_drive_stage2_analysis.py` | Verified |
| Fig. 6, Table 9 (GPT-4.1, Conditions A–D) | `figures/figure_06/Results_Parameter_Combinations.xlsx` (A–D rows) | `figures/figure_06/GPT4_ToT_Component_Ablation.py` | `figures/figure_06/make_figure_06.py`, `reproduce/results.py::ablation_table` | Verified |
| Fig. 6, Table 9 (GPT-4.1, Condition E) | Stage 2 ToT workbook, F = 24 s, no-limit, TTC ∈ {1.7, 8.5} | `figures/figure_05/ROLE + ToT + HR One Run.py` | same | Verified (see D1) |
| Table 9 (Qwen3-VL-8B-Instruct) | `tables/table_09/Results_Parameter_Combinations_Qwen.xlsx` (400 rows) | `tables/table_09/Qwen_ToT_Component_Ablation.py` | `ablation_table("qwen")` | Verified (see D2) |
| Fig. A.8, Table A.12, Sec. 4.2.6 | `figures/figure_A8/GPT4_ToT_Baseline_vs_CAREDrive.xlsx` (160 rows) | `figures/figure_A8/GPT4_ToT_SpeedCompliance_Ablation.py` | `figures/figure_A8/GPT4_speed_offset_figure.ipynb`, `speed_offset_table` | Verified (see D4) |
| Table 10 (CARLA demo) | not in this repository | not in this repository | — | Not verifiable |
| — (exploratory, not in the paper) | `tables/table_A12/Qwen_ToT_Baseline_vs_CAREDrive.xlsx` | `tables/table_A12/Qwen_ToT_SpeedCompliance_Ablation.py` | `tables/table_A12/QWEN_speed_offset_figure.ipynb` | — |
| — (exploratory, not in the paper) | none | `tables/table_05/ROLE + HR.py` (gpt-4.1-mini, no thought strategy) | — | — |

Every "Verified" row is checked automatically by `python -m reproduce.reproduce_all --stats`
and by `pytest`.

## 2. Shared elements

**Decision parsing (all overtaking experiments).** The first match of
`decision:\s*case\s*[12]` (case-insensitive) in the response is the decision:
`case 2` → `1` (overtake), `case 1` → `0` (stay behind); no match → `"Unclear"`;
an API exception → `"Error"`. Re-applying this rule to every archived response
reproduces every stored `Decision` value (Stage 2, ablation, Qwen).

**Factor encoding in the workbooks.** `Traffic_Behind` is `"None"` or
`"One vehicle behind at 10 m distance"`; `Passenger_Hurry` is `""` or
`"in hurry"`. pandas reads `"None"` and `""` as missing, so presence is
`notna()`. `Text_Version` is `Unlimited` (No-Limit) or `Limited` (Few-Sentences).

**Explanation-length instruction.** No-Limit appends
`ONLY PRINT the FINAL ACTION and YOUR JUSTIFICATION` plus the CoT/ToT response
template; Few-Sentences appends `… in FEW SENTENCES` and omits the template.

**Prompt text.** The prompts are the string literals inside each script; they
are not stored separately, so the script *is* the prompt record. The system
message holds the role (`Ibase`), the 11 human reasons and the key principles;
the user message holds the situation, the image(s) and the task.

**Randomness.** Sampling is stochastic (temperature 0.1, top-p 0.9). OpenAI
calls are not seeded and Qwen generation does not call `torch.manual_seed`,
so a rerun estimates the same conditional decision distribution but cannot
reproduce individual historical responses. The Stage 2 bootstrap is seeded
(`SEED = 20260903`).

## 3. Per-experiment protocol

### Stage 1, Step 1 — configuration screening (Table 4)

| | |
|---|---|
| Models | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano` (OpenAI Responses API) |
| Prompt configurations | Role; Role + HR; Role + HR + CoT; Role + HR + ToT → 4 × 3 models = **12 configurations** |
| Scripts | `tables/table_04/BB + Role + HR.py`, `BB + Role + CoT + HR.py`, `BB + Role + ToT + HR.py` (all include HR; the `BB` prefix is historical). The Role-only baseline has no script in the repository. |
| Visual input | `Images/scenario 1.jpg` |
| Context | Scenario 1: no oncoming traffic ("Planner considers the maneuver safe"), no vehicle behind, F = 24 s |
| Explanation length | Few-Sentences |
| Decoding | temperature 0.1, top-p 0.9, no max-token limit |
| Repetitions | 30 per configuration |
| Output | one workbook per script, columns `Run_Number, Model, Following_Time, Text_Version, Traffic_Behind, Passenger_Hurry, Response, Decision, Elapsed_Time` |
| Archived output | none (only the aggregate counts in `final_results_table_3_4_5_6.xlsx`) |
| Rerun note | `gpt-4.1-nano` returned `404 model_not_found` (deprecated) when called on 2026-10-28; that row of Table 4 can no longer be regenerated. |

Role + CoT and Role + ToT *without* human reasons are not among the 12
configurations and are not part of the manuscript.

### Stage 1, Step 2 — scenario / explanation-length comparison (Table 5)

| | |
|---|---|
| Model | `gpt-4.1` (Responses API) |
| Prompt | Role + HR + CoT, Role + HR + ToT |
| Scenarios | 1: `scenario 1.jpg`, no oncoming, no rear vehicle · 2: `scenario 2.jpg` + `TTCOncoming.png`, TTC = 8.5 s · 3: `scenario 1.jpg`, "One vehicle behind at 10 m distance" |
| Fixed context | F = 24 s, no passenger urgency |
| Explanation length | No-Limit and Few-Sentences |
| Decoding / repetitions | temperature 0.1, top-p 0.9 / 30 per scenario × regime |
| Archived output | none (aggregates only) |

### Stage 2 — contextual evaluation (Fig. 5, Tables 6–8)

| | |
|---|---|
| Model / thought strategy | `gpt-4.1` + ToT (primary); `gpt-4.1` + CoT (sensitivity) — Responses API |
| Visual input | `Images/scenario 2.jpg` and `Images/TTCOncoming.png` |
| Factors | TTC_o ∈ {1.7, 3.4, 5.1, 6.8, 8.5} s × B ∈ {0, 1} × U ∈ {0, 1} × F ∈ {12, 18, 24} s × L ∈ {No-Limit, Few-Sentences} = 120 cells |
| Decoding / repetitions | temperature 0.1, top-p 0.9, no max-token limit / 30 per cell → 3,600 per strategy |
| Output columns | `Experiment_ID` (ToT file) or `Run_Number` (CoT file), `Following_Time, TTC, Text_Version, Traffic_Behind, Passenger_Hurry, Response, Decision, Elapsed_Time` |
| Analysis | `care_drive_stage2_analysis.py`: No-Limit regime, TTC = 1.7 s excluded (complete separation), grouped-binomial logit `Y ~ C(TTC)*C(F) + B + U` with condition-clustered SEs, 2,000-replicate condition-level bootstrap stratified by TTC × F (replicates hitting separation are discarded: 1,981 kept for ToT, 1,987 for CoT) |

### Prompt-component ablation (Fig. 6, Table 9, GPT-4.1)

| | |
|---|---|
| Model | `gpt-4.1` via the **Chat Completions** API, `max_tokens = 2048` |
| Conditions | A: no reasons, no principles, no safety line · B: safety line only · C: reasons only · D: reasons + principles · E: all three |
| Visual input | `scenario 2.jpg` + `TTCOncoming.png` |
| Context | F = 24 s, No-Limit, TTC ∈ {1.7, 8.5} s, B × U |
| Repetitions | 30 per cell (archived file pools a 10-run and a 20-run batch) |
| Condition E in the paper | the 240 matching rows of the Stage 2 ToT dataset (Responses API, no token limit), not the E rows produced by this script |
| A–D vs. paper's E | different API (Chat Completions vs. Responses), token limit (2048 vs. none) and prompt wording ("KEY PRINCIPLES" sentence after vs. before the reason list); the script's own E rows give 90/120 instead of 75/120. See report D1. |

### Cross-model ablation (Table 9, Qwen3-VL-8B-Instruct)

| | |
|---|---|
| Model | `Qwen/Qwen3-VL-8B-Instruct` via `transformers` (`Qwen3VLForConditionalGeneration`, `dtype="auto"`, `device_map="auto"`) |
| Decoding | `do_sample=True`, temperature 0.1, top-p 0.9, `max_new_tokens = 2048`, no seed |
| Design | identical to the GPT-4.1 ablation (A–E, TTC ∈ {1.7, 8.5}, B × U, F = 24 s, No-Limit) |
| Repetitions | 10 per cell → 400 generations |
| Hardware | manuscript: local workstation with an RTX 3090; repository also ships a DAIC SLURM job (`qwen_tot_ablation.sbatch`, L40). Which machine produced the archived file is not recorded. |

### Held-out speed-offset evaluation (Fig. A.8, Table A.12)

| | |
|---|---|
| Model | `gpt-4.1` via Chat Completions, ToT, temperature 0.1, top-p 0.9, `max_tokens = 800` |
| Visual input | `Images/scenario_addition.png` (ego 57 km/h, limit 60 km/h) |
| Factors | rear time headway ∈ {1.0, 2.5} s × surrounding-traffic speed ∈ {70, 90} km/h |
| Conditions | `A_baseline` (no reasons/principles) and `E_care_drive` (reasons + principles; *no* planner safety line) |
| Repetitions | 20 per cell → 160 |
| Output format | `SPEED OFFSET: …`, `TARGET SPEED: …`, `ACTION: …`, `JUSTIFICATION: …`, each parsed by regex; `Consistent` checks TARGET = 60 + OFFSET (all 160 consistent) |
| Run metadata | stored in the workbook's `Run Metadata` sheet (executed 2026-09-01T05:29:19) |
