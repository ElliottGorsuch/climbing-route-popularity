"""Export the report's figures and comparison tables for the website gallery."""

import json
import shutil
from pathlib import Path

import pandas as pd

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
    models = pd.read_csv(EDA / "regression_model_comparison.csv")
    rows = []
    for name, label in [
        ("roped_ticks_quality_baseline", "Sport/trad, no stars"),
        ("roped_ticks_quality", "Same routes, with stars"),
        ("boulder_ticks", "Bouldering"),
    ]:
        r = models.loc[models.name.eq(name)].iloc[0]
        rows.append([label, f"{int(r.fit_routes):,}", f"{r.r_squared:.3f}"])
    items.append(
        {
            "label": "Question 3 · Regression",
            "title": "Quality changes the length story.",
            "description": "R² increases from 0.121 to 0.213 when stars are added on the same 61,277 routes. R² describes the logged outcome in the fitted data, not raw tick counts or future prediction accuracy.",
            "headers": ["Model", "Routes", "Logged-outcome R²"],
            "rows": rows,
        }
    )
    items.append(
        {
            "label": "Question 3 · Length comparison",
            "title": "Longer does not always mean more popular.",
            "description": "Doubling length has a +11.5% association without stars and −8.2% with stars. These are geometric (ticks + 1) comparisons, not arithmetic average count changes or causal effects.",
            "headers": ["Model comparison", "Length association"],
            "rows": [["Without stars", "+11.5%"], ["With stars", "−8.2%"]],
        }
    )
    manifest = json.dumps(items, indent=2) + "\n"
    (target / "gallery.json").write_text(manifest)
    (ROOT / "web/gallery.json").write_text(manifest)


if __name__ == "__main__":
    export_gallery()
