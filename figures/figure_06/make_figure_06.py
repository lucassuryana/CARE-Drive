"""
CARE-Drive - Figure 6 (prompt-component ablation, GPT-4.1)
===========================================================

Script version of overtaking_rate_figure_rev.ipynb with one change: Condition E
is computed from the Stage 2 ToT dataset (figures/figure_05/) instead of being
typed into the notebook. Section 3.4.5 states that the 240 Condition E
observations were extracted from the Stage 2 factorial (F = 24 s, no-limit,
TTC in {1.7, 8.5} s); Conditions A-D come from Results_Parameter_Combinations.xlsx
in this folder. The E rows stored in that workbook come from a separate run
of GPT4_ToT_Component_Ablation.py and are not used in the paper (see
docs/reproducibility_report.md).

    python figures/figure_06/make_figure_06.py

Writes overtaking_two_panel.{png,pdf,svg} next to this script.
Requires: pandas, numpy, matplotlib, openpyxl
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from reproduce import results as r  # noqa: E402

CONDITIONS = [
    ('A_000_baseline',           'A: Baseline'),
    ('B_001_safety_only',        'B: Safety only'),
    ('C_100_reasons_only',       'C: Reasons only'),
    ('D_110_reasons_principles', 'D: Reasons +\nprinciples'),
    ('E_111_full_prompt',        'E: Complete\nprompt'),
]
TTC_HIGH = 8.5
CONTEXTS = [
    (0, 0, 'No rear vehicle /\nNo urgency', '#9DC3E6', None),
    (0, 1, 'No rear vehicle /\nUrgency',    '#1F4E96', '////'),
    (1, 0, 'Rear vehicle /\nNo urgency',    '#8C8C8C', None),
    (1, 1, 'Rear vehicle /\nUrgency',       '#E8A33D', '////'),
]
TTC_COLORS = {1.7: '#1F4E96', 8.5: '#E8A33D'}

# panel A: conditions x TTC, contexts pooled (E from Stage 2)
panel_a = r.ablation_table("gpt").set_index(["Condition", "TTC"])
# panel B: the four contexts within the complete prompt at high TTC
panel_b = r.ablation_E_breakdown("gpt").set_index(["B", "U"])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={'width_ratios': [1.5, 1]})

x = np.arange(len(CONDITIONS))
width = 0.34
ttc_values = sorted(TTC_COLORS)
for i, ttc in enumerate(ttc_values):
    offset = (i - (len(ttc_values) - 1) / 2) * width
    rows = [panel_a.loc[(key, ttc)] for key, _ in CONDITIONS]
    heights = [row.overtake / row.n * 100 for row in rows]
    ax1.bar(x + offset, heights, width=width, color=TTC_COLORS[ttc],
            edgecolor='#404040', linewidth=0.7, label=f'TTC = {ttc:g} s')
    for xi, h, row in zip(x + offset, heights, rows):
        k, n = int(row.overtake), int(row.n)
        label = f"{k}/{n}" if h == 0 else f"{k}/{n}\n({h:.1f}%)"
        y = 2 if h == 0 else h + 2
        ax1.text(xi, y, label, ha='center', va='bottom', fontsize=8.5,
                 color=TTC_COLORS[ttc], fontweight='bold')

ax1.set_xlabel('Prompt condition')
ax1.set_ylabel('Overtaking rate (%)')
ax1.set_xticks(x)
ax1.set_xticklabels([lbl for _, lbl in CONDITIONS])
ax1.set_ylim(0, 100)
ax1.set_title('A. Prompt-component ablation across TTC levels', fontsize=12, fontweight='bold')
ax1.grid(axis='y', linestyle=':', linewidth=0.7, color='#BFBFBF', zorder=0)
ax1.set_axisbelow(True)
ax1.spines[['top', 'right']].set_visible(False)
ax1.legend(frameon=False, fontsize=9, loc='upper left')

labels = [lbl for _, _, lbl, _, _ in CONTEXTS]
values = [panel_b.loc[(b, u), "k"] / panel_b.loc[(b, u), "n"] * 100 for b, u, *_ in CONTEXTS]
bars = ax2.bar(labels, values, color=[c for *_, c, _ in CONTEXTS], edgecolor='#404040', linewidth=0.7)
for bar, (b, u, _, _, hatch) in zip(bars, CONTEXTS):
    bar.set_hatch(hatch)
    k, n = int(panel_b.loc[(b, u), "k"]), int(panel_b.loc[(b, u), "n"])
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
             f"{k}/{n}\n({k / n * 100:.1f}%)", ha='center', va='bottom',
             fontsize=9, color='#1A1A1A')

ax2.set_xlabel('Scenario (rear vehicle / urgency)')
ax2.set_ylabel('Overtaking rate (%)')
ax2.set_ylim(0, 100)
ax2.set_title(f'B. Complete prompt at TTC = {TTC_HIGH} s', fontsize=12, fontweight='bold')
ax2.grid(axis='y', linestyle=':', linewidth=0.7, color='#BFBFBF', zorder=0)
ax2.set_axisbelow(True)
ax2.spines[['top', 'right']].set_visible(False)

fig.tight_layout()
for ext in ('png', 'pdf', 'svg'):
    fig.savefig(os.path.join(HERE, f'overtaking_two_panel.{ext}'), dpi=300,
                bbox_inches='tight', facecolor='white')
print(f"Figure 6 written to {HERE}/overtaking_two_panel.{{png,pdf,svg}}")
