"""Build a ten-page team-review PDF from verified EDA outputs (not final submission)."""

import json
from html import escape
from pathlib import Path

import pandas as pd
from report_figures import build_report_figures
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
        ("BodyItalic", "DejaVuSans-Oblique.ttf"),
        ("Title", "DejaVuSerif.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(font_root / file)))
    pdfmetrics.registerFontFamily(
        "Body",
        normal="Body",
        bold="BodyBold",
        italic="BodyItalic",
        boldItalic="BodyBold",
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
    styles.add(
        ParagraphStyle(
            name="ReferenceProject",
            parent=styles["BodyTextProject"],
            fontSize=8.4,
            leading=12,
            leftIndent=14,
            firstLineIndent=-14,
            spaceAfter=10,
        )
    )
    data, states = build_report_figures()
    grades = pd.read_csv(EDA / "grade_summary.csv")
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

    def table(rows, widths, padding=7):
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
                    ("TOPPADDING", (0, 0), (-1, -1), padding),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8e1dd")),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 12))

    def nextpage():
        story.append(PageBreak())

    repo = "https://github.com/ElliottGorsuch/climbing-route-popularity"
    notebook = repo + "/blob/main/notebooks/02_popularity_eda.ipynb"
    atlas = "https://climb-data-viz.base44.app"

    def link(url, label):
        return f'<link href="{url}" color="#287060">{label}</link>'

    p("What makes a climb popular?", "ProjectTitle")
    p(
        "A historical look at U.S. climbing routes<br/>John Elliott Gorsuch and Victor Lee | SIADS 593 | Team-review draft",
        "CaptionProject",
    )
    heading("Motivation and research questions")
    p(
        "As climbers, we want to know what makes certain routes get climbed more than others. Is it the grade, the style, the location, or the route itself? We use recorded ticks to explore which features go along with popular climbs."
    )
    p(
        "We ask three questions: (1) Which grades and climbing styles get the most ticks? (2) How do popularity and style mix change across the U.S.? (3) How do length, pitches, star ratings and protection designations relate to popularity? We keep roped YDS grades and bouldering V grades separate."
    )
    heading("Executive summary")
    p(
        "Our core dataset has <b>96,735 rock climbs and 1,939,376 historical tick records</b>. <b>5.10 leads total ticks for both sport and trad, and V0 leads bouldering.</b> But the biggest total and the highest average per route answer different questions."
    )
    p(
        "<b>Sport 5.7 has the highest mean of any style-grade group: 47.3 ticks per route across 1,722 routes.</b> Here are the top three means within each style:"
    )
    rows = [["Style", "1st: grade / mean", "2nd: grade / mean", "3rd: grade / mean"]]
    for kind in ["Sport", "Trad", "Bouldering"]:
        top = grades.loc[grades.analysis_type.eq(kind) & grades.routes.ge(30)].nlargest(
            3, "mean_ticks"
        )
        rows.append(
            [kind]
            + [
                f"{r.analysis_grade_family} / {r.mean_ticks:.2f}"
                for r in top.itertuples()
            ]
        )
    table(rows, [90, 126, 126, 126])
    p(
        "Means are ticks per route; rankings require at least 30 routes per grade group, not 30 ticks. Sport 5.3 has only 49 routes. V1 and V0 round to the same mean and are nearly tied. No minimum-tick filter is used.",
        "CaptionProject",
    )
    p(
        "Geography changes the mix of sport, trad and bouldering activity. Length also tells a more complicated story once we account for star ratings. Our "
        + link(atlas, "interactive Climbing Atlas")
        + " lets readers explore the same data by location, style and grade."
    )
    p(
        "These are patterns in a historical sample, not complete Mountain Project totals. Earlier projects explored popularity by grade (Wilder, 2014) and sport-route characteristics (Present et al., n.d.); we bring those ideas together with a reproducible joined dataset.",
        "CaptionProject",
    )
    nextpage()

    heading("Data sources and how we combined them")
    p(
        "We started with route descriptions, added a historical tick archive, and then attached a second source of rating information. Each source brings something different to the project."
    )
    table(
        [
            ["Source", "What it adds", "How we accessed it"],
            [
                "Kaggle (Galban, n.d.)",
                "151,037 route rows with grades, styles, location, stars, pitches and length.",
                "Published CSV ZIP, version 2.",
            ],
            [
                "Georgia Tech archive (Ajayi et al., 2019)",
                "2,115,034 tick-derived rows from 47,002 users, covering 118,018 route IDs. Also includes historical route metadata.",
                "Published CSV/JSON ZIPs at pinned commit d1d75b...",
            ],
            [
                "OpenBeta (n.d.)",
                "41 state rating archives; adds rating-record counts for 63,639 routes in our main dataset.",
                "Published CSV ZIPs at pinned commit 51a046...",
            ],
        ],
        [113, 220, 135],
    )
    p(
        "The download script saves the source files and logs their URLs, sizes, retrieval times and checksums. We can therefore check exactly which files went into the analysis. OpenBeta rating counts are supplemental; they are not tick counts."
    )
    heading("Join population: the process we followed")
    p(
        "First, we cleaned the 151,037 Kaggle routes and added 48,046 U.S. bouldering routes from the historical archive that were missing from Kaggle. That gave us 199,083 unique routes with feature data."
    )
    p(
        "Next, we counted tick records and distinct climbers for each Mountain Project route ID. We used an <b>inner join on that ID</b> to keep routes present in both the feature table and the tick totals. This retained <b>97,437 routes</b> and dropped 101,646 routes without sampled ticks. We then attached extra metadata and rating totals with left joins, so those additions did not remove any routes."
    )
    p(
        "The result contains 70,907 Kaggle routes and 26,530 historical boulder additions. We matched route IDs rather than guessing from names. A missing route means we have no sampled tick data for it; it does not mean nobody climbed it."
    )
    p(
        "This process is reproducible: download.py retrieves the pinned inputs, and build_main.py rebuilds the join. Our "
        + link(notebook, "EDA notebook")
        + " documents the data and analysis choices, then reproduces the summaries and models from the main table. The source scripts make the earlier join steps reproducible too."
    )
    heading("Dates, privacy and reuse limits")
    p(
        "The tick archive was committed on April 21, 2019, but individual tick dates and its observation cutoff are unknown. Kaggle and OpenBeta come from different snapshots. User IDs are used only to build aggregate counts and are excluded from releases. Kaggle and OpenBeta declare CC0 for their data; the research tick archive has no declared data license. Our MIT code license does not license the original records. We did not scrape current Mountain Project pages."
    )
    nextpage()

    heading("Exploratory data analysis (EDA)")
    p(
        "We kept the main comparison focused on rock climbing: <b>36,856 sport, 33,349 trad and 26,530 bouldering routes</b>. The full table still includes 630 ice, aid or snow routes and 72 other/top-rope-only records, but we leave them out of the core comparisons."
    )
    p(
        "To avoid counting a mixed route twice, we exclude ice/aid/snow flags first. For the remaining routes, any trad designation puts the climb in trad; otherwise bouldering takes priority, then sport. A sport/trad route therefore counts as trad because it includes trad gear."
    )
    p(
        "We group roped grades into YDS families: 5.10a through 5.10d all count as 5.10. Boulders stay on the V scale; ranges use the lower grade, and V-easy/VB stay separate. We also found source grades that appeared to lose the zero in 5.10. Historical grades helped resolve 1,604 cases; 29 stay unresolved. We keep the original grades and flag each correction, then check results without those corrections."
    )
    p(
        "Boulders are not pitched climbs, and this archive usually has no comparable length-in-feet or Kaggle star data for them. We do not invent those values. Protection designations such as PG-13, R and X are optional: an absent designation means <b>not recorded</b>, not necessarily safe. We still have plenty of grade, style, location and tick data for the main EDA."
    )
    image("05_missingness", width=410)
    p(
        "Figure 1. Missing data by climbing style. Most historical boulders lack length, pitches and Kaggle stars. We use those features where available for sport/trad analyses, and keep bouldering comparisons focused on the fields we actually have. Length follows the source's feet convention.",
        "CaptionProject",
    )
    nextpage()

    heading("Popularity: most routes have a few ticks")
    image("popularity_bins_report")
    p(
        "Figure 2. Each bar shows the percentage of a style's routes in a tick-count range. For example, '2-4' means two to four recorded ticks per route. All three panels use the same percentage scale. Every retained route has at least one sampled tick; we apply no five-tick minimum.",
        "CaptionProject",
    )
    summaries = [["Style", "Routes", "Median ticks", "Mean ticks", "100+ ticks"]]
    for kind in ["Sport", "Trad", "Bouldering"]:
        ticks = data.loc[data.analysis_type.eq(kind), "ticks"]
        summaries.append(
            [
                kind,
                f"{len(ticks):,}",
                f"{ticks.median():.0f}",
                f"{ticks.mean():.2f}",
                f"{ticks.ge(100).mean():.1%}",
            ]
        )
    table(summaries, [90, 92, 95, 95, 96])
    p(
        "A small number of heavily ticked climbs pull the averages up. That is why we show both the mean and the median: the mean captures overall activity per route, while the median describes the middle route in the sample."
    )
    p(
        "Our main measure counts every archive row. A second measure counts distinct climbers on each route. Their route rankings are very similar: correlations are about 0.996 for sport, 0.993 for trad and 0.990 for bouldering. Adding route-level climber counts across an area counts route-climber pairs, not unique people in that area."
    )
    p(
        "There is a catch with repeated records. The original collection capped each user's history at 1,000 records, and 235,763 user-route-rating rows repeat earlier entries. Without tick IDs or dates, we cannot tell which are repeat climbs and which are collection duplicates. We keep the records, but do not treat them as confirmed repeat ascents."
    )
    nextpage()

    heading("Question 1: which grades get the most ticks?")
    p(
        "The table below ranks the top three grades <b>by total ticks within each style</b>. Means and medians help us see whether a big total comes from many routes or high activity per route."
    )
    rows = [["Style", "Grade", "Routes", "Total ticks", "Mean", "Median"]]
    for kind in ["Sport", "Trad", "Bouldering"]:
        top = grades.loc[grades.analysis_type.eq(kind)].nlargest(3, "total_ticks")
        for r in top.itertuples():
            rows.append(
                [
                    kind,
                    r.analysis_grade_family,
                    f"{r.routes:,}",
                    f"{r.total_ticks:,}",
                    f"{r.mean_ticks:.2f}",
                    f"{r.median_ticks:.0f}",
                ]
            )
    table(rows, [85, 53, 80, 110, 70, 70])
    p(
        "Sport 5.10 has almost twice the ticks of sport 5.9, but fewer ticks per route: 28.45 versus 39.20. Sport 5.11 averages 17.03. The 5.10 family includes all letter subgrades and many routes, so its leading total is not the same as saying a typical 5.10 is the most popular climb."
    )
    p(
        "For a different view, these are the <b>top three grades by mean ticks per route</b>. We require at least 30 routes per group so a tiny group is less likely to lead the ranking."
    )
    rows = [["Style", "Mean leaders, highest first", "Routes in those groups"]]
    for kind in ["Sport", "Trad", "Bouldering"]:
        top = grades.loc[grades.analysis_type.eq(kind) & grades.routes.ge(30)].nlargest(
            3, "mean_ticks"
        )
        rows.append(
            [
                kind,
                "; ".join(
                    f"{r.analysis_grade_family}: {r.mean_ticks:.2f}"
                    for r in top.itertuples()
                ),
                "; ".join(
                    f"{r.analysis_grade_family}: {r.routes:,}" for r in top.itertuples()
                ),
            ]
        )
    table(rows, [85, 215, 168])
    p(
        "Sport 5.7 is the overall mean leader, even before the 30-route screen. The high sport 5.3 mean comes from just 49 routes and deserves extra caution. V1, V0 and V4 are nearly tied; V0-V4 all average roughly 8.2 ticks, so we would not call one a clear bouldering sweet spot."
    )
    p(
        "These rankings depend on the sample. A five-tick or five-climber filter keeps the total leaders the same, but changes some mean leaders. Those are sensitivity checks; the main analysis keeps all matched routes.",
        "CaptionProject",
    )
    nextpage()

    heading("Question 2: where are the ticks?")
    image("state_counts_report", width=468, height=220)
    p(
        "Figure 3. The ten states with the most historical rock-climbing ticks, ordered from highest to lowest. Bar segments show each style's contribution to the total. Exact counts appear below; the notebook includes all states in the sample.",
        "CaptionProject",
    )
    rows = [["State", "Bouldering", "Sport", "Trad", "Total"]]
    for state, r in states.head(10).iterrows():
        rows.append(
            [state]
            + [f"{int(r[c]):,}" for c in ["Bouldering", "Sport", "Trad", "Total"]]
        )
    table(rows, [104, 91, 91, 91, 91], padding=5)
    p(
        "Colorado leads total ticks, followed by California and Utah. The split by style tells another story: a state can have a large total but a very different mix of sport, trad and bouldering. Counts combine the number of available routes with activity on those routes; they do not measure regional preference on their own."
    )
    p(
        "Explore these patterns in the "
        + link(atlas, "Climbing Atlas")
        + ": filter by state, style and grade, and switch between total ticks, mean ticks, route counts and the leading style. Alaska and Hawaii remain included. Map cells are 0.2-degree bins, not equal-area densities; blank cells mean no matching sample records.",
        "CaptionProject",
    )
    nextpage()

    heading("Question 3: how do route features fit together?")
    image("pca_report")
    p(
        "Figure 4. PCA biplot for sport/trad routes. Dots represent route profiles. Arrows show how features line up with the two plotted components; arrow lengths are enlarged threefold for readability. Popularity was not used to fit PCA. The notebook adds a popularity overlay.",
        "CaptionProject",
    )
    meta = json.loads((EDA / "pca_metadata.json").read_text())
    p(
        f"Think of PCA as a way to put several route features on one map. We fit it to {meta['fit_routes']:,} sport/trad routes with complete data, using length, pitches, YDS grade family, Kaggle stars and PG-13/R/X flags. We put the features on comparable scales first (scikit-learn developers, n.d.). The two plotted directions capture {100 * sum(meta['explained_variance_ratio'][:2]):.1f}% of feature variation, so this is a useful view rather than the whole picture."
    )
    p(
        "<b>Length and pitches point in similar directions</b>, which fits the climbing interpretation: longer routes tend to have more pitches. Features with similar arrow directions tend to move together in this view; dots closer together have similar profiles in these two components."
    )
    p(
        "Protection arrows are short because this view captures little of their variation: about 6.9% for PG-13, 9.9% for R and 0.9% for X. That does not mean protection is unrelated to popularity. We need the correlation tables and regression models to explore that question."
    )
    p(
        "The figure uses a fixed 6,000-route display sample and clips points beyond +/-4.5 component-score standard deviations. Full scores remain available. Grade is a coarse ordered scale, and missing-feature exclusions can affect the picture. PCA summarizes route profiles; it does not establish cause and effect.",
        "CaptionProject",
    )
    nextpage()

    heading("Regression: what changes when we compare similar routes?")
    p(
        "A simple length-versus-ticks plot mixes together grades, states and climbing styles. Regression lets us ask a narrower question: when we account for those other features, what relationship remains between length and popularity?"
    )
    p(
        "For sport/trad, we account for grade family, state, style, length, pitches and recorded protection. A second model adds star ratings. <b>We compare those two models on the same 61,277 routes</b>, so a change is not just caused by using a different sample. Bouldering gets a separate model without missing length, pitch or quality fields."
    )
    p(
        "Tick counts have a long tail, so we model log(1 + ticks). This keeps a handful of very popular climbs from dominating the fit. The '1 +' lets the transformation handle small counts. These are exploratory comparisons, not a tested prediction system."
    )
    models = pd.read_csv(EDA / "regression_model_comparison.csv")
    rows = [["Model", "Routes", "Fit (R²)"]]
    for name, label in [
        ("roped_ticks_quality_baseline", "Sport/trad, without stars"),
        ("roped_ticks_quality", "Same sport/trad routes, with stars"),
        ("boulder_ticks", "Bouldering, separate model"),
    ]:
        r = models.loc[models.name.eq(name)].iloc[0]
        rows.append([label, f"{int(r.fit_routes):,}", f"{r.r_squared:.3f}"])
    table(rows, [270, 95, 103])
    p(
        "R² measures how much variation the model describes in the logged outcome, using the data it was fitted on. Adding stars improves that fit from about 12% to 21%. This is not the percent of raw ticks explained or evidence of prediction accuracy on new routes.",
        "CaptionProject",
    )
    heading("The main takeaway: length depends on context")
    table(
        [
            ["Comparing routes twice as long", "Length association"],
            ["Without accounting for stars", "+11.5%"],
            ["After accounting for stars", "-8.2%"],
        ],
        [335, 133],
    )
    p(
        "These percentages describe the model's geometric (ticks + 1) scale, not a change in the arithmetic average tick count. The length coefficient switches from +0.157 to -0.123. <b>We cannot simply say that longer climbs are more popular.</b> The answer changes when quality enters the comparison."
    )
    p(
        "PG-13, R and X designations have negative adjusted associations in both sport/trad models. Their comparison group is 'no designation recorded,' which is not a guarantee of safe protection. Stars can also reflect popularity, and we lack route age and access information, so none of these patterns prove a causal effect."
    )
    p(
        "The notebook includes coefficient intervals, fit checks and residual plots. Intervals allow records within a climbing area to be related (statsmodels developers, n.d.); they cannot remove sampling bias or shared-user effects. Models use complete records and grade groups with at least 30 complete routes.",
        "CaptionProject",
    )
    nextpage()

    heading("What we learned, and what we still cannot say")
    p(
        "The clearest finding is that <b>moderate grades carry much of the recorded activity</b>. The 5.10 family leads total sport and trad ticks, while V0 leads bouldering. Looking per route changes the leaders to sport 5.7, trad 5.6 and a near tie between boulder V1 and V0. Sport 5.7 has the highest mean overall."
    )
    p(
        "That gives us two useful ways to talk about popularity. Total ticks show where activity is concentrated. Mean ticks show how much activity a route gets on average within its group. We need both, plus route counts and medians, to avoid confusing a large grade group with a more popular typical route."
    )
    p(
        "Location adds another layer: states differ in total activity and style mix. Route features add still more context. The PCA shows length and pitches moving together, while regression shows that the length-popularity relationship changes after accounting for stars. There is no single feature that gives us a complete explanation of a popular climb."
    )
    heading("Checks and limits")
    p(
        "We checked distinct climbers as an alternative to tick records, five-tick/five-climber subsets, Kaggle-only routes, unresolved-source-grade choices, and lengths above 3,000 feet. The total-grade leaders survive the threshold checks, but some mean leaders change. Kaggle alone has only 59 classified boulders in the matched sample, so it cannot stand in for our fuller bouldering data."
    )
    p(
        "Our sample misses routes without archived ticks and may represent some areas better than others. User histories are capped, repeat records are ambiguous, and the time window is unknown. We also lack route age, approach difficulty, access conditions and comparable boulder measurements. These limits matter when interpreting both regional patterns and feature relationships."
    )
    p(
        "For this project, the goal is to explore those patterns honestly and make them easy to inspect. A future climber recommender could build on the work, but we have not built or validated one here."
    )
    heading("Reproducibility")
    p(
        "Start with the "
        + link(notebook, "executed Jupyter notebook")
        + " for the full EDA, figures, model details and interpretations. The "
        + link(repo, "GitHub repository")
        + " contains the source pipeline, data dictionary, pinned inputs, dependencies and instructions for rebuilding the dataset and analysis."
    )
    p(
        "The download and main-build scripts recreate the joined dataset; shared analysis modules recreate the tables, PCA, regressions and Atlas exports. The report builder also recreates the simplified report charts directly from those outputs. Join integrity, grade handling, style precedence and population preservation are covered by tests."
    )
    p(
        "The "
        + link(atlas, "published Climbing Atlas")
        + " is a companion for exploring locations and route profiles. The notebook remains the main analytical deliverable."
    )
    nextpage()

    heading("Statement of work and collaboration")
    story.append(Spacer(1, 90))
    heading("References")
    refs = [
        (
            "Ajayi, O., Croft, B., Demeo, J., Sayre, J., &amp; Zhu, J. (2019). <i>Rock climbing route recommender</i> [Data set and source code; commit d1d75b]. GitHub.",
            "https://github.com/jdemeo/Rock_Climbing_Recommendation_System",
        ),
        (
            "Galban, M. (n.d.). <i>Mountain Project rock climbing routes in the U.S.</i> (Version 2) [Data set]. Kaggle.",
            "https://www.kaggle.com/datasets/matthiasgalban/mountain-project-rock-climbing-routes",
        ),
        (
            "OpenBeta. (n.d.). <i>Climbing data: Ratings</i> [Data set; commit 51a046]. GitHub.",
            "https://github.com/OpenBeta/climbing-data/tree/main/ratings",
        ),
        (
            "Present, J., Berger, K., &amp; Boland, C. (n.d.). <i>RouteFinder: Choosing the right sport climbing route for you.</i>",
            "https://jakepresent.github.io/RouteFinder/",
        ),
        (
            "scikit-learn developers. (n.d.). <i>PCA</i> [Software documentation]. Retrieved October 6, 2026, from",
            "https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html",
        ),
        (
            "statsmodels developers. (n.d.). <i>RegressionResults.get_robustcov_results</i> [Software documentation]. Retrieved October 6, 2026, from",
            "https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html",
        ),
        (
            "Wilder, N. (2014, September 15). <i>Factoid: Most popular routes by difficulty.</i> REI Co-op, Uncommon Path.",
            "https://www.rei.com/blog/uncategorized/factoid-4-most-popular-routes-by-difficulty",
        ),
    ]
    for ref, url in refs:
        # Break long URLs at path separators while retaining their actual link target.
        display = (
            escape(url)
            .replace("/", "/<wbr/>")
            .replace(".", ".<wbr/>")
            .replace("_", "_<wbr/>")
        )
        p(ref + "<br/>" + link(url, display), "ReferenceProject")

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
