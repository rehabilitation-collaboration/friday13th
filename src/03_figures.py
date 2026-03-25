"""03_figures.py
Figure generation for Friday the 13th manuscript.

Figure 1: Scatter plot — Friday 13th vs other Fridays
Figure 2: Forest plot — Cross-national comparison

Design: Each figure is an independent function with config dict at top.
All visual parameters are centralized for easy post-review tweaking.

Usage:
    python 03_figures.py          # Generate all figures
    python 03_figures.py fig1     # Generate Figure 1 only
    python 03_figures.py fig2     # Generate Figure 2 only
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Shared visual config (tweak here after review)
# ---------------------------------------------------------------------------
SHARED = {
    "dpi": 300,
    "font_family": "sans-serif",
    "font_size": 10,
    "title_size": 12,
    "figformat": "png",  # "png" or "pdf"
}

# ---------------------------------------------------------------------------
# Figure 1 config
# ---------------------------------------------------------------------------
FIG1_CFG = {
    "figsize": (10, 5),
    "color_fri13": "#D32F2F",
    "color_other": "#B0BEC5",
    "marker_fri13": "D",
    "marker_other": "o",
    "size_fri13": 60,
    "size_other": 12,
    "alpha_other": 0.4,
    "alpha_fri13": 0.9,
    "mean_line_color_fri13": "#D32F2F",
    "mean_line_color_other": "#607D8B",
    "mean_line_style": "--",
    "mean_line_width": 1.2,
    "ylabel": "Daily traffic accident count",
    "xlabel": "Date",
    "filename": "figure1_scatter.png",
}

# ---------------------------------------------------------------------------
# Figure 2 config
# ---------------------------------------------------------------------------
FIG2_CFG = {
    "figsize": (8, 6),
    "color_western": "#1976D2",
    "color_japan": "#D32F2F",
    "marker_size": 8,
    "null_line_color": "#999999",
    "null_line_style": "--",
    "null_line_width": 0.8,
    "ci_linewidth": 1.5,
    "ci_capsize": 3,
    "xlabel": "Effect estimate (RR or OR)",
    "filename": "figure2_forest.png",
    "xlim": (0.4, 2.2),
}

# ---------------------------------------------------------------------------
# Cross-national study data for forest plot
# (Centralized here for easy update after review)
# ---------------------------------------------------------------------------
FOREST_DATA = [
    # (label, RR, CI_lo, CI_hi, significant, is_japan)
    ("Scanlon 1993 (UK)", 1.44, None, None, True, False),
    ("Nayha 2002 - Women (Finland)", 1.63, None, None, True, False),
    ("Nayha 2002 - Men (Finland)", 1.02, None, None, False, False),
    ("Radun 2004 (Finland)", 1.00, None, None, False, False),
    ("CVS 2008 (Netherlands)", 0.96, None, None, False, False),
    ("Schuld 2011 (Germany)", 1.00, None, None, False, False),
    ("Lo 2012 - Overall (USA)", 0.90, None, None, False, False),
    ("Lo 2012 - Penetrating (USA)", 1.65, 1.04, 2.61, True, False),
    ("Ranganathan 2024 (Canada)", 1.02, 0.94, 1.09, False, False),
    ("Shekhar 2025 (USA)", 1.00, None, None, False, False),
    ("Present study (Japan)", 1.02, 0.54, 1.94, False, True),
]


# ===========================================================================
# Figure 1: Scatter plot
# ===========================================================================

def make_figure1():
    """Friday 13th (red diamonds) vs other Fridays (gray dots)."""
    cfg = FIG1_CFG
    daily = pd.read_parquet(DATA_DIR / "daily_accidents.parquet")
    fridays = daily[daily["is_friday"] == 1].copy()
    fridays["date"] = pd.to_datetime(fridays["date"])

    fri13 = fridays[fridays["is_friday13th"] == 1]
    other = fridays[fridays["is_friday13th"] == 0]

    fig, ax = plt.subplots(figsize=cfg["figsize"])

    # Other Fridays
    ax.scatter(
        other["date"], other["total"],
        c=cfg["color_other"], s=cfg["size_other"],
        alpha=cfg["alpha_other"], marker=cfg["marker_other"],
        label=f"Other Fridays (n={len(other)})", zorder=2,
        edgecolors="none",
    )

    # Friday 13th
    ax.scatter(
        fri13["date"], fri13["total"],
        c=cfg["color_fri13"], s=cfg["size_fri13"],
        alpha=cfg["alpha_fri13"], marker=cfg["marker_fri13"],
        label=f"Friday the 13th (n={len(fri13)})", zorder=3,
        edgecolors="white", linewidths=0.5,
    )

    # Mean lines
    mean_other = other["total"].mean()
    mean_fri13 = fri13["total"].mean()
    ax.axhline(
        mean_other, color=cfg["mean_line_color_other"],
        linestyle=cfg["mean_line_style"], linewidth=cfg["mean_line_width"],
        label=f"Mean other Fridays ({mean_other:.0f})", zorder=1,
    )
    ax.axhline(
        mean_fri13, color=cfg["mean_line_color_fri13"],
        linestyle=cfg["mean_line_style"], linewidth=cfg["mean_line_width"],
        label=f"Mean Friday 13th ({mean_fri13:.0f})", zorder=1,
    )

    ax.set_xlabel(cfg["xlabel"], fontsize=SHARED["font_size"])
    ax.set_ylabel(cfg["ylabel"], fontsize=SHARED["font_size"])
    ax.legend(loc="upper right", fontsize=SHARED["font_size"] - 1, framealpha=0.9)
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))

    # Year tick marks
    years = sorted(fridays["date"].dt.year.unique())
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in years])
    ax.set_xticklabels(years)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out = OUTPUT_DIR / cfg["filename"]
    fig.savefig(out, dpi=SHARED["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 1 saved: {out}")


# ===========================================================================
# Figure 2: Forest plot
# ===========================================================================

def make_figure2():
    """Cross-national forest plot of effect estimates."""
    cfg = FIG2_CFG
    data = FOREST_DATA

    n = len(data)
    fig, ax = plt.subplots(figsize=cfg["figsize"])

    y_positions = list(range(n - 1, -1, -1))

    for i, (label, rr, ci_lo, ci_hi, sig, is_japan) in enumerate(data):
        y = y_positions[i]
        color = cfg["color_japan"] if is_japan else cfg["color_western"]
        marker = "D" if is_japan else "o"
        ms = cfg["marker_size"] + (2 if is_japan else 0)

        # Point estimate
        ax.plot(rr, y, marker=marker, color=color, markersize=ms, zorder=3)

        # CI whiskers (only if available)
        if ci_lo is not None and ci_hi is not None:
            ax.plot(
                [ci_lo, ci_hi], [y, y],
                color=color, linewidth=cfg["ci_linewidth"], zorder=2,
            )
            ax.plot(
                [ci_lo, ci_lo], [y - 0.15, y + 0.15],
                color=color, linewidth=cfg["ci_linewidth"], zorder=2,
            )
            ax.plot(
                [ci_hi, ci_hi], [y - 0.15, y + 0.15],
                color=color, linewidth=cfg["ci_linewidth"], zorder=2,
            )

        # Label
        style = "bold" if is_japan else ("italic" if sig else "normal")
        ax.text(
            cfg["xlim"][0] - 0.02, y, label,
            ha="right", va="center",
            fontsize=SHARED["font_size"] - 1,
            fontstyle="italic" if sig and not is_japan else "normal",
            fontweight="bold" if is_japan else "normal",
        )

    # Null effect line
    ax.axvline(
        1.0, color=cfg["null_line_color"],
        linestyle=cfg["null_line_style"],
        linewidth=cfg["null_line_width"], zorder=1,
    )

    ax.set_xlabel(cfg["xlabel"], fontsize=SHARED["font_size"])
    ax.set_xlim(cfg["xlim"])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Add "Favours decrease / Favours increase" annotations
    ax.text(
        0.7, -1.2, "Favours decrease",
        ha="center", va="center", fontsize=SHARED["font_size"] - 2,
        color="#666666",
    )
    ax.text(
        1.5, -1.2, "Favours increase",
        ha="center", va="center", fontsize=SHARED["font_size"] - 2,
        color="#666666",
    )

    fig.subplots_adjust(left=0.45)
    fig.tight_layout()

    out = OUTPUT_DIR / cfg["filename"]
    fig.savefig(out, dpi=SHARED["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 2 saved: {out}")


# ===========================================================================
# Main
# ===========================================================================

def main():
    plt.rcParams.update({
        "font.family": SHARED["font_family"],
        "font.size": SHARED["font_size"],
    })

    args = sys.argv[1:]

    if not args or "fig1" in args:
        make_figure1()
    if not args or "fig2" in args:
        make_figure2()

    print("Done.")


if __name__ == "__main__":
    main()
