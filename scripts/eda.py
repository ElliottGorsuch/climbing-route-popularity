"""Reproducible exploratory analysis of historical sampled climbing ticks."""

import gzip
import json
import os
import re
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".runtime/matplotlib")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/eda"
COLORS = {"Sport": "#287f8e", "Trad": "#d08042", "Bouldering": "#6d67a0"}


def classify_route(row):
    """Non-rock exclusions first; any trad flag takes precedence in rock routes."""
    if any(bool(row.get(key, False)) for key in ["is_ice", "is_aid", "is_snow"]):
        return "Excluded: ice/aid/snow"
    if row.get("is_trad", False):
        return "Trad"
    if row.get("is_boulder", False):
        return "Bouldering"
    if row.get("is_sport", False):
        return "Sport"
    return "Other rock / top rope"


def grade_family(raw, boulder=False):
    """Coarse families, never decimal YDS arithmetic; V ranges use lower bound."""
    if pd.isna(raw):
        return None
    text = str(raw)
    if boulder:
        if re.search(r"\bV(?:-easy|B)(?!\w)", text, re.IGNORECASE):
            return "V-easy"
        match = re.search(r"(?<!\w)V(\d+)", text, re.IGNORECASE)
        return f"V{int(match[1])}" if match else None
    match = re.search(r"(?<!\w)5\.(\d+)", text)
    return f"5.{int(match[1])}" if match else None


def prepare_routes(routes):
    """Create transparent analysis features while retaining all source columns."""
    data = routes.copy()
    data["analysis_type"] = data.apply(classify_route, axis=1)
    data["in_core_rock"] = data.analysis_type.isin(COLORS)
    data["analysis_grade_family"] = [
        grade_family(raw, kind == "Bouldering")
        for raw, kind in zip(data.rating_raw, data.analysis_type)
    ]
    data["analysis_grade_status"] = "source grade family"
    # The source export contains apparent trailing-zero loss. Never silently
    # relabel a genuine 5.1 route; retain only archive-supported 5.1/5.10 families.
    ambiguous = (
        data.route_source.eq("kaggle_v2")
        & data.grade.eq("5.1")
        & data.analysis_type.ne("Bouldering")
    )
    historical = data.archived_rating_raw.map(grade_family)
    supported = ambiguous & historical.isin(["5.1", "5.10"])
    data.loc[ambiguous, "analysis_grade_family"] = None
    data.loc[ambiguous, "analysis_grade_status"] = "ambiguous source 5.1; unresolved"
    data.loc[supported, "analysis_grade_family"] = historical[supported]
    data.loc[supported, "analysis_grade_status"] = (
        "historical family resolves ambiguous 5.1"
    )
    data["grade_order"] = data.analysis_grade_family.map(
        lambda value: (
            -1
            if value == "V-easy"
            else int(value[1:])
            if isinstance(value, str) and value.startswith("V")
            else int(value[2:])
            if isinstance(value, str) and value.startswith("5.")
            else np.nan
        )
    )
    data["analysis_map_valid"] = data.area_latitude.between(
        18, 72
    ) & data.area_longitude.between(-180, -60)
    data["ticks"] = data.sampled_tick_record_count.astype(int)
    data["climbers"] = data.sampled_climber_count.astype(int)
    data["log_ticks"] = np.log1p(data.ticks)
    data["log_climbers"] = np.log1p(data.climbers)
    data["log_length"] = np.log(data.length_feet.astype(float))
    data["log_pitches"] = np.log(data.pitches.astype(float))
    data["protection_group"] = data.protection_rating.fillna("Not recorded")
    for name in ["is_pg13", "is_r", "is_x"]:
        data[name] = data[name].astype(int)
    data["length_band"] = pd.cut(
        data.length_feet,
        [0, 30, 60, 100, 150, 300, 600, 1500, np.inf],
        labels=[
            "≤30",
            "31–60",
            "61–100",
            "101–150",
            "151–300",
            "301–600",
            "601–1500",
            ">1500",
        ],
    )
    data["area_cluster"] = (
        data.state.astype(str)
        + ":"
        + data.area_latitude.round(3).astype(str)
        + ":"
        + data.area_longitude.round(3).astype(str)
    )
    return data


def summarize(data, groups):
    return (
        data.groupby(groups, observed=True, dropna=False)
        .agg(
            routes=("mp_route_id", "size"),
            total_ticks=("ticks", "sum"),
            mean_ticks=("ticks", "mean"),
            median_ticks=("ticks", "median"),
            total_route_climber_pairs=("climbers", "sum"),
            mean_climbers=("climbers", "mean"),
            median_climbers=("climbers", "median"),
        )
        .reset_index()
    )


def savefig(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=170, bbox_inches="tight")
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def create_tables(data):
    OUT.mkdir(parents=True, exist_ok=True)
    core = data.loc[data.in_core_rock]
    tables = {
        "type_summary": summarize(data, ["analysis_type"]),
        "grade_summary": summarize(
            core, ["analysis_type", "analysis_grade_family", "grade_order"]
        ),
        "state_type_summary": summarize(core, ["state", "analysis_type"]),
        "length_summary": summarize(core, ["analysis_type", "length_band"]),
        "protection_summary": summarize(core, ["analysis_type", "protection_group"]),
        "state_grade_summary": summarize(
            core, ["state", "analysis_type", "analysis_grade_family"]
        ),
        "grade_audit": summarize(data, ["analysis_grade_status"]),
    }
    tables["missingness"] = (
        core.groupby("analysis_type")[
            [
                "length_feet",
                "pitches",
                "average_stars",
                "analysis_grade_family",
                "protection_rating",
            ]
        ]
        .agg(lambda x: x.isna().mean())
        .reset_index()
    )
    for name, table in tables.items():
        table.to_csv(OUT / f"{name}.csv", index=False)
    return tables


def create_plots(data, tables):
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
        }
    )
    core = data.loc[data.in_core_rock]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for kind, color in COLORS.items():
        values = core.loc[core.analysis_type.eq(kind), "ticks"].sort_values()
        axes[0].plot(
            values, 1 - np.arange(len(values)) / len(values), label=kind, color=color
        )
        axes[1].hist(
            np.log10(values),
            bins=35,
            histtype="step",
            density=True,
            label=kind,
            color=color,
        )
    axes[0].set(
        xscale="log",
        yscale="log",
        xlabel="Recorded sample ticks per route",
        ylabel="Fraction of routes at or above count",
        title="A small set of routes attracts many records",
    )
    axes[1].set(
        xlabel="log₁₀(recorded sample ticks)",
        ylabel="Density",
        title="Popularity distributions differ by type",
    )
    axes[0].legend()
    axes[1].legend()
    fig.tight_layout()
    savefig(fig, "01_tick_distribution")
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    for kind, color in COLORS.items():
        values = core.loc[core.analysis_type.eq(kind), "ticks"].sort_values()
        ax.plot(
            values, 1 - np.arange(len(values)) / len(values), label=kind, color=color
        )
    ax.set(
        xscale="log",
        yscale="log",
        xlabel="Recorded sample ticks per route",
        ylabel="Fraction at or above count",
        title="Recorded participation has a long tail",
    )
    ax.legend()
    fig.tight_layout()
    savefig(fig, "distribution_report")
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for col, (kind, color) in enumerate(COLORS.items()):
        table = (
            tables["grade_summary"]
            .loc[tables["grade_summary"].analysis_type.eq(kind)]
            .dropna(subset=["grade_order"])
            .sort_values("grade_order")
        )
        for row, metric in enumerate(["total_ticks", "mean_ticks"]):
            axes[row, col].bar(table.analysis_grade_family, table[metric], color=color)
            axes[row, col].tick_params(axis="x", rotation=65)
            axes[row, col].set(
                title=f"{kind}: {'total' if row == 0 else 'mean per route'} sample ticks",
                ylabel="Sample ticks" if row == 0 else "Mean sample ticks / route",
                xlabel="Grade family",
            )
    fig.suptitle(
        "Which grade is most popular? Total activity and per-route activity answer different questions"
    )
    fig.tight_layout()
    savefig(fig, "02_grade_popularity")
    state = tables["state_type_summary"]
    top = state.groupby("state").total_ticks.sum().nlargest(15).index
    pivot = (
        state.pivot(index="state", columns="analysis_type", values="total_ticks")
        .fillna(0)
        .reindex(top)
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    pivot.plot.barh(stacked=True, color=[COLORS[k] for k in pivot.columns], ax=axes[0])
    (pivot.div(pivot.sum(axis=1), axis=0) * 100).plot.barh(
        stacked=True, color=[COLORS[k] for k in pivot.columns], ax=axes[1], legend=False
    )
    axes[0].set(
        title="States with most sample tick records",
        xlabel="Recorded sample ticks",
        ylabel="",
    )
    axes[1].set(
        title="Style share within those states",
        xlabel="Share of recorded sample ticks (%)",
        ylabel="",
    )
    fig.tight_layout()
    savefig(fig, "03_state_styles")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for kind in ["Sport", "Trad"]:
        table = (
            tables["length_summary"]
            .loc[tables["length_summary"].analysis_type.eq(kind)]
            .dropna(subset=["length_band"])
        )
        axes[0].plot(
            table.length_band.astype(str),
            table.mean_ticks,
            marker="o",
            color=COLORS[kind],
            label=kind,
        )
    axes[0].set(
        title="Recorded length and mean sample ticks",
        xlabel="Length band (feet)",
        ylabel="Mean sample ticks / route",
    )
    axes[0].tick_params(axis="x", rotation=40)
    axes[0].legend()
    table = tables["protection_summary"].pivot(
        index="protection_group", columns="analysis_type", values="mean_ticks"
    )
    table.plot.bar(ax=axes[1], color=[COLORS[k] for k in table.columns])
    axes[1].set(
        title="Recorded protection designations",
        xlabel="Not recorded ≠ safe",
        ylabel="Mean sample ticks / route",
    )
    axes[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    savefig(fig, "04_length_protection")
    fig, ax = plt.subplots(figsize=(6.8, 4.7))
    shares = pivot.head(10).div(pivot.head(10).sum(axis=1), axis=0) * 100
    shares.plot.barh(stacked=True, color=[COLORS[k] for k in shares.columns], ax=ax)
    ax.set(
        title="Style share in ten highest-volume states",
        xlabel="Share of sample tick records (%)",
        ylabel="",
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=8)
    fig.tight_layout()
    savefig(fig, "state_report")
    fig, ax = plt.subplots(figsize=(8, 5))
    table = tables["missingness"].set_index("analysis_type")
    img = ax.imshow(table.to_numpy(dtype=float) * 100, cmap="YlOrBr", vmin=0, vmax=100)
    ax.set_xticks(range(len(table.columns)), table.columns, rotation=25, ha="right")
    ax.set_yticks(range(len(table)), table.index)
    for y in range(len(table)):
        for x in range(len(table.columns)):
            ax.text(
                x,
                y,
                f"{100 * table.iloc[y, x]:.1f}%",
                ha="center",
                va="center",
                color="black",
            )
    ax.set_title("Feature coverage differs by climbing type")
    fig.colorbar(img, ax=ax, label="Missing values (%)")
    fig.tight_layout()
    savefig(fig, "05_missingness")
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, kind in zip(axes, COLORS):
        part = core.loc[core.analysis_type.eq(kind)]
        ax.hexbin(
            part.climbers,
            part.ticks,
            gridsize=45,
            xscale="log",
            yscale="log",
            mincnt=1,
            cmap="viridis",
        )
        limit = max(part.ticks.max(), part.climbers.max())
        ax.plot([1, limit], [1, limit], "--", color="#c45c33")
        ax.set(
            title=kind,
            xlabel="Distinct sampled climbers",
            ylabel="Recorded sample ticks",
        )
    fig.suptitle("Repeated records: tick counts can exceed distinct-climber counts")
    fig.tight_layout()
    savefig(fig, "06_ticks_vs_climbers")


def pca_analysis(data):
    # Keep one grade system and one score source; use complete records for PCA.
    eligible = data.loc[data.analysis_type.isin(["Sport", "Trad"])].copy()
    features = [
        "log_length",
        "log_pitches",
        "grade_order",
        "average_stars",
        "is_pg13",
        "is_r",
        "is_x",
    ]
    part = eligible.dropna(subset=features).copy()
    scaler = StandardScaler()
    z = scaler.fit_transform(part[features].astype(float))
    model = PCA(svd_solver="full").fit(z)
    scores = model.transform(z)
    # Correlation biplot: arrows are feature/PC correlations; unit-SD scores.
    part["pc1"] = scores[:, 0] / np.sqrt(model.explained_variance_[0])
    part["pc2"] = scores[:, 1] / np.sqrt(model.explained_variance_[1])
    loadings = (
        model.components_.T[:, :2]
        * np.sqrt(model.explained_variance_[:2])
        / z.std(axis=0, ddof=1)[:, None]
    )
    loading_table = pd.DataFrame(loadings, index=features, columns=["PC1", "PC2"])
    loading_table["represented_variance_pc1_pc2"] = (loading_table**2).sum(axis=1)
    loading_table.to_csv(OUT / "pca_loadings.csv", index_label="feature")
    variance = pd.DataFrame(
        {
            "component": np.arange(1, len(features) + 1),
            "explained_variance_ratio": model.explained_variance_ratio_,
        }
    )
    variance.to_csv(OUT / "pca_variance.csv", index=False)
    part[["mp_route_id", "pc1", "pc2"]].to_parquet(
        ROOT / "data/processed/pca_route_scores.parquet", index=False
    )
    labels = [
        "log length",
        "log pitches",
        "YDS family (ordinal)",
        "Kaggle stars",
        "PG-13 recorded",
        "R recorded",
        "X recorded",
    ]
    shown = part.sample(min(6000, len(part)), random_state=593)
    label_positions = [
        (2.85, 0.05),
        (2.85, -1.25),
        (0.3, 2.95),
        (1.55, 2.25),
        (-2.8, -1.3),
        (-1.7, -2.05),
        (0.25, -2.55),
    ]

    def draw_biplot(ax, label_size=9):
        for kind in ["Sport", "Trad"]:
            subset = shown.loc[shown.analysis_type.eq(kind)]
            ax.scatter(
                subset.pc1,
                subset.pc2,
                s=5,
                alpha=0.17,
                color=COLORS[kind],
                label=kind,
                rasterized=True,
            )
        for vector, label, position in zip(loadings, labels, label_positions):
            ax.annotate(
                "",
                xy=vector * 3,
                xytext=(0, 0),
                arrowprops={"arrowstyle": "->", "color": "#213f36"},
            )
            ax.annotate(
                label,
                xy=vector * 3,
                xytext=position,
                fontsize=label_size,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.8},
                arrowprops={
                    "arrowstyle": "-",
                    "linestyle": ":",
                    "lw": 0.5,
                    "color": "gray",
                },
            )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    draw_biplot(axes[0])
    for ax in axes:
        ax.set(
            xlabel=f"PC1 ({100 * model.explained_variance_ratio_[0]:.1f}% variance)",
            ylabel=f"PC2 ({100 * model.explained_variance_ratio_[1]:.1f}% variance)",
            xlim=(-4.5, 4.5),
            ylim=(-4.5, 4.5),
        )
        ax.axhline(0, lw=0.5, color="gray")
        ax.axvline(0, lw=0.5, color="gray")
    axes[0].set_title("Route-feature correlation biplot")
    axes[0].legend()
    plot = axes[1].scatter(
        shown.pc1,
        shown.pc2,
        c=np.log10(shown.ticks),
        s=5,
        alpha=0.5,
        cmap="viridis",
        rasterized=True,
    )
    axes[1].set_title("Popularity overlay (not a fitted PCA feature)")
    fig.colorbar(plot, ax=axes[1], label="log₁₀(sample ticks)")
    fig.suptitle(
        f"PCA: {len(part):,} complete sport/trad routes; arrows ×3 for display"
    )
    fig.tight_layout()
    savefig(fig, "07_pca_biplot")
    fig, ax = plt.subplots(figsize=(6.8, 4.5))
    draw_biplot(ax, label_size=9)
    ax.set(
        xlabel=f"PC1 ({100 * model.explained_variance_ratio_[0]:.1f}% variance)",
        ylabel=f"PC2 ({100 * model.explained_variance_ratio_[1]:.1f}% variance)",
        xlim=(-4.5, 4.5),
        ylim=(-4.5, 4.5),
        title="Sport/trad route profiles · correlation biplot",
    )
    ax.axhline(0, lw=0.5, color="gray")
    ax.axvline(0, lw=0.5, color="gray")
    ax.legend(loc="upper left")
    fig.tight_layout()
    savefig(fig, "pca_report")
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(variance.component, variance.explained_variance_ratio * 100, color="#287f8e")
    ax.set(
        xlabel="Principal component",
        ylabel="Variance explained (%)",
        title="PCA scree plot",
    )
    savefig(fig, "08_pca_scree")
    metadata = {
        "eligible_routes": len(eligible),
        "fit_routes": len(part),
        "complete_case_exclusions": len(eligible) - len(part),
        "features": features,
        "explained_variance_ratio": model.explained_variance_ratio_.tolist(),
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "arrow_display_multiplier": 3,
        "cautions": [
            "Popularity is an overlay, not a PCA input.",
            "Binary protection flags and ordinal grade encoding affect geometry.",
            "Missing protection designation is not safety.",
            "Two-component arrows approximate feature correlations only to the extent those features are represented.",
        ],
    }
    (OUT / "pca_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return part, metadata


def fit_regression(
    data, outcome="log_ticks", boulder=False, quality=False, name="roped_ticks"
):
    kind = ["Bouldering"] if boulder else ["Sport", "Trad"]
    part = data.loc[data.analysis_type.isin(kind)].copy()
    required = ["analysis_grade_family", "state", "area_cluster"]
    if not boulder:
        required += ["log_length", "log_pitches"]
    if quality:
        required += ["average_stars"]
    eligible = len(part)
    part = part.dropna(subset=required).copy()
    # Groups with <30 routes are reported descriptively but not modeled.
    group_counts = part.analysis_grade_family.value_counts()
    part = part.loc[
        part.analysis_grade_family.isin(group_counts[group_counts >= 30].index)
    ].copy()
    formula = outcome + " ~ C(analysis_grade_family) + C(state)"
    if boulder:
        formula += " + C(route_source)"
    else:
        formula += ' + C(analysis_type, Treatment(reference="Sport")) + log_length + log_pitches'
    for flag in ["is_pg13", "is_r", "is_x"]:
        if part[flag].sum() >= 30 and part[flag].nunique() > 1:
            formula += " + " + flag
    if quality:
        formula += " + average_stars"
    # Statsmodels/patsy expects ordinary numpy/object dtypes, not pandas nullable.
    for col in required + ["analysis_type", "route_source"]:
        if pd.api.types.is_string_dtype(part[col]):
            part[col] = part[col].astype(object)
    fit = smf.ols(formula, data=part).fit(
        cov_type="cluster",
        cov_kwds={"groups": pd.factorize(part.area_cluster)[0]},
        use_t=True,
    )
    ci = fit.conf_int()
    coefficients = pd.DataFrame(
        {
            "term": fit.params.index,
            "coefficient": fit.params.values,
            "ci_low": ci.iloc[:, 0].values,
            "ci_high": ci.iloc[:, 1].values,
            "p_value": fit.pvalues.values,
        }
    )
    coefficients["percent_change_in_geometric_count_plus_one"] = (
        np.expm1(coefficients.coefficient) * 100
    )
    coefficients.to_csv(OUT / f"regression_{name}.csv", index=False)
    pd.DataFrame(
        {
            "mp_route_id": part.mp_route_id,
            "fitted_log": fit.fittedvalues,
            "residual": fit.resid,
        }
    ).to_parquet(
        ROOT / f"data/processed/regression_{name}_diagnostics.parquet", index=False
    )
    meta = {
        "name": name,
        "formula": formula,
        "eligible_routes": eligible,
        "fit_routes": int(fit.nobs),
        "excluded_routes": eligible - int(fit.nobs),
        "area_clusters": part.area_cluster.nunique(),
        "r_squared": fit.rsquared,
        "adjusted_r_squared": fit.rsquared_adj,
        "design_rank": int(np.linalg.matrix_rank(fit.model.exog)),
        "design_columns": fit.model.exog.shape[1],
        "condition_number": fit.condition_number,
        "outcome": outcome,
        "residual_mean": float(fit.resid.mean()),
        "interpretation": "OLS on log(1 + sample count), conditional on observed routes; associations, not causal effects or arithmetic expected count ratios. Area-clustered intervals do not account for unobserved shared users or collection bias.",
    }
    return fit, coefficients, part, meta


def regression_analysis(data):
    models = [
        ("roped_ticks", data, "log_ticks", False, False),
        ("roped_climbers", data, "log_climbers", False, False),
        ("roped_ticks_quality", data, "log_ticks", False, True),
        (
            "roped_ticks_quality_baseline",
            data.dropna(subset=["average_stars"]),
            "log_ticks",
            False,
            False,
        ),
        ("roped_ticks_ge5", data.loc[data.ticks.ge(5)], "log_ticks", False, False),
        (
            "roped_ticks_trimmed_length",
            data.loc[data.length_feet.le(3000)],
            "log_ticks",
            False,
            False,
        ),
        (
            "roped_ticks_source_grades_only",
            data.loc[data.analysis_grade_status.eq("source grade family")],
            "log_ticks",
            False,
            False,
        ),
        ("boulder_ticks", data, "log_ticks", True, False),
        ("boulder_climbers", data, "log_climbers", True, False),
    ]
    results = []
    primary = None
    for name, population, outcome, boulder, quality in models:
        fit, coefficients, part, meta = fit_regression(
            population, outcome, boulder, quality, name
        )
        results.append(meta)
        if name == "roped_ticks":
            primary = (fit, coefficients, part)
    (OUT / "regression_metadata.json").write_text(json.dumps(results, indent=2) + "\n")
    pd.DataFrame(results).to_csv(OUT / "regression_model_comparison.csv", index=False)
    fit, coefficients, part = primary
    selected = coefficients.loc[
        coefficients.term.isin(["log_length", "log_pitches", "is_pg13", "is_r", "is_x"])
        | coefficients.term.str.contains("analysis_type")
    ]
    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(selected))
    ax.errorbar(
        selected.coefficient,
        y,
        xerr=np.array(
            [
                selected.coefficient - selected.ci_low,
                selected.ci_high - selected.coefficient,
            ]
        ),
        fmt="o",
        color="#287f8e",
        capsize=3,
    )
    ax.set_yticks(
        y,
        selected.term.str.replace(
            'C(analysis_type, Treatment(reference="Sport"))[T.Trad]',
            "Trad vs sport",
            regex=False,
        ),
    )
    ax.axvline(0, ls="--", color="gray")
    ax.set(
        xlabel="Coefficient on log(1 + sample ticks), 95% area-clustered interval",
        title="Adjusted associations in complete sport/trad records",
    )
    fig.tight_layout()
    savefig(fig, "09_regression_coefficients")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].hexbin(fit.fittedvalues, fit.resid, gridsize=55, mincnt=1, cmap="viridis")
    axes[0].axhline(0, color="gray", ls="--")
    axes[0].set(
        xlabel="Fitted log(1 + ticks)",
        ylabel="Residual",
        title="Residual patterns remain",
    )
    axes[1].hist(fit.resid, bins=60, color="#287f8e")
    axes[1].set(xlabel="Residual", ylabel="Routes", title="Residual distribution")
    fig.tight_layout()
    savefig(fig, "10_regression_diagnostics")
    return results


def sensitivity_analysis(data):
    rows = []
    core = data.loc[data.in_core_rock]
    for label, subset in [
        ("All core rock", core),
        ("At least 5 sample ticks", core.loc[core.ticks.ge(5)]),
        ("At least 5 sampled climbers", core.loc[core.climbers.ge(5)]),
        ("Kaggle only", core.loc[core.route_source.eq("kaggle_v2")]),
        (
            "No historical grade resolutions",
            core.loc[core.analysis_grade_status.eq("source grade family")],
        ),
    ]:
        for kind in COLORS:
            part = subset.loc[subset.analysis_type.eq(kind)]
            grades = summarize(
                part.dropna(subset=["analysis_grade_family"]), ["analysis_grade_family"]
            )
            if len(grades):
                supported = grades.loc[grades.routes.ge(30)]
                rows.append(
                    {
                        "population": label,
                        "type": kind,
                        "routes": len(part),
                        "ticks_climbers_spearman": spearmanr(
                            part.ticks, part.climbers
                        ).statistic,
                        "grade_most_total_ticks": grades.loc[
                            grades.total_ticks.idxmax(), "analysis_grade_family"
                        ],
                        "grade_highest_mean_ticks_ge30_routes": supported.loc[
                            supported.mean_ticks.idxmax(), "analysis_grade_family"
                        ]
                        if len(supported)
                        else None,
                    }
                )
    pd.DataFrame(rows).to_csv(OUT / "sensitivity_summary.csv", index=False)
    return rows


def export_web(data, pca, metadata):
    target = ROOT / "web/data"
    target.mkdir(parents=True, exist_ok=True)
    core = data.loc[data.in_core_rock].copy()
    cols = [
        "mp_route_id",
        "route_name",
        "state",
        "analysis_type",
        "analysis_grade_family",
        "grade_order",
        "area_latitude",
        "area_longitude",
        "analysis_map_valid",
        "ticks",
        "climbers",
        "length_feet",
        "pitches",
        "protection_group",
        "route_url",
    ]
    clean = core[cols].astype(object).where(core[cols].notna(), None)
    payload = {
        "version": "0.3.0-eda",
        "columns": cols,
        "rows": clean.values.tolist(),
        "metadata": {
            "archive_commit_date": "2019-04-21",
            "observation_dates": "unknown",
            "coordinates": "Climbing-area coordinates; not individual route positions",
            "tick_definition": "Historical sample archive records, including ambiguous repeats",
            "primary_measure": "ticks",
            "type_rule": "Exclude ice/aid/snow; trad > bouldering > sport",
        },
    }
    (target / "routes.json").write_text(
        json.dumps(payload, separators=(",", ":"), allow_nan=False)
    )
    shown = pca.sample(min(6000, len(pca)), random_state=593)
    pcols = [
        "mp_route_id",
        "route_name",
        "state",
        "analysis_type",
        "ticks",
        "climbers",
        "pc1",
        "pc2",
    ]
    pcadata = {
        "columns": pcols,
        "rows": shown[pcols]
        .astype(object)
        .where(shown[pcols].notna(), None)
        .values.tolist(),
        "metadata": metadata,
        "loadings": pd.read_csv(OUT / "pca_loadings.csv").to_dict("records"),
    }
    (target / "pca.json").write_text(
        json.dumps(pcadata, separators=(",", ":"), allow_nan=False)
    )
    (target / "model_summary.json").write_text(
        (OUT / "regression_metadata.json").read_text()
    )

    snapshots = ROOT / "web/snapshots"
    snapshots.mkdir(exist_ok=True)
    for name in ["routes", "pca", "model_summary"]:
        (snapshots / f"{name}.json.gz").write_bytes(
            gzip.compress((target / f"{name}.json").read_bytes(), mtime=0)
        )


def additional_plots(data):
    """Pairwise coverage and spatial activity accompany PCA projections."""
    part = data.loc[data.analysis_type.isin(["Sport", "Trad"])]
    columns = [
        "log_length",
        "log_pitches",
        "grade_order",
        "average_stars",
        "is_pg13",
        "is_r",
        "is_x",
        "log_ticks",
    ]
    values = part[columns].astype(float)
    corr = values.corr(method="spearman")
    valid = values.notna().astype(int)
    pairs = valid.T.dot(valid)
    corr.to_csv(OUT / "spearman_correlations.csv", index_label="feature")
    pairs.to_csv(OUT / "correlation_pair_counts.csv", index_label="feature")
    fig, ax = plt.subplots(figsize=(9, 7))
    image = ax.imshow(corr.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(columns)), columns, rotation=40, ha="right")
    ax.set_yticks(range(len(columns)), columns)
    for y in range(len(columns)):
        for x in range(len(columns)):
            ax.text(
                x, y, f"{corr.iloc[y, x]:.2f}", ha="center", va="center", fontsize=8
            )
    ax.set_title("Sport/trad feature associations: pairwise Spearman correlations")
    fig.colorbar(image, ax=ax, label="Spearman correlation")
    fig.tight_layout()
    savefig(fig, "11_feature_correlations")
    core = data.loc[
        data.in_core_rock
        & data.area_longitude.between(-125, -66)
        & data.area_latitude.between(24, 50)
    ].copy()
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True)
    for ax, kind in zip(axes, COLORS):
        subset = core.loc[core.analysis_type.eq(kind)]
        # Fixed 0.2-degree cells mirror the interactive atlas; not equal area.
        subset["lat_cell"] = np.floor(subset.area_latitude / 0.2) * 0.2 + 0.1
        subset["lon_cell"] = np.floor(subset.area_longitude / 0.2) * 0.2 + 0.1
        cells = subset.groupby(["lat_cell", "lon_cell"]).ticks.sum().reset_index()
        plot = ax.scatter(
            cells.lon_cell,
            cells.lat_cell,
            c=np.log10(cells.ticks),
            s=8,
            marker="s",
            cmap="YlOrRd",
            vmin=0,
            vmax=5,
        )
        ax.set(title=kind, xlabel="Longitude", xlim=(-125, -66), ylim=(24, 50))
        ax.set_aspect(1.25)
    axes[0].set_ylabel("Latitude")
    fig.colorbar(
        plot,
        ax=axes.tolist(),
        shrink=0.55,
        label="log₁₀(total sample ticks per 0.2° cell)",
    )
    fig.suptitle("Geographic sample activity by style · contiguous U.S. view")
    savefig(fig, "12_geographic_ticks")


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    data = prepare_routes(
        pd.read_parquet(ROOT / "data/processed/climbing_routes_main.parquet")
    )
    data.to_parquet(ROOT / "data/processed/climbing_routes_eda.parquet", index=False)
    tables = create_tables(data)
    create_plots(data, tables)
    additional_plots(data)
    pca, metadata = pca_analysis(data)
    regression_analysis(data)
    sensitivity_analysis(data)
    export_web(data, pca, metadata)
    quality = {
        "main_routes": len(data),
        "core_routes": int(data.in_core_rock.sum()),
        "type_counts": data.analysis_type.value_counts().to_dict(),
        "grade_status_counts": data.analysis_grade_status.value_counts().to_dict(),
        "core_total_sample_ticks": int(data.loc[data.in_core_rock, "ticks"].sum()),
        "invalid_core_map_coordinates": int(
            (data.in_core_rock & ~data.analysis_map_valid).sum()
        ),
        "primary_measure": "sampled_tick_record_count",
        "minimum_tick_filter": None,
    }
    (OUT / "analysis_population.json").write_text(json.dumps(quality, indent=2) + "\n")
    print(json.dumps(quality, indent=2))
    return data


if __name__ == "__main__":
    run()
