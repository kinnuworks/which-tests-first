"""Figure 3: Recall@10 on planted bugs vs real regressions, from the results files."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, INK2, GRID, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#b5b4ae"
METH = [("graphdist", "Graph distance", "#2a78d6"), ("lexical", "Lexical similarity", "#e87ba4"),
        ("e4b", "Gemma 4 E4B, prompt v1", "#1baf7a"), ("e4b_v2", "Gemma 4 E4B, prompt v2", "#eb6834"),
        ("coverage", "Coverage (upper bound)", "#eda100")]
data, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = []
planted = json.loads((data / "results.json").read_text())["recall"]
v2p = {}
for l in (data / "results_v2_planted.md").read_text().splitlines():
    if l.startswith("| pooled |"):
        cells = [c.strip() for c in l.strip("|").split("|")]
        v2p = {"e4b_v2": float(cells[6])}
rows.append(("Planted bugs (375)", {m: planted[m]["10"][0] for m, _, _ in METH if m in planted} | v2p))
for name, f in (("FastAPI real (40)", "results_real.json"), ("Rich real (36)", "results_real_rich.json"), ("requests real", "results_real_requests.json")):
    p = data / f
    if p.exists():
        r = json.loads(p.read_text())
        rows.append((f"{name.split(' (')[0]} ({r['n']})" if "(" not in name or True else name, {m: r["recall"][m]["10"][0] for m, _, _ in METH if m in r["recall"]}))
fig, ax = plt.subplots(figsize=(7.2, 0.75 * len(rows) + 1.3), dpi=200)
fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(MUTED)
ax.tick_params(colors=INK2, labelsize=9, left=False)
ax.grid(axis="x", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
for i, (label, vals) in enumerate(rows):
    xs = [vals[m] for m, _, _ in METH if m in vals]
    ax.plot([min(xs), max(xs)], [i, i], color=GRID, linewidth=3, zorder=1)
    for j, (m, _, c) in enumerate(METH):
        if m in vals:
            ax.plot([vals[m]], [i + (j - 2) * 0.09], marker="o", markersize=9, color=c, markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.invert_yaxis()
ax.set_xlim(0, 1); ax.set_xlabel("Share of bugs with a failing test in the first 10 (Recall@10)", color=INK2, fontsize=9.5)
handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=7, color=c, label=l) for _, l, c in METH]
ax.legend(handles=handles, frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(-0.32, 1.02), ncol=3, columnspacing=1.0, handletextpad=0.3, labelcolor=INK)
fig.suptitle("Planted bugs flatter every method", x=0.02, ha="left", color=INK, fontsize=10.5)
fig.subplots_adjust(left=0.24, right=0.97, bottom=0.2, top=0.72)
fig.savefig(out / "fig3_planted_vs_real.png", facecolor=SURFACE)
print("ok", [r[0] for r in rows])
