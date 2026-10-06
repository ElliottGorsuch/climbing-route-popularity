"""Export the report's figures and comparison tables for the website gallery."""

import json
import shutil
from pathlib import Path

import pandas as pd
from length_figure import length_comparison

ROOT = Path(__file__).resolve().parents[1]
EDA = ROOT / "reports/eda"


def export_gallery():
    figures = ROOT / "web/figures"
    figures.mkdir(exist_ok=True)
    target = ROOT / "web/data"
    target.mkdir(exist_ok=True)
    items = []
    for name, label, title, description in [
        (
            "05_missingness",
            "Figure 1 · Data coverage",
            "What data do we have?",
            "Boulders usually lack comparable lengths, pitches and Kaggle stars. Optional protection labels may be absent. Missing labels do not establish safety.",
        ),
        (
            "popularity_bins_report",
            "Figure 2 · Recorded activity",
            "Most climbs have just a few records.",
            "Simple tick-count ranges show the long tail. A few heavily logged routes pull up averages; every retained route has at least one archive record.",
        ),
        (
            "state_counts_report",
            "Figure 3 · Geography",
            "Where activity is concentrated.",
            "The ten states with most historical ticks, highest first. Each segment shows a climbing style. Colorado, California and Utah lead total activity.",
        ),
        (
            "pca_report",
            "Figure 4 · Route profiles",
            "Length and pitches move together.",
            "The first two components retain 48% of feature variation. Short protection arrows reflect poor representation in this projection, not a lack of relationship with popularity.",
        ),
    ]:
        shutil.copyfile(EDA / f"{name}.svg", figures / f"{name}.svg")
        items.append(
            {
                "label": label,
                "title": title,
                "description": description,
                "image": f"figures/{name}.svg",
                "alt": f"{title} {description}",
            }
        )
    grades = pd.read_csv(EDA / "grade_summary.csv")
    rows = []
    for style in ["Sport", "Trad", "Bouldering"]:
        for r in (
            grades.loc[grades.analysis_type.eq(style)]
            .nlargest(3, "total_ticks")
            .itertuples()
        ):
            rows.append(
                [
                    style,
                    r.analysis_grade_family,
                    f"{r.routes:,}",
                    f"{r.total_ticks:,}",
                    f"{r.mean_ticks:.2f}",
                    f"{r.median_ticks:.0f}",
                ]
            )
    items.insert(
        2,
        {
            "label": "Question 1 · Top grades by total",
            "title": "5.10 and V0 lead total activity.",
            "description": "Top three grades by total ticks within each style. Total activity and mean ticks per route answer different questions.",
            "headers": ["Style", "Grade", "Routes", "Total ticks", "Mean", "Median"],
            "rows": rows,
        },
    )
    rows = []
    for style in ["Sport", "Trad", "Bouldering"]:
        for r in (
            grades.loc[grades.analysis_type.eq(style) & grades.routes.ge(30)]
            .nlargest(3, "mean_ticks")
            .itertuples()
        ):
            rows.append(
                [style, r.analysis_grade_family, f"{r.mean_ticks:.2f}", f"{r.routes:,}"]
            )
    items.insert(
        3,
        {
            "label": "Question 1 · Top grades by mean",
            "title": "Sport 5.7 has the highest mean overall.",
            "description": "Mean rankings require 30 or more routes per group, not 30 ticks. Sport 5.3 has only 49 routes. V1 and V0 are nearly tied.",
            "headers": ["Style", "Grade", "Mean ticks", "Routes"],
            "rows": rows,
        },
    )
    states = pd.read_csv(EDA / "state_counts_report.csv").head(10)
    rows = [
        [r.state]
        + [f"{int(getattr(r, c)):,}" for c in ["Bouldering", "Sport", "Trad", "Total"]]
        for r in states.itertuples()
    ]
    items.append(
        {
            "label": "Question 2 · State totals",
            "title": "Activity by style, in exact counts.",
            "description": "Same states and order as Figure 3. A large total can reflect more routes, reporting habits or source coverage; it is not a direct measure of regional preference.",
            "headers": ["State", "Bouldering", "Sport", "Trad", "Total"],
            "rows": rows,
        }
    )
    _summary, correlations = length_comparison()
    items.append(
        {
            "label": "Question 3 · Length and ticks",
            "title": "Does a longer climb get more ticks?",
            "description": "A direct comparison of recorded length and tick counts, separately for sport and trad. No star ratings or adjusted regression are used. The overall rank relationships are weak, even though some long-route groups have high means.",
            "image": "figures/length_ticks.svg",
            "alt": "Mean and median historical ticks by recorded length range, with route counts, for sport and trad.",
            "wide": True,
            "headers": ["Style", "Routes with length", "Length–tick rank correlation"],
            "rows": [
                [r["style"], f"{r['routes']:,}", f"{r['spearman_rho']:.3f}"]
                for r in correlations
            ],
            "caption": "Bars compare mean and median ticks in each length range; n gives the route count. Rank correlation (Spearman) describes whether longer routes tend to have more ticks across all included routes. Missing/nonpositive lengths are excluded. Boulders lack comparable length coverage and are left out. Small groups and heavily logged climbs can pull up means; this is an association, not a causal effect.",
        }
    )
    captions = {
        "Figure 1 · Data coverage": "Each cell gives the percentage of a style's routes missing that field. Darker cells mean more missing data; a missing protection label does not establish safety.",
        "Figure 2 · Recorded activity": "Each bar gives the percentage of a style's routes in a tick-count range. All panels use the same scale and include routes with at least one archived record.",
        "Figure 3 · Geography": "Bars add historical ticks by style for the ten highest-total states, in descending order. Segment size shows a style's contribution; totals combine route availability and recorded activity.",
        "Figure 4 · Route profiles": "Dots show sport/trad profiles in the first two PCA components. Arrows show projected feature relationships, enlarged threefold. These two components retain 48% of feature variation; ticks do not determine the fit.",
        "Question 1 · Top grades by total": "Grades are ranked by summed ticks within each style. Mean and median values describe ticks per route; YDS families combine their letter subgrades.",
        "Question 1 · Top grades by mean": "Mean leaders are ranked within each style among groups with at least 30 routes. Sport 5.3 has only 49 routes; V1 and V0 are nearly tied.",
        "Question 2 · State totals": "Exact tick counts for the same ten states shown in Figure 3. Counts are historical archive records, including ambiguous repeats, rather than complete platform totals.",
    }
    for item in items:
        item.setdefault(
            "caption",
            captions[item["label"]]
            if item["label"] in captions
            else item["description"],
        )
    manifest = json.dumps(items, indent=2) + "\n"
    (target / "gallery.json").write_text(manifest)
    (ROOT / "web/gallery.json").write_text(manifest)


if __name__ == "__main__":
    export_gallery()
