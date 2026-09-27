"""
CARE-Drive - Figure 5 (Stage 2 full-factorial overtaking rate, with Wilson CIs)
===============================================================================

Draws the 2x3 grid described in the Figure 5 caption: rows are the
explanation-length regime (no-limit / few-sentences), columns are following
time (12/18/24 s), the x-axis within each panel is TTC_o, and each of the four
curves is one (vehicle-behind, passenger-urgency) combination. Error bars are
95% Wilson binomial confidence intervals, as the caption requires -- the
earlier overtaking_rate_calculation.ipynb in this folder plots the same point
estimates but without those intervals.

Produces the primary ToT figure (Fig. 5 itself) and, from the same code, an
analogous CoT figure as a supplementary sensitivity view (not itself a
numbered figure in the paper, but drawn from the Table 8 CoT dataset already
sitting in this folder).

Requires: pandas, numpy, matplotlib, statsmodels
"""

import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from statsmodels.stats.proportion import proportion_confint

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.linewidth': 0.8, 'axes.edgecolor': '#333333',
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'xtick.major.size': 3, 'ytick.major.size': 3,
})

HERE = os.path.dirname(os.path.abspath(__file__))


def prep(fname):
    df = pd.read_excel(os.path.join(HERE, fname), usecols=[
        'Following_Time', 'TTC', 'Text_Version',
        'Traffic_Behind', 'Passenger_Hurry', 'Decision',
    ])
    df['B'] = df['Traffic_Behind'].notna().astype(int)
    df['Uh'] = df['Passenger_Hurry'].notna().astype(int)
    df['L'] = (df['Text_Version'] == 'Limited').astype(int)
    df['Fc'] = df['Following_Time'].astype(float)
    df['Tc'] = df['TTC'].astype(float)
    df['Y'] = df['Decision'].astype(int)
    return df


tot = prep("Results_Parameter_Combinations.xlsx")
cot = prep("Results_Parameter_Combinations_CoT.xlsx")

# series styling follows the existing Figure 5 legend
SERIES = [
    ((0, 0), 'Behind (No) + Hurry (No)', '#1f3d99', 'D'),
    ((0, 1), 'Behind (No) + Hurry (Yes)', '#4f9fe0', 'D'),
    ((1, 0), 'Behind (Yes) + Hurry (No)', '#6e6e6e', 's'),
    ((1, 1), 'Behind (Yes) + Hurry (Yes)', '#c08a1e', '^'),
]
TTCS = [1.7, 3.4, 5.1, 6.8, 8.5]
FS = [12.0, 18.0, 24.0]
DODGE = {(0, 0): -0.105, (0, 1): -0.035, (1, 0): 0.035, (1, 1): 0.105}


def make_figure(df, strategy, outstem):
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 6.4), sharex=True, sharey=True)
    for row, (L, Llab) in enumerate([(0, 'no-limit'), (1, 'few-sentences')]):
        for col, F in enumerate(FS):
            ax = axes[row, col]
            for (b, u), lab, color, mk in SERIES:
                xs, ps, lo, hi = [], [], [], []
                for T in TTCS:
                    s = df[(df.L == L) & (df.Fc == F) & (df.Tc == T) &
                           (df.B == b) & (df.Uh == u)]['Y']
                    n, k = len(s), int(s.sum())
                    if n == 0:
                        continue
                    cl, ch = proportion_confint(k, n, alpha=0.05, method='wilson')
                    xs.append(T + DODGE[(b, u)]); ps.append(100 * k / n)
                    lo.append(100 * (k / n - cl)); hi.append(100 * (ch - k / n))
                ax.errorbar(xs, ps, yerr=[lo, hi], color=color, marker=mk,
                            markersize=4.5, linewidth=1.3, elinewidth=0.9,
                            capsize=2.0, capthick=0.9, markeredgewidth=0,
                            alpha=0.95, zorder=3)
            ax.set_ylim(-6, 106)
            ax.set_xlim(1.0, 9.2)
            ax.set_xticks(TTCS)
            ax.set_yticks([0, 20, 40, 60, 80, 100])
            ax.grid(axis='y', color='#dddddd', linewidth=0.6, zorder=0)
            ax.set_axisbelow(True)
            for sp in ('top', 'right'):
                ax.spines[sp].set_visible(False)
            ax.set_title(f'Following time = {int(F)} s', fontsize=9.5, pad=6)
            ax.tick_params(labelbottom=True)
            ax.set_xlabel('TTC oncoming (s)', fontsize=9)
            if col == 0:
                ax.set_ylabel('Overtaking rate (%)', fontsize=9)

    fig.suptitle('Overtaking Rate by Time-to-Collision, Length of Explanation, '
                 f'and Following Time\n({strategy})',
                 fontsize=11, fontweight='bold', y=1.02)

    handles = [Line2D([0], [0], color=c, marker=m, markersize=4.5,
                      linewidth=1.3, markeredgewidth=0, label=l)
               for (_, l, c, m) in SERIES]
    fig.legend(handles=handles, loc='lower center', ncol=2,
               frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, -0.035))

    fig.tight_layout(rect=[0, 0.045, 1, 0.925])
    fig.subplots_adjust(hspace=0.78)

    # panel labels sit just above the column titles of each row
    for row, lab in [(0, '(a) Length of explanation: no-limit'),
                     (1, '(b) Length of explanation: few-sentences')]:
        top = axes[row, 0].get_position().y1
        fig.text(0.5, top + 0.062, lab, ha='center',
                 fontsize=9.5, fontweight='bold')
    for ext in ('pdf', 'png'):
        fig.savefig(os.path.join(HERE, f'{outstem}.{ext}'), dpi=300,
                    bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {outstem}.pdf / .png')


make_figure(tot, 'GPT-4.1 + Tree-of-Thought', 'fig5_ToT_wilson')
make_figure(cot, 'GPT-4.1 + Chain-of-Thought', 'fig5_CoT_wilson')

# supporting table of every cell proportion + Wilson interval
rows = []
for strat, df in [('ToT', tot), ('CoT', cot)]:
    for L in [0, 1]:
        for F in FS:
            for T in TTCS:
                for (b, u), lab, _, _ in SERIES:
                    s = df[(df.L == L) & (df.Fc == F) & (df.Tc == T) & (df.B == b) & (df.Uh == u)]['Y']
                    n, k = len(s), int(s.sum())
                    cl, ch = proportion_confint(k, n, alpha=0.05, method='wilson')
                    rows.append({'Strategy': strat,
                                 'Explanation': 'few-sentences' if L else 'no-limit',
                                 'Following_time_s': int(F), 'TTC_s': T,
                                 'Vehicle_behind': b, 'Passenger_urgency': u,
                                 'n': n, 'overtakes': k, 'rate': round(k / n, 4),
                                 'wilson_lo': round(cl, 4), 'wilson_hi': round(ch, 4)})
out = pd.DataFrame(rows)
out.to_csv(os.path.join(HERE, 'stage2_condition_proportions_wilson.csv'), index=False)
print('wrote stage2_condition_proportions_wilson.csv:', out.shape)
print('mean Wilson interval width: %.3f' % (out.wilson_hi - out.wilson_lo).mean())
