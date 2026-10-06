"""Readable report-only figures built from the unchanged EDA population."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker

ROOT = Path(__file__).resolve().parents[1]
EDA = ROOT / "reports/eda"
STYLES = ["Sport", "Trad", "Bouldering"]
COLORS = {"Sport": "#38796b", "Trad": "#c08749", "Bouldering": "#687eae"}


def build_report_figures():
    data = pd.read_parquet(ROOT / "data/processed/climbing_routes_eda.parquet")
    data = data.loc[data.in_core_rock]
    bins = [0, 1, 4, 9, 24, 49, 99, np.inf]
    labels = ["1", "2-4", "5-9", "10-24", "25-49", "50-99", "100+"]
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
        }
    )
    fig, axes = plt.subplots(1, 3, figsize=(9.3, 5.2), sharex=True)
    rows = []
    for ax, style in zip(axes, STYLES):
        ticks = data.loc[data.analysis_type.eq(style), "ticks"]
        counts = pd.cut(ticks, bins, labels=labels).value_counts(sort=False)
        assert counts.sum() == len(ticks)
        pct = counts / len(ticks) * 100
        ax.barh(labels, pct, color=COLORS[style], height=0.64)
        ax.invert_yaxis()
        ax.set_xlim(0, 58)
        ax.set_xticks([0, 20, 40])
        ax.xaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
        ax.tick_params(axis="both", length=0, labelsize=11)
        ax.set_title(f"{style}\n{len(ticks):,} routes", fontsize=12, pad=16)
        ax.set_xlabel("Share of routes", labelpad=12)
        ax.grid(axis="x", alpha=0.15)
        ax.set_axisbelow(True)
        for i, (label, value) in enumerate(pct.items()):
            ax.text(value + 1, i, f"{value:.1f}%", va="center", fontsize=11)
            rows.append(
                {
                    "style": style,
                    "tick_range": label,
                    "routes": int(counts[label]),
                    "percent": value,
                }
            )
    axes[0].set_ylabel("Tick records per route", labelpad=12)
    fig.tight_layout(w_pad=2)
    for ext in ["png", "svg"]:
        fig.savefig(EDA / f"popularity_bins_report.{ext}", dpi=200)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(EDA / "popularity_bins_report.csv", index=False)

    states = pd.read_csv(EDA / "state_type_summary.csv")
    pivot = states.pivot(
        index="state", columns="analysis_type", values="total_ticks"
    ).fillna(0)
    pivot = pivot[STYLES].astype(int)
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=False)
    pivot.to_csv(EDA / "state_counts_report.csv")
    top = pivot.head(10)
    fig, ax = plt.subplots(figsize=(9.3, 4.4))
    left = np.zeros(len(top))
    for style in STYLES:
        ax.barh(
            top.index,
            top[style],
            left=left,
            color=COLORS[style],
            label=style,
            height=0.68,
        )
        left += top[style].to_numpy()
    for i, total in enumerate(top.Total):
        ax.text(total + 5000, i, f"{total:,}", va="center", fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, top.Total.max() * 1.24)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda n, _: f"{n / 1000:.0f}k"))
    ax.set_xlabel("Total historical tick records")
    ax.tick_params(axis="both", length=0)
    ax.grid(axis="x", alpha=0.15)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=11)
    fig.tight_layout()
    for ext in ["png", "svg"]:
        fig.savefig(EDA / f"state_counts_report.{ext}", dpi=200)
    plt.close(fig)
    return data, pivot
