"""Author the annotated project notebook from the agreed analysis specification."""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def main():
    notebook = nbf.v4.new_notebook()
    cells = []

    def md(text):
        cells.append(nbf.v4.new_markdown_cell(text))

    def code(text):
        cells.append(nbf.v4.new_code_cell(text))

    md("""# What characteristics do popular climbing routes have in common?
**John Elliott Gorsuch and Victor Lee · SIADS 593 · exploratory analysis**

We study historical recorded climbing participation across the United States. Our three questions are:
1. How does popularity vary with climbing type and difficulty, keeping roped and bouldering grades separate?
2. How does the geographic distribution of participation differ between sport, trad and bouldering?
3. How do length, pitches, quality scores and recorded protection designations relate to popularity?

**Primary outcome:** absolute `sampled_tick_record_count` (archive records per route). There is **no minimum-tick filter**. Distinct sampled climbers provide a sensitivity comparison. A tick record is not necessarily a completed ascent, and ambiguous repeated records cannot be interpreted as confirmed repeat climbs.

This notebook is the analytical record. The course also requires a separate PDF report of at most 11 pages; the website is a companion, not a replacement for either deliverable.""")
    md("""## Motivation and related work
Climbers choose among routes that differ in difficulty, protection style, location and physical commitment. Recorded participation lets us investigate which profiles attract activity, while distinguishing popularity from quality and acknowledging who records climbs.

[Nick Wilder's 2014 Mountain Project tick analysis](https://www.rei.com/blog/uncategorized/factoid-4-most-popular-routes-by-difficulty) compared popular individual routes within difficulty grades. [RouteFinder by Present, Berger and Boland](https://jakepresent.github.io/RouteFinder/) mapped sport-climbing grades and explored descriptive route characteristics. These are useful precedents for grade and geographic comparisons. Our analysis combines tick-derived participation and structured route features, separates styles, and checks whether apparent relationships survive adjusted comparisons. We do not reproduce those studies or infer a representative census.""")
    md("""## Reproduce and inspect the sources
Install the pinned dependencies, then run:
```bash
python scripts/download.py
python scripts/build_main.py
```
This notebook builds the EDA outputs. `python scripts/eda.py` produces the same figures, tables and map exports outside Jupyter. `requirements-lock.txt` records the full installed environment.

The main table has **97,437 unique MP route IDs and 46 fields**. It combines Kaggle CSV features, historical JSON bouldering metadata, historical tick-derived CSV aggregates, and separate OpenBeta rating aggregates. The tick archive contains 2,115,034 rows for 47,002 users and 118,018 route IDs; it was committed April 21, 2019, with unknown individual observation dates. Source user histories were capped at 1,000 records.

The feature population was 199,083 routes. A strict inner join on MP ID retained 97,437 and dropped 101,646 without sample records. Subsequent metadata/rating left joins preserved that population. Matching uses IDs rather than guessed names or coordinates. Missing values remain missing. See [source access details](../docs/sources.md), [join implementation](../docs/main_dataset.md), [field definitions](../docs/data_dictionary.md), and checksummed [source manifest](../reports/source_manifest.json). Public availability does not establish a license for the original tick archive, which declares none. Only aggregates are published; no user identifiers are in the analytical table.""")
    code("""from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
from IPython.display import Image, Markdown, display

ROOT = Path.cwd() if (Path.cwd() / "scripts").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT / "scripts"))
import eda

raw = pd.read_parquet(ROOT / "data/processed/climbing_routes_main.parquet")
assert raw.mp_route_id.is_unique
assert raw.sampled_tick_record_count.ge(1).all()
assert not {"UserID", "users", "comment", "tick_count"}.intersection(raw.columns)
display(pd.DataFrame({"rows": [len(raw)], "columns": [raw.shape[1]], "unique_route_ids": [raw.mp_route_id.nunique()]}))
raw[["route_name", "state", "rating_raw", "route_type", "sampled_tick_record_count"]].head()""")
    md("""## Cleaning decisions and the analysis population
We keep the complete joined dataset intact and create documented analysis fields:
- Exclude any ice, aid or snow flag from the core rock comparisons; summarize those records separately. Other/top-rope-only records are also outside the three-style comparison.
- Among core rock routes, **trad takes precedence**, then bouldering, then sport. Mixed trad/sport routes therefore belong to trad.
- Use textual grade families (`5.10`, `V2`), not decimal arithmetic. Letter/suffix grades are grouped by their major family. V ranges use the lower bound; V-easy/VB form a separate category.
- The source contains ambiguous `5.1` grades. For these cases only, an archived `5.1` or `5.10` family resolves the analysis family with an audit flag. Other cases remain unresolved. Original grade fields never change. Historical resolution is a sensitivity assumption because feature dates differ.
- Preserve missing lengths, pitch counts, quality scores and protection labels. **Not recorded does not mean safe.**
- Log-transform counts as `log(1 + count)` for regression/diagnostics and positive lengths/pitches as natural logs. Model and PCA complete-case filters apply only to those analyses.
- Flag coordinates outside a broad U.S. latitude/longitude envelope as implausible; omit them only from maps. This is an outlier check, not a validation of exact route locations.""")
    code("""data = eda.prepare_routes(raw)
core = data.loc[data.in_core_rock].copy()
tables = eda.create_tables(data)
display(tables["type_summary"])
display(tables["grade_audit"])
display(tables["missingness"].set_index("analysis_type").map(lambda value: f"{value:.1%}"))
assert len(data) == len(raw)
assert len(core) == 96735
assert core.ticks.eq(core.sampled_tick_record_count).all()
data.loc[~data.analysis_map_valid, ["route_name", "state", "area_latitude", "area_longitude"]]""")
    md("""The core population has 36,856 sport, 33,349 trad and 26,530 bouldering routes. The analysis documents 630 ice/aid/snow routes and 72 other/top-rope-only routes separately. There are 1,604 archive-supported grade-family resolutions and 29 unresolved ambiguous cases. One California route has coordinates in Australia; its counts remain in non-spatial summaries, but it is omitted from maps. Some source state labels also disagree with otherwise plausible U.S. coordinates (for example, Colorado-labeled routes located in California). State summaries/filtering use source labels; maps use source coordinates. These discrepancies remain unresolved and limit fine geographic interpretation.

Most bouldering lengths and pitch counts are unavailable. We therefore do not pretend to compare boulder length with roped length or impute all boulders to one pitch. The join-retention report describes the pre-join population; core style counts describe a later, different filter.""")
    code("""coverage = pd.read_csv(ROOT / "reports/main_join_coverage.csv")
state_coverage = coverage.groupby("state")[["input_routes", "retained_routes", "dropped_routes"]].sum()
state_coverage["retained_percent"] = 100 * state_coverage.retained_routes / state_coverage.input_routes
display(state_coverage.sort_values("retained_routes", ascending=False).head(15))
eda.create_plots(data, tables)
eda.additional_plots(data)

def show_figure(name, width=950):
    display(Image(filename=str(eda.OUT / f"{name}.png"), width=width))

show_figure("05_missingness")""")
    md("""## Recorded popularity: distribution and repeated records
Figure 1 compares the count distributions with logarithmic axes so the long tail remains visible. Figure 2 compares ticks with distinct climbers. Values above the diagonal reflect repeated user-route records, including unresolved collection duplicates. Counts are positive because the inner join excludes unobserved routes; absence from this sample is not zero real-world activity.""")
    code("""display(core.groupby("analysis_type")["ticks"].describe(percentiles=[.5, .9, .95, .99]))
show_figure("01_tick_distribution")
show_figure("06_ticks_vs_climbers")""")
    md("""## Question 1 — Which grade families are most popular?
We present both **total sample ticks** and **mean ticks per route**. The first measures recorded activity volume; the second divides by route availability in the retained sample. Neither adjusts for route age, access or reporting exposure. `5.10` combines its letter subgrades, so it is a coarse family rather than one precise difficulty.

All groups appear in the descriptive figure. To avoid choosing a highest mean from a handful of routes, the summary below requires **30 routes per grade group** when ranking means; this is not a tick threshold. Route counts and medians accompany those means.""")
    code("""grades = tables["grade_summary"].dropna(subset=["analysis_grade_family"])
winners = []
for kind in eda.COLORS:
    part = grades.loc[grades.analysis_type.eq(kind)]
    volume = part.loc[part.total_ticks.idxmax()]
    supported = part.loc[part.routes.ge(30)]
    average = supported.loc[supported.mean_ticks.idxmax()]
    winners.append({"style": kind, "highest_total_grade": volume.analysis_grade_family,
                    "total_ticks": int(volume.total_ticks), "routes_in_total_grade": int(volume.routes),
                    "highest_mean_grade_ge30_routes": average.analysis_grade_family,
                    "mean_ticks": average.mean_ticks, "median_ticks": average.median_ticks,
                    "routes_in_mean_grade": int(average.routes)})
display(pd.DataFrame(winners))
show_figure("02_grade_popularity")""")
    md(
        """**Finding:** 5.10 leads total tick records for both sport (310,717) and trad (163,711). V0 leads bouldering (36,701). Per-route means peak at 5.7 for sport and 5.6 for trad among groups with at least 30 routes. Bouldering V0–V4 means are very close: the numerical V1 lead is not a persuasive separation on its own. Changing the observation threshold changes some mean leaders, as the sensitivity section shows."""
    )
    md("""## Question 2 — How does recorded activity vary geographically?
State tables and Figure 4 distinguish tick volume from style share. Figure 5 shows fixed 0.2° coordinate cells for the contiguous U.S., with a common color scale across the three styles. These cells are **not equal-area density estimates**, and coordinates describe climbing areas rather than precise route positions. Alaska and Hawaii remain in nationwide tables and the interactive atlas.

The companion atlas supports state, style, grade, protection, length and name filters; total/mean ticks, route count, route–climber pairs and dominant-style map layers; cell inspection; and filtered CSV export. Summing distinct climbers across routes counts participation pairs, not unique people in an area.""")
    code("""state_types = tables["state_type_summary"]
state_totals = state_types.groupby("state").agg(routes=("routes", "sum"), ticks=("total_ticks", "sum"))
state_totals["mean_ticks_per_route"] = state_totals.ticks / state_totals.routes
display(state_totals.sort_values("ticks", ascending=False).head(15))
state_shares = state_types.pivot(index="state", columns="analysis_type", values="total_ticks").fillna(0)
display((state_shares.div(state_shares.sum(axis=1), axis=0) * 100).round(1).loc[state_totals.nlargest(15, "ticks").index])
show_figure("03_state_styles")
show_figure("12_geographic_ticks")""")
    md(
        """Large regional totals can reflect route availability and participation/reporting patterns. We should not label an area intrinsically more popular from totals alone. The tables allow comparisons within climbing type and grade family, and the coverage table shows where the inner join retained relatively little information."""
    )
    md("""## Question 3 — Which characteristics relate to popularity?
Figure 6 compares recorded length bands and protection categories. Interpret these as unadjusted comparisons, with denominators and missingness shown in the tables. Sparse long sport-route groups can have unstable means. Protection groups compare recorded labels; the reference does not establish safety.

Figure 7 provides pairwise Spearman associations among sport/trad features and log ticks. Pairwise available cases are used, and a separate matrix records each pair's sample size. These correlations do not hold geography, difficulty or type constant.""")
    code("""display(tables["length_summary"])
display(tables["protection_summary"])
show_figure("04_length_protection")
show_figure("11_feature_correlations")
display(pd.read_csv(eda.OUT / "correlation_pair_counts.csv", index_col=0))""")
    md("""## PCA — route profiles, with popularity as an overlay
We fit PCA to complete sport/trad routes using log length, log pitches, coarse YDS family order, Kaggle stars and three recorded protection flags. These seven features are standardized before PCA. Popularity and geographic coordinates are **not** fitted features. The bouldering scale stays out of this fit.

The left panel is a correlation biplot: standardized component scores and feature/PC correlation arrows, enlarged ×3 for display. The right panel colors the same profile projection by ticks. The plotted points are a reproducible 6,000-route sample; PCA uses all complete eligible records. The view clips scores beyond ±4.5, and the full score export preserves them.

The first two components retain about **48.0%** of feature variance. Arrow relationships are only approximations in that projection. Binary flags and ordinal grade choices affect distances; PCA is descriptive rather than a validated route similarity or safety model. [PCA documentation](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html), [feature scaling](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).""")
    code("""pca_routes, pca_metadata = eda.pca_analysis(data)
display(pd.DataFrame({"eligible": [pca_metadata["eligible_routes"]],
                      "complete_fit": [pca_metadata["fit_routes"]],
                      "excluded_missing": [pca_metadata["complete_case_exclusions"]]}))
loadings = pd.read_csv(eda.OUT / "pca_loadings.csv")
display(loadings)
show_figure("07_pca_biplot")
show_figure("08_pca_scree", width=600)""")
    md(
        """**Interpretation:** length and pitches point in similar directions and are well represented in the first two components. The protection flags are poorly represented: the two-component representation accounts for only about 6.9% of PG-13, 9.9% of R and 0.9% of X feature variance. Consequently, a short protection arrow is not evidence that protection has no association with popularity. Use the full correlations and regression instead."""
    )
    md("""## Regression — adjusted associations, not causal effects
Because the joined sample has no zeros and very skewed positive counts, we fit exploratory OLS models of **log(1 + sample ticks)** rather than raw-count linear regression. The target is transformed recorded activity conditional on appearing in the sample. This is not a complete count-generating model; it does not correct sample selection or estimate unobserved zero-count routes.

Sport/trad models include grade-family categories, state categories, type, log length, log pitches and protection flags. A quality extension adds Kaggle stars. Its baseline is refitted on **exactly the same records** so adding stars is not confused with a changed population. Bouldering is modeled separately without fabricated lengths, pitches or quality scores. Rare grade groups (<30 complete routes) are excluded from models and remain in descriptive tables.

Uncertainty intervals cluster by rounded climbing-area coordinates within state, using [statsmodels' clustered covariance](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html). Clustering cannot correct unknown shared users, route age, reporting selection or mixed observation dates. Grade categories avoid assuming equal linear grade steps. R² is **in-sample variance explained in the log outcome**, not forecast accuracy or variance explained in raw tick counts.""")
    code("""models = eda.regression_analysis(data)
comparison = pd.DataFrame(models)
display(comparison[["name", "eligible_routes", "fit_routes", "excluded_routes", "area_clusters", "r_squared", "design_rank", "design_columns"]])
assert comparison.design_rank.eq(comparison.design_columns).all()
terms = ["log_length", "log_pitches", "is_pg13", "is_r", "is_x", "average_stars"]
coefficient_tables = []
for name in ["roped_ticks_quality_baseline", "roped_ticks_quality", "roped_climbers"]:
    table = pd.read_csv(eda.OUT / f"regression_{name}.csv")
    table = table.loc[table.term.isin(terms)].copy()
    table.insert(0, "model", name)
    coefficient_tables.append(table)
display(pd.concat(coefficient_tables, ignore_index=True))
show_figure("09_regression_coefficients")
show_figure("10_regression_diagnostics")""")
    md("""**Finding:** the complete sport/trad tick model explains about 12.1% of log-outcome variance; the quality extension explains about 21.3%. Its matching baseline uses the same 61,277 routes. The length coefficient changes from positive without stars to negative with stars. Recorded PG-13/R/X designations have negative adjusted associations in these models. These results support a nuanced account of popularity rather than a causal claim about length, protection or quality. Quality ratings can also be influenced by who visits and rates routes.

Residual patterns remain. The models are interpretable EDA summaries, not validated prediction engines. Formal p-values are exploratory and are not adjusted for multiple comparisons; focus on effect sizes, uncertainty, sample composition and stability.""")
    md("""## Sensitivity checks
Compare ticks versus distinct sampled climbers; at least five ticks and at least five climbers; Kaggle-only records; exclusion of archive-resolved grades; and exclusion of roped lengths above 3,000 feet. These are alternative populations, not improvements guaranteed to remove bias. Five-record/climber thresholds truncate the popularity outcome and can change mean-grade rankings. The full population remains the main result.""")
    code("""sensitivity = eda.sensitivity_analysis(data)
display(pd.DataFrame(sensitivity))
length_effects = []
for name in ["roped_ticks_quality_baseline", "roped_ticks_quality", "roped_ticks_trimmed_length", "roped_ticks_source_grades_only"]:
    table = pd.read_csv(eda.OUT / f"regression_{name}.csv")
    row = table.loc[table.term.eq("log_length")].iloc[0]
    length_effects.append({"model": name, "length_coefficient": row.coefficient,
                           "doubling_length_association_geometric_count_plus_one_pct": 100 * np.expm1(row.coefficient * np.log(2)),
                           "ci_low": row.ci_low, "ci_high": row.ci_high})
display(pd.DataFrame(length_effects))
eda.export_web(data, pca_routes, pca_metadata)""")
    md("""Tick and distinct-climber route rankings are strongly related (Spearman correlations above 0.98 within all three styles), but they remain different quantities. Total-grade leaders stay 5.10/5.10/V0 in the five-record and five-climber comparisons; some per-route mean leaders change. Kaggle-only bouldering has only 59 classified routes, so it is not an adequate substitute for the full bouldering population.

## Conclusions and practical limits
1. Grade-family activity volume peaks at 5.10 for sport/trad and V0 for bouldering, while per-route averages tell a different story.
2. Geographic tick volume and style share vary, but source coverage and route availability accompany every comparison.
3. Length, quality and recorded protection relate to sampled activity, with the length association sensitive to quality adjustment. PCA explains profile structure, not popularity effects.

The strongest limits are sample selection, capped user histories, ambiguous repeats, absent individual dates, unknown route age/access, missing bouldering measurements, and mixed feature snapshots. Findings apply to retained historical records and should not be generalized to all climbers or current traffic. Unmatched routes cannot be assigned zero ticks. No personalized recommender is built.

## Deliverables and collaboration
The notebook, Python modules, figures, coefficient/coverage tables and interactive explorer form the analytical package. The final PDF must use the Canvas team name, be at most 11 pages and accompany the notebooks/modules in a ZIP. The final statement of work, collaboration reflection, actual meeting/check-in evidence, and any required AI-assistance disclosure need team confirmation before submission; they are not fabricated here.

The atlas is published on [Base44](https://climb-data-viz.base44.app), with the same verified aggregate counts and PCA exports as this notebook. The hosted root redirects to its static atlas entry point. See the [deployment notes](../docs/base44_handoff.md).""")
    notebook.cells = cells
    notebook.metadata = {
        "kernelspec": {
            "display_name": "Python 3 (project environment)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
    }
    target = ROOT / "notebooks/02_popularity_eda.ipynb"
    nbf.write(notebook, target)
    print(target)


if __name__ == "__main__":
    main()
