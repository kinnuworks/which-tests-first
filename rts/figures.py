"""Figures for the paper, from data/rows.json (written by analyze.py).

Usage: python figures.py <data_dir> <out_dir>
"""
import json
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, INK2, GRID, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#b5b4ae"
# categorical slots 1-4 of the validated reference palette, light mode, fixed order
FOCUS = {"graphdist": ("Graph distance", "#2a78d6"), "e2b": ("Gemma 4 E2B", "#eb6834"),
         "e4b": ("Gemma 4 E4B", "#1baf7a"), "coverage": ("Coverage (upper bound)", "#eda100"), "lexical": ("Lexical similarity", "#e87ba4")}
OTHER = {"full": "Full suite order", "name": "Name match", "reach": "Reachability"}
REPO_LABEL = {"cachetools": "cachetools", "toolz": "toolz", "humanize": "humanize",
              "python-sortedcontainers": "sortedcontainers", "fastapi": "FastAPI"}


def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    data, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rows = json.loads((data / "rows.json").read_text())
    methods = [m for m in list(OTHER) + list(FOCUS) if all(m in r["hit"] for r in rows)]
    ks = list(range(1, 31))

    # Figure 1: Recall@k, pooled
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    style(ax)
    ends = []
    for m in methods:
        ys = [sum(1 for r in rows if r["hit"][m] is not None and r["hit"][m] < k) / len(rows) for k in ks]
        if m in FOCUS:
            label, color = FOCUS[m]
            ax.plot(ks, ys, color=color, linewidth=2, solid_capstyle="round", zorder=3)
            ends.append((ys[-1], label, color))
        else:
            ax.plot(ks, ys, color=MUTED, linewidth=1.2, zorder=2)
            ends.append((ys[-1], OTHER[m], INK2))
    # direct labels for the focus lines only; the gray baselines go in a legend
    focus_ends = sorted(e for e in ends if e[2] != INK2)
    placed = []
    for y, label, color in focus_ends:
        y2 = y
        for p in placed:
            if abs(y2 - p) < 0.05:
                y2 = p + 0.05
        placed.append(y2)
        ax.annotate("", xy=(32.2, y2), xytext=(31.0, y2), arrowprops=dict(arrowstyle="-", color=color, lw=2.5), annotation_clip=False)
        ax.annotate(label, xy=(30, y), xytext=(32.6, y2), fontsize=8.5, color=INK, va="center", annotation_clip=False)
        ax.plot([30], [y], marker="o", markersize=3.5, color=color, zorder=4)
    gray = [plt.Line2D([], [], color=MUTED, linewidth=1.2, label=OTHER[m]) for m in methods if m in OTHER]
    ax.legend(handles=gray, title="Other baselines (gray)", title_fontsize=8, fontsize=8, frameon=False,
              loc="lower left", bbox_to_anchor=(1.0, 0.0), labelcolor=INK2)
    ax.set_xlim(1, 30)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Tests run (k)", color=INK2, fontsize=9.5)
    ax.set_ylabel("Share of bugs caught", color=INK2, fontsize=9.5)
    ax.set_title(f"Bugs caught within the first k tests, {len(rows)} planted bugs in {len({r['repo'] for r in rows})} repositories",
                 loc="left", color=INK, fontsize=10.5)
    fig.subplots_adjust(right=0.70, left=0.09, bottom=0.12, top=0.9)
    fig.savefig(out / "fig1_recall_at_k.png", facecolor=SURFACE)

    # Figure 2: median time to first failure per repository (log scale), model time included
    repos = [r for r in REPO_LABEL if any(x["repo"] == r for x in rows)]
    show = [m for m in ("graphdist", "e2b", "e4b") if m in methods] + (["full"] if "full" in methods else [])
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    style(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    for i, repo in enumerate(repos):
        rs = [x for x in rows if x["repo"] == repo]
        for m in show:
            v = statistics.median(x["ttff"][m] for x in rs)
            color = FOCUS[m][1] if m in FOCUS else MUTED
            ax.plot([v], [i], marker="o", markersize=8, color=color, markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
    ax.set_yticks(range(len(repos)), [f"{REPO_LABEL[r]} ({rows[[x['repo'] for x in rows].index(r)]['suite_time']:.0f} s suite)" for r in repos])
    ax.set_xscale("log")
    ax.invert_yaxis()
    ax.set_xlabel("Median seconds until the first failing test (model time included)", color=INK2, fontsize=9.5)
    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=7,
                          color=(FOCUS[m][1] if m in FOCUS else MUTED), label=(FOCUS[m][0] if m in FOCUS else OTHER[m])) for m in show]
    ax.legend(handles=handles, frameon=False, fontsize=8.5, loc="lower left", bbox_to_anchor=(-0.36, 1.02), ncol=len(handles), columnspacing=1.2, handletextpad=0.3, labelcolor=INK)
    fig.suptitle("Time to the first failing test", x=0.02, ha="left", color=INK, fontsize=10.5)
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.17, top=0.82)
    fig.savefig(out / "fig2_time_to_failure.png", facecolor=SURFACE)
    print("figures written")


if __name__ == "__main__":
    main()
