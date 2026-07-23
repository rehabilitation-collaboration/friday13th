"""06_figures.py

Phase 2C-C4 supplementary figures.

Figure S2: same-month ratio pair plot — one connected line per Fri13 pair
           showing (Fri13 count) vs (mean of same-month other-Friday controls).
           Data source: output/case_crossover_results.json (2C-C3).

Figure S3: prefecture-level IRR forest plot — 47 prefecture-specific
           is_fri13 count ratios with 95% CIs sorted by magnitude.
           Data source: output/prefecture_irr_by_prefecture.json (2C-C4).

Design rationale
----------------
  Kept separate from 03_figures.py, which handles preliminary/cross-national
  figures (Figure 1 scatter, Figure 2 cross-national forest). The 2C
  analysis figures depend on JSON outputs from 03_prefecture_panel_weather_nb
  and 05_case_crossover, not on the raw daily_accidents parquet, so
  co-locating them with the panel/case-crossover analysis pipeline reads
  more naturally than appending them to the preliminary figure module.

Usage:
    python 06_figures.py           # Generate S2 and S3
    python 06_figures.py --only s2 # Generate Figure S2 only
    python 06_figures.py --only s3 # Generate Figure S3 only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "output" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CASE_CROSSOVER_JSON = ROOT / "output" / "case_crossover_results.json"
PREF_IRR_JSON = ROOT / "output" / "prefecture_irr_by_prefecture.json"

# ---------------------------------------------------------------------------
# Shared visual config (matches 03_figures.py SHARED for consistency)
# ---------------------------------------------------------------------------
SHARED = {
    "dpi": 300,
    "font_family": "sans-serif",
    "font_size": 10,
    "title_size": 12,
    "figformat": "png",
}


# ---------------------------------------------------------------------------
# Figure S2 config: same-month ratio pair plot
# ---------------------------------------------------------------------------
FIG_S2_CFG = {
    "figsize": (10, 6),
    "color_fri13": "#D32F2F",
    "color_control": "#607D8B",
    "line_color": "#B0BEC5",
    "line_alpha": 0.7,
    "line_width": 1.2,
    "marker_fri13": "D",
    "marker_control": "o",
    "marker_size_fri13": 90,
    "marker_size_control": 55,
    "xlabel": "Same-month pair (year-month)",
    "ylabel": "Daily traffic accident count",
    "filename": "S2_same_month_pair_plot.png",
}


# ---------------------------------------------------------------------------
# Figure S3 config: prefecture IRR forest plot
# ---------------------------------------------------------------------------
FIG_S3_CFG = {
    "figsize": (8, 12),
    "color_point": "#1976D2",
    "color_ci": "#1976D2",
    "color_non_conv": "#9E9E9E",
    "null_line_color": "#999999",
    "null_line_style": "--",
    "null_line_width": 0.8,
    "ci_linewidth": 1.4,
    "ci_capsize": 0,  # caps drawn manually below
    "cap_half_height": 0.22,
    "marker_size": 5.5,
    "xlabel": "is_fri13 count ratio (95% CI, HC1-robust)",
    "filename": "S3_prefecture_forest.png",
    "xlim": (0.28, 2.05),  # widen lower to accommodate Tottori CI-low ~0.32
    "x_log_scale": False,
}


# ===========================================================================
# Figure S2: same-month ratio pair plot
# ===========================================================================
def make_figure_s2() -> Path | None:
    """Connected-line pair plot: Fri13 count vs same-month other-Friday
    control mean. One line per Fri13 pair (10 pairs total)."""
    cfg = FIG_S2_CFG
    if not CASE_CROSSOVER_JSON.exists():
        print(f"  Figure S2 SKIPPED: {CASE_CROSSOVER_JSON} not found "
              f"(run src/05_case_crossover.py first).")
        return None
    data = json.loads(CASE_CROSSOVER_JSON.read_text(encoding="utf-8"))
    pairs = data["pair_summary"]["pairs"]
    pairs = sorted(pairs, key=lambda p: p["ym"])
    labels = [p["ym"] for p in pairs]
    fri13 = [p["fri13_count"] for p in pairs]
    control = [p["control_mean"] for p in pairs]
    x = np.arange(len(pairs))

    fig, ax = plt.subplots(figsize=cfg["figsize"])

    # Connecting lines (drawn first so markers sit on top)
    for i in range(len(pairs)):
        ax.plot(
            [x[i], x[i]],
            [fri13[i], control[i]],
            color=cfg["line_color"],
            alpha=cfg["line_alpha"],
            linewidth=cfg["line_width"],
            zorder=1,
        )

    # Control mean markers
    ax.scatter(
        x, control,
        c=cfg["color_control"],
        s=cfg["marker_size_control"],
        marker=cfg["marker_control"],
        label="Same-month other-Friday mean (n=3 controls each)",
        zorder=2,
        edgecolors="white",
        linewidths=0.5,
    )
    # Fri13 markers
    ax.scatter(
        x, fri13,
        c=cfg["color_fri13"],
        s=cfg["marker_size_fri13"],
        marker=cfg["marker_fri13"],
        label="Friday the 13th",
        zorder=3,
        edgecolors="white",
        linewidths=0.5,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right",
                       fontsize=SHARED["font_size"] - 1)
    ax.set_xlabel(cfg["xlabel"], fontsize=SHARED["font_size"])
    ax.set_ylabel(cfg["ylabel"], fontsize=SHARED["font_size"])
    ax.legend(loc="lower left", fontsize=SHARED["font_size"] - 1, framealpha=0.9)
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out = OUTPUT_DIR / cfg["filename"]
    fig.savefig(out, dpi=SHARED["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure S2 saved: {out}")
    return out


# ===========================================================================
# Figure S3: prefecture IRR forest plot
# ===========================================================================
def make_figure_s3() -> Path | None:
    """Forest plot of per-prefecture is_fri13 count ratios sorted by
    magnitude. Non-converged prefectures (if any) are labeled at the top of
    the plot with a right-justified "(n.c.)" text annotation only — no marker
    is placed on the axis, to avoid the visual bomb of an "x" sitting on the
    null-effect reference line (2C-C4 MAGI-AKAGI B7 + AKAGI B8 fix).
    """
    cfg = FIG_S3_CFG
    if not PREF_IRR_JSON.exists():
        print(f"  Figure S3 SKIPPED: {PREF_IRR_JSON} not found "
              f"(run src/07_prefecture_by_prefecture_fit.py first).")
        return None
    data = json.loads(PREF_IRR_JSON.read_text(encoding="utf-8"))
    results = data["diagnostics"]["results"]

    # Sort: converged prefectures by ratio (ascending, so highest ratio
    # appears at top of plot); non-converged pinned to top with n/a.
    conv = sorted(
        [r for r in results if r["converged"]],
        key=lambda r: r["count_ratio"],
    )
    non_conv = sorted(
        [r for r in results if not r["converged"]],
        key=lambda r: r["prefecture_en"],
    )
    ordered = conv + non_conv  # non_conv appears at top (highest y)
    n = len(ordered)
    fig, ax = plt.subplots(figsize=cfg["figsize"])
    y_positions = list(range(n))

    for y, r in zip(y_positions, ordered):
        if not r["converged"]:
            # Right-justified text label only; no marker at x=1.0 to avoid
            # implying a null-value estimate for a non-converged fit.
            ax.text(
                cfg["xlim"][1] - 0.03, y,
                f"{r['prefecture_en']} (n.c.)",
                ha="right", va="center",
                fontsize=SHARED["font_size"] - 3,
                color=cfg["color_non_conv"],
                style="italic",
            )
            continue
        ratio = r["count_ratio"]
        lo = r["count_ratio_ci_low"]
        hi = r["count_ratio_ci_high"]
        # Whisker
        ax.plot(
            [lo, hi], [y, y],
            color=cfg["color_ci"], linewidth=cfg["ci_linewidth"], zorder=2,
        )
        # Caps
        cap = cfg["cap_half_height"]
        ax.plot([lo, lo], [y - cap, y + cap],
                color=cfg["color_ci"], linewidth=cfg["ci_linewidth"], zorder=2)
        ax.plot([hi, hi], [y - cap, y + cap],
                color=cfg["color_ci"], linewidth=cfg["ci_linewidth"], zorder=2)
        # Point
        ax.plot(
            ratio, y,
            marker="o", color=cfg["color_point"],
            markersize=cfg["marker_size"], zorder=3,
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [r["prefecture_en"] for r in ordered],
        fontsize=SHARED["font_size"] - 2,
    )
    ax.axvline(
        1.0, color=cfg["null_line_color"],
        linestyle=cfg["null_line_style"],
        linewidth=cfg["null_line_width"], zorder=1,
    )
    ax.set_xlabel(cfg["xlabel"], fontsize=SHARED["font_size"])
    ax.set_xlim(cfg["xlim"])
    if cfg["x_log_scale"]:
        ax.set_xscale("log")
    ax.set_ylim(-1, n)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()

    out = OUTPUT_DIR / cfg["filename"]
    fig.savefig(out, dpi=SHARED["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure S3 saved: {out}")
    return out


# ===========================================================================
# Main
# ===========================================================================
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Phase 2C-C4 supplementary figures (S2, S3)."
    )
    parser.add_argument(
        "--only",
        choices=["s2", "s3", "all"],
        default="all",
        help="Restrict generation to a single figure (default: all).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    plt.rcParams.update({
        "font.family": SHARED["font_family"],
        "font.size": SHARED["font_size"],
    })
    args = parse_args(argv)
    if args.only in ("s2", "all"):
        make_figure_s2()
    if args.only in ("s3", "all"):
        make_figure_s3()
    print("Done.")


if __name__ == "__main__":
    main(sys.argv[1:])
