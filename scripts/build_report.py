"""Build a ten-page team-review PDF from verified EDA outputs (not final submission)."""

import json
from html import escape
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf"
EDA = ROOT / "reports/eda"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font_root = Path(__import__("matplotlib").get_data_path()) / "fonts/ttf"
    for name, file in [
        ("Body", "DejaVuSans.ttf"),
        ("BodyBold", "DejaVuSans-Bold.ttf"),
        ("Title", "DejaVuSerif.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(font_root / file)))
    pdfmetrics.registerFontFamily(
        "Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold"
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyTextProject",
            fontName="Body",
            fontSize=9.4,
            leading=14,
            spaceAfter=9,
            textColor=colors.HexColor("#263b35"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="ProjectTitle",
            fontName="Title",
            fontSize=23,
            leading=29,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ProjectHeading",
            fontName="BodyBold",
            fontSize=15,
            leading=20,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CaptionProject",
            fontName="Body",
            fontSize=8,
            leading=12,
            spaceAfter=12,
            textColor=colors.HexColor("#65716d"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableProject",
            fontName="Body",
            fontSize=8,
            leading=11,
            alignment=TA_LEFT,
        )
    )
    story = []

    def p(text, style="BodyTextProject"):
        story.append(Paragraph(text, styles[style]))

    def heading(text):
        p(text, "ProjectHeading")

    def image(name, width=468, height=None):
        path = EDA / f"{name}.png"
        w, h = ImageReader(str(path)).getSize()
        story.append(Image(str(path), width=width, height=height or width * h / w))
        story.append(Spacer(1, 8))

    def table(rows, widths):
        wrapped = [
            [Paragraph(escape(str(value)), styles["TableProject"]) for value in row]
            for row in rows
        ]
        t = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e1ece7")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8e1dd")),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 12))

    def nextpage():
        story.append(PageBreak())

    p("Climbing route popularity<br/>in a historical U.S. sample", "ProjectTitle")
    p(
        "John Elliott Gorsuch and Victor Lee | SIADS 593 | Team-review draft",
        "CaptionProject",
    )
    heading("Motivation and research questions")
    p(
        "A climbing route can attract recorded activity because of its difficulty, style, location, quality or physical commitment. We investigate which route characteristics relate to popularity, while distinguishing high total activity from high activity per available route."
    )
    p(
        "Our questions are: (1) how popularity varies with climbing type and difficulty; (2) how geographic participation and climbing-style shares differ; and (3) how length, pitches, quality and recorded protection relate to participation. Bouldering and roped grades are analyzed separately."
    )
    p(
        "Wilder's Mountain Project analysis compared popular routes within difficulty grades [1]. RouteFinder mapped sport-climbing difficulty and explored descriptive route characteristics [2]. These precedents motivate our combined grade, geographic and feature analysis. Our contribution is a documented ID-based join, an explicit historical sample outcome, and comparisons that expose sensitivity to source coverage and adjustment."
    )
    heading("What we found")
    p(
        "The matched dataset contains 97,437 routes. Core rock comparisons retain 96,735 sport, trad and bouldering routes, with 1,939,376 sample tick records. The 5.10 family leads total sport and trad activity; V0 leads bouldering. Per-route averages have different leaders. A quality-adjusted regression changes the sign of the length association, showing why a simple popularity narrative would be incomplete."
    )
    p(
        "Absolute tick records are the primary measure, with no minimum-tick cutoff. They are historical archive rows, including unresolved repeats, rather than complete Mountain Project totals or confirmed successful ascents. This report summarizes the executed notebook and its companion atlas."
    )
    p(
        "Draft status: analysis and figures are reproducible. Team contributions, collaboration evidence and any required AI-assistance disclosure must be confirmed before submission.",
        "CaptionProject",
    )
    nextpage()
    heading("Data sources and reproducible access")
    table(
        [
            ["Source", "Magnitude and content", "Access"],
            [
                "Kaggle version 2 [3]",
                "151,037 route rows; grades, types, location, stars, pitches and lengths.",
                "Published CSV ZIP; dataset version pinned.",
            ],
            [
                "Georgia Tech archive [4]",
                "2,115,034 tick-derived rows; 47,002 users; 118,018 route IDs. 189,177 metadata IDs before U.S. filtering.",
                "Published CSV ZIP and JSON ZIP; Git commit d1d75b... pinned.",
            ],
            [
                "OpenBeta ratings [5]",
                "41 state archives; rating-record counts for 63,639 main-table routes.",
                "Published CSV ZIPs; Git commit 51a046... pinned.",
            ],
        ],
        [100, 220, 148],
    )
    p(
        "The download script caches published files and records source URLs, bytes, retrieval times and SHA-256 checksums. The main build is reproducible with download.py and build_main.py. The EDA modules create figures, tables, PCA scores, regression diagnostics and website exports. Dependency versions and a full environment lock accompany the notebook."
    )
    heading("Join population")
    p(
        "Normalize 151,037 Kaggle routes and add 48,046 U.S. historical bouldering IDs absent from Kaggle, giving 199,083 unique feature IDs. Aggregate archive rows and distinct users by route. An inner join on MP ID retains 97,437 and excludes 101,646 features without sampled ticks. Additional metadata and rating aggregates are left-joined without changing the matched population. No fuzzy name matching is used."
    )
    p(
        "The main population includes 70,907 Kaggle routes and 26,530 historical boulder additions. A route absent from the archive is excluded, not assigned zero traffic. Pre-join retention is reported by state and source; those denominators differ from the subsequent rock-only population."
    )
    heading("Date, privacy and reuse limitations")
    p(
        "The archive was committed April 21, 2019; individual dates and the observation cutoff are unknown. Kaggle and OpenBeta snapshots have different dates. Raw users are used only transiently for aggregation and are excluded from releases. Kaggle/OpenBeta declare CC0 for their data; the research tick archive declares no data license. Our MIT code license does not license its original records. No current Mountain Project scraping was performed."
    )
    nextpage()
    heading("Cleaning, manipulation and analysis decisions")
    p(
        "Types are mutually exclusive for comparison: any ice, aid or snow flag is excluded first; among the rest, any trad flag wins, then bouldering, then sport. This retains 36,856 sport, 33,349 trad and 26,530 bouldering routes. The 630 ice/aid/snow and 72 other/top-rope-only records remain documented in the full table."
    )
    p(
        "Grades remain text. Roped grades are grouped into major YDS families (for example, 5.10a and 5.10d both enter 5.10); boulders use separate V families. V ranges use the lower bound, while V-easy/VB are separate. We found apparent trailing-zero loss in source 5.1 values. Archived 5.1/5.10 families resolve 1,604 analysis grades with provenance flags; 29 remain unresolved. Original source fields never change. Excluding these historical resolutions is a sensitivity check."
    )
    p(
        "Missing lengths, pitches, quality and protection values remain missing. Recorded PG-13/R/X become binary flags; missing designation is not evidence of safety. Length is treated as feet following the source convention, an assumption recorded in the dictionary. Model/PCA complete-case filters apply only to those analyses. One California boulder has coordinates in Australia; maps omit it while other analyses retain its counts."
    )
    image("05_missingness", width=410)
    p(
        "Figure 1. Missingness by core climbing type. Historical boulder additions usually lack length, pitches and Kaggle quality scores. Those gaps rule out a credible boulder-length comparison.",
        "CaptionProject",
    )
    nextpage()
    heading("Popularity distributions and repeated records")
    image("distribution_report")
    p(
        "Figure 2. Recorded participation has a long tail within each style. Logarithmic axes expose both the many low-count routes and the small set with high counts. Comparisons are conditional on at least one archive record.",
        "CaptionProject",
    )
    p(
        "The primary outcome is sampled_tick_record_count, which counts every source archive row. sampled_climber_count counts distinct user IDs for each route. Summing the latter across routes gives route-climber participation pairs, not distinct people across an area."
    )
    p(
        "The original collection capped histories at 1,000 records per user. There are 235,763 repeated user-route-rating rows beyond their first appearances. Tick IDs and dates are absent, so these repeats cannot be classified reliably as genuine repeat climbs or collection duplicates. The repeat-climbing interpretation is therefore plausible but unverified."
    )
    p(
        "Within all core rock records, tick and climber route ranks are strongly related: Spearman correlations are approximately 0.996 for sport, 0.993 for trad and 0.990 for bouldering. This supports checking both quantities, but does not establish complete or representative participation."
    )
    p(
        "Means are sensitive to the tail, so descriptive tables include medians, group counts and totals. The five-tick and five-climber populations are sensitivity checks only; the primary population uses no such filter."
    )
    nextpage()
    heading("Question 1: grade and climbing style")
    grades = pd.read_csv(EDA / "grade_summary.csv")
    rows = [["Style", "Largest total", "Sample ticks", "Highest mean*", "Mean ticks"]]
    for kind in ["Sport", "Trad", "Bouldering"]:
        t = grades.loc[grades.analysis_type.eq(kind)].dropna(
            subset=["analysis_grade_family"]
        )
        volume = t.loc[t.total_ticks.idxmax()]
        supported = t.loc[t.routes.ge(30)]
        average = supported.loc[supported.mean_ticks.idxmax()]
        rows.append(
            [
                kind,
                volume.analysis_grade_family,
                f"{int(volume.total_ticks):,}",
                average.analysis_grade_family,
                f"{average.mean_ticks:.2f}",
            ]
        )
    table(rows, [85, 92, 98, 98, 95])
    p(
        "* Highest means are ranked only among groups containing at least 30 routes, not 30 ticks. All groups remain in the descriptive notebook.",
        "CaptionProject",
    )
    p(
        "The 5.10 family has 10,923 sport routes and 8,542 trad routes in the retained sample. It leads total tick volume for both styles, but this broad family includes letter subgrades and has more routes than many lower families. Total activity does not isolate the popularity of a typical route."
    )
    p(
        "Mean ticks peak at 5.7 for sport (47.31 per route; 1,722 routes) and 5.6 for trad (36.87; 2,171 routes). V0 leads total boulder activity (36,701 ticks; 4,435 routes). V1 has the highest supported boulder mean (8.28; 3,893 routes), but V0-V4 means are very close. These differences should not be presented as strong evidence of a unique boulder-grade optimum."
    )
    p(
        "Filtering to five tick records or five sampled climbers leaves the total-volume leaders unchanged, while mean leaders change for sport and bouldering. This illustrates how selecting on the popularity outcome affects the claim about a 'most popular grade.'"
    )
    p(
        "The full notebook provides total and per-route panels for every grade family, route counts, medians and state-grade tables. Letter/suffix grouping and historical grade resolution are explicit manipulation choices, not implied precision about physical difficulty."
    )
    nextpage()
    heading("Question 2: geography and style shares")
    image("state_report")
    p(
        "Figure 3. Climbing-style shares in the ten states with highest recorded tick volume. The companion notebook shows totals as well as shares; these answer different questions.",
        "CaptionProject",
    )
    p(
        "The state and geographic-cell summaries use the same core classification. The interactive atlas can filter style, state, grade family, recorded protection, name and length, then show total ticks, mean ticks per route, route counts, route-climber pairs or the leading style by ticks. Cell inspection links to its highest-recorded routes."
    )
    p(
        "The static spatial figure in the notebook uses a contiguous-U.S. view. Alaska and Hawaii remain in nationwide tables and the atlas. Fixed 0.2-degree latitude/longitude cells are not equal-area densities, and coordinates can be shared climbing-area locations. Some source state labels disagree with coordinates; state summaries use labels and maps use coordinates. Empty cells mean no matching retained records, not proof of no climbing."
    )
    p(
        "Regional comparisons must accompany route counts and pre-join retention. These data cannot distinguish climbing opportunities, route age, reporting habits, access conditions or source sampling from intrinsic regional preference. We therefore describe recorded activity patterns rather than universal claims about which style a region's climbers prefer."
    )
    nextpage()
    heading("Question 3: feature relationships and PCA")
    image("pca_report")
    p(
        "Figure 4. A sport/trad correlation biplot. Points use unit-SD component scores; feature/PC correlation arrows are enlarged by three. Dashed leaders separate labels from arrow tips. Popularity is not fitted into PCA; its overlay appears in the notebook.",
        "CaptionProject",
    )
    meta = json.loads((EDA / "pca_metadata.json").read_text())
    p(
        f"PCA fits {meta['fit_routes']:,} complete sport/trad routes from {meta['eligible_routes']:,} eligible records. Features are standardized log length, log pitches, coarse YDS ordinal family, Kaggle stars and recorded PG-13/R/X flags. The first two components retain {100 * sum(meta['explained_variance_ratio'][:2]):.1f}% of overall feature variance. The displayed points are a fixed 6,000-route sample, clipped outside +/-4.5 component-score SDs; complete scores are exported."
    )
    p(
        "Length and pitches point in similar directions and are well represented. Protection flags are poorly represented in these two components: about 6.9% for PG-13, 9.9% for R and 0.9% for X. A short protection arrow does not establish a weak relationship with popularity. The pairwise Spearman matrix and adjusted regressions supply complementary evidence."
    )
    p(
        "PCA depends on binary-flag scaling and an ordinal approximation of grade. It summarizes feature geometry, rather than proving causal relationships or a validated similarity metric. The complete-case sample differs from the full dataset and can introduce additional selection."
    )
    nextpage()
    heading("Regression: adjusted, conditional associations")
    p(
        "We fit exploratory OLS models of log(1 + sampled ticks), rather than a raw-count linear model. Sport/trad models include categorical grade family and state, trad versus sport, log length, log pitches and recorded protection flags. A quality extension adds Kaggle stars. Its comparison baseline uses exactly the same records. Separate boulder models omit unavailable length/pitch/quality features. Grade groups with fewer than 30 complete routes are excluded from modeling."
    )
    p(
        "Intervals use climbing-area clusters (state plus coordinates rounded to 0.001 degrees). This allows within-area dependence but cannot resolve shared users, collection truncation or missing exposure. Full-rank design matrices are checked. R-squared describes in-sample variance in the transformed outcome, not raw-count explanation or forecast accuracy."
    )
    models = pd.read_csv(EDA / "regression_model_comparison.csv")
    rows = [["Model", "Routes", "Log-outcome R²"]]
    for name, label in [
        ("roped_ticks", "Roped tick baseline"),
        ("roped_ticks_quality_baseline", "Same-case baseline"),
        ("roped_ticks_quality", "Same-case + stars"),
        ("boulder_ticks", "Boulder ticks"),
    ]:
        row = models.loc[models.name.eq(name)].iloc[0]
        rows.append([label, f"{int(row.fit_routes):,}", f"{row.r_squared:.3f}"])
    table(rows, [225, 110, 133])
    p(
        "Adding stars raises same-case R-squared from 0.121 to 0.213. The log-length coefficient changes from approximately +0.157 without stars to -0.123 with stars. This corresponds to associations of about +11.5% versus -8.2% in geometric (ticks + 1) for doubling length, conditional on the model. These are not arithmetic count ratios or causal effects."
    )
    p(
        "Recorded PG-13/R/X have negative adjusted associations in both model specifications. The models compare designations with an unrecorded reference, which must not be called a safe group. Quality can reflect participation as well as influence it, and unknown route age/access can confound all these associations."
    )
    p(
        "Residual patterns remain, and the analysis is exploratory. No multiple-testing-adjusted confirmatory claim or held-out predictive-performance claim is made. The notebook contains coefficient intervals, residual figures and model-population tables."
    )
    nextpage()
    heading("Sensitivity, conclusions and limitations")
    p(
        "Sensitivity analyses compare distinct climbers with tick records, five-record and five-climber subsets, Kaggle-only rows, exclusion of historical grade resolutions, and exclusion of roped lengths above 3,000 feet. Total-grade leaders persist across the two threshold checks; some mean-grade leaders change. Kaggle-only bouldering retains only 59 classified routes and cannot replace the fuller historical boulder population."
    )
    p(
        "The principal conclusions are descriptive: 5.10 and V0 lead activity volume in their respective families; per-route averages distinguish a different aspect of participation; geography changes activity composition; and associations involving length depend on adjustment for quality. PCA explains route-profile structure, while regressions address conditional popularity relationships."
    )
    p(
        "Limits include nonrandom user selection, capped histories, ambiguous repeats, unknown observation dates, absent route age and accessibility, geography-dependent source coverage, missing boulder measurements, and mixed feature dates. Removing unobserved routes and complete-case filtering can both introduce selection. Area-clustered intervals do not make this sample representative."
    )
    heading("Reproducibility and submission package")
    p(
        "The executed notebook is notebooks/02_popularity_eda.ipynb. Shared modules implement transformations, summaries, PCA, regressions and export. Tests cover grade ambiguity, mixed-type precedence, exclusions, join integrity and preservation of the primary population. The standalone pipeline reproduces the analytical outputs; the environment and sources are pinned and documented."
    )
    p(
        "The final Canvas ZIP should contain this named PDF, polished notebooks and supporting Python modules, plus dependencies, definitions and reproducible data access. A website supplements those requirements. This draft stays below the 11-page limit, but final collaboration text must replace the next page's review items before submission."
    )
    nextpage()
    heading("Statement of work and collaboration: pending team review")
    p(
        "Team members: John Elliott Gorsuch and Victor Lee. The user has set the research questions and analytical preferences. The project assets now contain the source pipeline, joined dataset, EDA modules, notebook, figures and local atlas. That asset history does not establish the individual coursework contributions of both team members."
    )
    p(
        "Before submission, the team must record each person's actual tasks, their joint review/interpretation work, how collaboration went, and what they would improve next time. Add actual dates, progress, challenges and decisions for synchronous meetings and Slack check-ins. Do not present plans as completed meetings or assign work to Victor without confirmation."
    )
    p(
        "The supplied rubric's highest status-update band requires at least three video-based synchronous meetings and one or more Slack check-ins. Verify the expanded course guidelines, the Canvas team name and any AI-assistance disclosure requirements. These are the remaining team-review items, not analytical findings."
    )
    heading("References")
    refs = [
        '[1] Wilder, N. (2014). Factoid: Most Popular Routes by Difficulty. REI Uncommon Path. <link href="https://www.rei.com/blog/uncategorized/factoid-4-most-popular-routes-by-difficulty">Article</link>.',
        '[2] Present, J., Berger, K., and Boland, C. RouteFinder. <link href="https://jakepresent.github.io/RouteFinder/">Project report</link>.',
        '[3] Galban, M. Mountain Project Rock Climbing Routes in the U.S., version 2. <link href="https://www.kaggle.com/datasets/matthiasgalban/mountain-project-rock-climbing-routes">Kaggle</link>.',
        '[4] Ajayi, O., Croft, B., Demeo, J., Sayre, J., and Zhu, J. Rock Climbing Recommendation System. Commit d1d75bbeb143d4fc863dc1d36173b15b9c0f6ba3. <link href="https://github.com/jdemeo/Rock_Climbing_Recommendation_System">Research archive</link>.',
        '[5] OpenBeta. Historical climbing ratings. Commit 51a0461a44078148135561c651d25a9203330609. <link href="https://github.com/OpenBeta/climbing-data/tree/main/ratings">Repository</link>.',
        '[6] scikit-learn. PCA and StandardScaler documentation. <link href="https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html">PCA</link>.',
        '[7] statsmodels. RegressionResults.get_robustcov_results documentation. <link href="https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html">Clustered covariance</link>.',
    ]
    for ref in refs:
        p(ref, "CaptionProject")

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Body", 7)
        canvas.setFillColor(colors.HexColor("#65716d"))
        canvas.drawString(
            55,
            30,
            "TEAM-REVIEW DRAFT | Historical sample, not complete Mountain Project totals",
        )
        canvas.drawRightString(557, 30, str(doc.page))
        canvas.restoreState()

    path = OUT / "John Elliott Gorsuch and Victor Lee.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=45,
        bottomMargin=50,
        title="Climbing route popularity in a historical U.S. sample",
        author="John Elliott Gorsuch and Victor Lee",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(path)


if __name__ == "__main__":
    main()
