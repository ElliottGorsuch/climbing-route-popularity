"""Descriptive length/tick comparisons; no star ratings or adjusted models."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def length_comparison():
    data = pd.read_parquet(ROOT / "data/processed/climbing_routes_eda.parquet")
    data = data.loc[
        data.in_core_rock
        & data.analysis_type.isin(["Sport", "Trad"])
        & data.length_feet.gt(0)
    ].dropna(subset=["ticks", "length_feet"])
    summary = pd.read_csv(ROOT / "reports/eda/length_summary.csv").dropna(
        subset=["length_band"]
    )
    summary = summary.loc[summary.analysis_type.isin(["Sport", "Trad"])].copy()
    bands = [
        "≤30",
        "31–60",
        "61–100",
        "101–150",
        "151–300",
        "301–600",
        "601–1500",
        ">1500",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.9), sharey=True)
    correlations = []
    for ax, style, color in zip(axes, ["Sport", "Trad"], ["#38796b", "#c08749"]):
        part = data.loc[data.analysis_type.eq(style)]
        rho = part[["length_feet", "ticks"]].corr(method="spearman").iloc[0, 1]
        correlations.append({"style": style, "routes": len(part), "spearman_rho": rho})
        table = (
            summary.loc[summary.analysis_type.eq(style)]
            .set_index("length_band")
            .reindex(bands)
        )
        assert int(table.routes.sum()) == len(part)
        positions = list(range(len(table)))
        ax.bar(
            [x - 0.18 for x in positions],
            table.mean_ticks,
            width=0.36,
            color=color,
            label="Mean ticks",
        )
        ax.bar(
            [x + 0.18 for x in positions],
            table.median_ticks,
            width=0.36,
            color="#cad3d0",
            label="Median ticks",
        )
        for i, row in enumerate(table.itertuples()):
            ax.text(
                i,
                max(row.mean_ticks, row.median_ticks) + 3,
                f"n={row.routes:,}",
                ha="center",
                fontsize=8,
            )
        ax.set_xticks(positions, bands, rotation=35, ha="right", fontsize=10)
        ax.set_ylim(0, 100)
        ax.set_title(
            f"{style} · {len(part):,} routes\nLength–tick rank correlation: {rho:.3f}",
            fontsize=12,
            pad=14,
        )
        ax.set_xlabel("Recorded length (feet)", fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.14)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=10)
    axes[0].set_ylabel("Historical tick records per route", fontsize=11)
    fig.tight_layout()
    path = ROOT / "web/figures/length_ticks.svg"
    path.parent.mkdir(exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return summary, correlations
