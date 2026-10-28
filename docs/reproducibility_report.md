# Reproducibility report

Audit of the CARE-Drive repository against the manuscript (TRC submission,
version dated 28 October 2026). Carried out on branch `repro-audit`,
2026-10-28. No archived experimental output was modified, and no paid API calls
were made during the audit.

**Bottom line.** Every result in Stage 2 (Fig. 5, Tables 6–8), the GPT-4.1
and Qwen ablation (Fig. 6, Table 9) and the speed-offset evaluation (Fig. A.8,
Table A.12) is recomputed from archived per-generation data and matches the
paper at the printed precision. Stage 1 (Tables 4–5) can only be checked against
a hand-compiled summary workbook: no per-run outputs were ever committed, so
those tables are **not independently reproducible** from this repository. The
discrepancies below are reported for the authors to resolve; none of them was
"fixed" by editing data.

How to rerun this audit:

```bash
pip install -r requirements.txt
python -m reproduce.reproduce_all --stats   # writes reproduce/output/verification.md
pytest                                      # same checks as regression tests
```

## 1. What was verified

| Area | Result | How |
|---|---|---|
| Stage 2 design | ToT and CoT workbooks each have 3,600 rows = 120 cells × 30; no `Unclear`/`Error`; re-parsing every response reproduces every stored decision | `reproduce/results.py::stage2_integrity` |
| Fig. 5 | Per-cell rates and Wilson CIs regenerate; the script reproduces the committed PNGs and `stage2_condition_proportions_wilson.csv` byte-for-byte | `care_drive_stage2_figures.py` |
| Table 6 | All four rows (k, AIC, lack-of-fit deviance, df, p) match. The fourth row (TTC × F + B × U) was not produced by the analysis script before; it is now. | `care_drive_stage2_analysis.py` |
| Tables 7, 8 | All 10 odds ratios and bootstrap CIs match to 2 d.p. | idem, seed 20260903 |
| Sec. 4.2.2–4.2.3 | TTC = 1.7 s has 0 overtakes (separation); CoT Few-Sentences has 0 overtakes; Strategy × Rear β = −1.24, Strategy × Urgency β = −1.15, both p < 0.001; TTC × F joint Wald p < 0.001 | idem |
| Table 9, GPT-4.1 | A–D: 0/120 at both TTC levels; E: 0/120 and 75/120 | `ablation_table("gpt")` |
| Fig. 6b | 18/30, 11/30, 26/30, 20/30 | `ablation_E_breakdown("gpt")` |
| Table 9, Qwen | 400 generations, 0 overtakes in every condition (but see D2) | `ablation_table("qwen")` |
| Fig. A.8 notebook | The README's `nbconvert` command runs in a clean environment and plots the Table A.12 means. The committed figure files were the Qwen plot and have been restored (D8). | final review |
| Table A.12, Sec. 4.2.6 | Baseline mean 0.0 in all cells; complete prompt 6.0 / 10.0 / 1.9 / 0.5; pooled 8.0 / 1.2; 13/20 and 19/20 zero offsets | `speed_offset_table` |
| Table 4, Table 5 | Every number equals `final_results_table_3_4_5_6.xlsx`; Table 4 has exactly 12 configurations (4 prompts × 3 models) | `stage1_record` — record only |

Status counts from `reproduce_all --stats`: 59 MATCH, 25 RECORD_ONLY,
1 NOT_VERIFIABLE, 3 MISMATCH (D1–D3 below).

## 2. Discrepancies (not resolved — need an author decision)

**D1. Condition E in the ablation has two sources, generated differently.**
The paper's Condition E (75/120 at TTC 8.5 s) is the matching subset of the
Stage 2 ToT dataset, as Sec. 3.4.5 states, and it reproduces exactly from that
dataset. But:
- `figures/figure_06/Results_Parameter_Combinations.xlsx` also contains 240 E
  rows produced by `GPT4_ToT_Component_Ablation.py`. They give **90/120**
  (25/24/22/19 of 30) at TTC 8.5 s and share no responses with Stage 2. The paper
  does not use them, but they sit in the same file as A–D.
- The original Fig. 6 notebook typed the Stage 2 percentages in by hand and
  overrode the workbook's E bar. `make_figure_06.py` now derives them from the
  Stage 2 data instead. The output is visually identical.
- Sec. 3.4.5 says all prompt elements other than the three ablated components
  were held constant. In the code, A–D were generated through the Chat
  Completions API with `max_tokens = 2048`. The paper's E came from the Stage 2
  script, which uses the Responses API with no token limit. The prompt wording
  also differs slightly: in Stage 2 the "Use the KEY PRINCIPLES …" sentence comes
  before the reason list and the task says "KEY PRINCIPLE"; in the ablation
  script it follows the list and says "KEY PRINCIPLES". The 90/120 versus 75/120
  gap shows that E is sensitive to the run or to these implementation details.
  The A–D floor (0/960) is unaffected.
- The two E samples also disagree on the context pattern at TTC 8.5 s. In
  Stage 2 (Fig. 6b), a rear vehicle raises overtaking (18, 11 → 26, 20 of 30).
  In the ablation script's own E, which used the same pipeline as A–D, a rear
  vehicle lowers it (25, 24 → 22, 19).

*Effect on the reported results:* none of the printed numbers changes. Table 9
and Fig. 6 reproduce exactly from the source the paper names.
- The headline conclusion holds under both E samples: overtaking appears only
  under the complete prompt and only at TTC 8.5 s. The same-pipeline sample
  (90/120) supports it as well as the Stage 2 one (75/120).
- What does not hold as written is the "held constant" sentence in Sec. 3.4.5.
- Any reading of the Fig. 6b context pattern as a property of Condition E
  should be qualified: with 30 runs per bar it was not replicated in the second
  sample.

**D2. One Qwen output has no parseable decision.** Condition E, TTC 8.5 s,
rear vehicle present, no urgency: the response is a 10,096-character
repetition loop with no "Decision: case …". The notebook counts it as not
overtaking. "0 overtaking decisions in 400 generations" is therefore true, but
strictly it is 399 stay-behind + 1 unclassifiable.

*Handling.*
- The stored `Decision` is `Unclear`; the decision parser reproduces this.
- `reproduce/results.py` and `overtaking_rate_figure_qwen.ipynb` count the
  output in the cell's denominator and not as an overtake. This gives 0/40 for
  that cell and 0/400 overall.
- Excluding it instead would give 0/39 and 0/399.

*Effect on the reported results:* every Qwen rate stays 0 % either way, and the
denominators match Table 9 only when the output is counted. The manuscript does
not mention it. A footnote to Table 9 would disclose it, for example: "One
Condition E generation (TTC 8.5 s, rear vehicle, no urgency) contained no
parseable decision and is counted as not overtaking."

**D3. "Approximately five-fold" shorter explanations (Sec. 3.3.1).** In
Stage 2, No-Limit responses are 6.2× longer than Few-Sentences responses in
characters (6.5× in words) for ToT, and 6.4× (6.6×) for CoT. The Stage 1 data
that may have been the basis is not archived. Elapsed time gives smaller ratios
(ToT 3.7×, CoT 2.2×).

*Effect on the reported results:* the claim is descriptive context for the
explanation-length manipulation. It enters no model, table or figure. The text
should either say "approximately six-fold" or state how the ratio was measured.

**D4. Speed-offset "predefined direction".** Sec. 4.2.6 says the complete
prompt produced positive mean offsets "in the predefined direction in all four
contexts". The predefined expectations stored in the script and workbook
(`EXPECTED_DIRECTIONS`) are *accelerate* only for 1.0 s / 90 km/h and
*maintain* for the other three cells. Against those, the complete prompt's
ACTION agrees in 0/20, 20/20, 10/20 and 19/20 generations (see
`reproduce/output/tableA12_gpt_directional_agreement.csv`). Two related notes:
- The speed-offset "complete prompt" (`E_care_drive`) contains reasons and
  principles but deliberately **no** planner-safety line. That is unlike
  Condition E in Table 3, which also has the label "complete prompt".
- The 2.5 s / 70 km/h mean is 1.95, printed as 1.9. Python's `.1f` rounds the
  stored float down; conventional rounding gives 2.0.

**D5. Stage 1 (Tables 4–5) cannot be reproduced from the repository.**
- No per-run responses for any Stage 1 configuration were ever committed.
  `final_results_table_3_4_5_6.xlsx` holds only aggregates. It was deleted in
  commit f6d55ff while the README still pointed to it, and has been restored.
  The Role-only rows have no timing in it.
- The **Role-only baseline** (3 rows of Table 4) has no script. A
  substitute has not been written, because its exact prompt is not recorded.
- `gpt-4.1-nano` now returns `404 model_not_found` (deprecated), so its Table 4
  rows cannot be regenerated.
- The Sec. 4.1.3 check that all 180 + 180 Step 2 explanations acknowledge
  the legal prohibition cannot be verified.

**D6. Qwen execution environment.** The manuscript says the Qwen runs used a
local RTX 3090 workstation. The repository ships a DAIC SLURM job on an L40
that checks out a branch `address-reviewer-comment`, which is not on this
remote. Which environment produced the archived file is not recorded, and Qwen
generation was not seeded.

**D7. Minor provenance gaps.**
- The archived Stage 2 ToT workbook's first column is `Experiment_ID`, while
  the current script writes `Run_Number`. So the file was produced by an earlier
  revision of the script; the data columns are identical.
- The GPT-4.1 ablation workbook pools two batches (10 + 20 runs per cell), and
  its `Run_Number` values repeat.
- The CARLA demonstration (Table 10) has no code or logs in this repository.
- `Images/Distance oncoming vehicle to AV.png` is not used by any script. Its
  metadata names Canva as the creating tool.

**D8. The committed Fig. A.8 files showed the Qwen data (fixed).**
`figures/figure_A8/speed_offset_two_panel.{png,pdf,svg}` showed the
exploratory Qwen speed-offset results (means 1.5 / 3.0 / 0.0 km/h); the PNG was
byte-identical to `tables/table_A12/speed_offset_two_panel.png`. Before commit
9bf0cfa, both notebooks lived in one folder and wrote the same file names, so
the Qwen run had overwritten the GPT-4.1 figure.
- The GPT-4.1 versions from the parent of 9bf0cfa have been restored. They
  show 0.0 / 8.0 / 1.2 and 6.0 / 10.0 / 1.9 / 0.5 km/h, which equals Table A.12.
- They are also the same as the figure the notebook regenerates from the
  archived workbook.
- The data and the manuscript were not affected.

## 3. What was changed

Code only — no file under `figures/*/` or `tables/*/` that holds experimental
output was edited, apart from adding one row to the derived
`specification_screen.csv`.

| Change | Why |
|---|---|
| All 12 generator scripts write to `<script folder>/reruns/` (or `$CARE_DRIVE_OUTPUT_DIR`) | Five of them previously **appended to the archived workbooks** on rerun (Stage 2 ToT/CoT, GPT ablation, both speed-offset). The Stage 1 scripts wrote into a CWD-relative `Result Table 3 New/` that also held unrelated ablation files. |
| `tables/table_04/BB + Role + HR.py`, `BB + Role + ToT + HR.py`: create the OpenAI `client` | Both referenced an undefined `client` since the first commit. Every call raised `NameError` inside the `try`, so every row was silently recorded as `Error`. |
| Stage 1 scripts read the key from `OPENAI_API_KEY` or `secrets/openai_api_key.txt` | Consistent with the other GPT-4.1 scripts. |
| `tables/table_05/*.py`: add a `Scenario` output column; fix the final summary `print` | Without the column, rows from the three scenarios could not be told apart. All three scripts crashed with `TypeError` (`len()` of an int) on the last line after saving. |
| `tables/table_05/ROLE + ToT + HR.py`: run Scenarios 1–3 by default | It had been left on Scenario 2 only, while Table 5 reports all three. |
| `care_drive_stage2_analysis.py`: add the TTC × F + B × U specification; `CARE_DRIVE_STAGE2_OUTDIR` override | Table 6's fourth row was not produced by any script. The override lets the tests run without touching tracked CSVs. Other outputs are unchanged apart from about 1e-14 float noise. |
| New `figures/figure_06/make_figure_06.py` | Fig. 6 without hand-typed values (D1). |
| New `reproduce/` (results, manuscript values, verification, checksums) and `tests/` | Automated checks of every result against the paper, plus SHA-256 checksums of all archived data and input images. |
| `requirements.txt`, `requirements-experiments.txt`, `pytest.ini` | Pinned, tested analysis environment; separate rerun dependencies. |
| Restored `final_results_table_3_4_5_6.xlsx`; untracked `.DS_Store`; `.gitignore` drops a stale path and ignores `reruns/`, `reproduce/output/` | — |
| Comments in `GPT4_ToT_Component_Ablation.py` and `tables/table_05/ROLE + HR.py` | Document the 10 + 20 pooling and that `ROLE + HR.py` is exploratory. |
| Final review: restored `figures/figure_A8/speed_offset_two_panel.*` from history | D8 |
| Final review: `LICENSE` (MIT, source code only); README licence, Stage 1 wording and pytest plugin note | Publication preparation; see §5 |

## 4. Rerunning experiments: limits

Rerunning can reproduce the *design* but not the *historical responses*.
- Hosted GPT-4.1 behaviour may have changed since the original runs.
- Neither API path accepts a seed in these scripts.
- `gpt-4.1-nano` is retired.
- The Chat Completions and Responses APIs are not interchangeable (D1).

A rerun is a new sample from today's model and should be reported as such.
None of the experiment scripts was re-executed against the API in this audit.

## 5. File classification and licensing

| Class | Files | Licence |
|---|---|---|
| Original source code | `*.py`, `*.ipynb`, `reproduce/`, `tests/`, `tables/table_09/qwen_tot_ablation.sbatch`, `pytest.ini`, `requirements*.txt` | MIT (`LICENSE`), pending confirmation of the copyright holder |
| Research data: archived model outputs | the seven `*.xlsx` files listed in `reproduce/data_checksums.sha256` | not licensed yet (author decision) |
| Research data: derived outputs | `stage2_analysis_output/*.csv`, `stage2_condition_proportions_wilson.csv`, figure `*.png/pdf/svg` | not licensed yet (author decision) |
| Input images | `Images/*` | not licensed; provenance not recorded (see below) |
| Documentation | `README.md`, `docs/` | not covered by MIT |
| Third-party, not redistributed | GPT-4.1 (OpenAI API), Qwen3-VL-8B-Instruct weights (Apache-2.0), Python packages, CARLA | their own terms |

Points to confirm before publishing:
1. **Copyright holder** in `LICENSE`. It currently reads "Lucas Elbert
   Suryana, Delft University of Technology". Under TU Delft policy the
   university usually holds copyright in employee-written software, and code by
   student co-authors may belong to them. Confirm the line with TU Delft before
   pushing.
2. **Images.** It is not recorded whether the scene images are original
   renderings or contain third-party material such as map tiles, simulator
   assets or Canva stock elements. Confirm their origin before choosing a licence.
3. **Data licence.** CC BY 4.0, as used by 4TU.ResearchData, would be the usual
   choice for the workbooks, but none has been applied.
4. **Prompt text.** The scripts contain the 11 human reasons, which are based
   on expert input. If they come from earlier published work, cite that source
   in the README.

## 6. Final review run (2026-10-28)

The run was done on a fresh clone of `repro-audit` in a new virtual
environment: Python 3.13.12 with exactly the pinned `requirements.txt`.
- `python -m reproduce.reproduce_all --stats` exits 0 in 88 s with 59 MATCH,
  25 RECORD_ONLY, 1 NOT_VERIFIABLE and 3 MISMATCH. The mismatches are D1–D3.
- `pytest`: 7 passed in 79 s. `pytest -m "not slow"`: 6 passed in 7 s.
- Each command in the README's "Individual figures and tables" table also
  exits 0, including the Fig. A.8 `nbconvert` command.
  - The regenerated Stage 2 CSVs differ from the committed ones only by float
    noise (at most 2e-12).
  - Fig. 6 and Fig. 5 are visually identical; only the PDF timestamps and
    1-pixel PNG sizes differ.
- On this audit machine, pytest needs `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`
  because ROS packages sit on `PYTHONPATH`. This is an environment issue,
  documented in the README.

No unresolved test failures. The experiment scripts themselves (workflow B)
were not rerun, because that requires paid API calls or a GPU.
