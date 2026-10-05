# Climbing popularity: EDA findings

Analysis run October 5, 2026. Historical archive committed April 21, 2019; individual observation dates unknown. These results describe retained archive records, not complete Mountain Project totals or current climbing traffic.

## Population and measurement

The main inner join contains 97,437 unique routes and 46 source/derived fields. Core comparisons use 96,735 routes: 36,856 sport, 33,349 trad and 26,530 bouldering. Ice/aid/snow (630) and other/top-rope-only records (72) remain documented separately. Trad takes precedence among rock styles. The primary outcome is **absolute sampled tick record count**, with no minimum threshold; the core population accounts for 1,939,376 records. Distinct sampled climbers are a sensitivity outcome.

Ticks may include attempts. Capped user histories, selection of users, uncertain repeated rows, missing dates, route exposure and feature snapshot differences prevent a representative or causal interpretation. The inner join drops unobserved routes; their absence is not zero actual activity.

## 1. Grade and style

| Style | Grade family with most ticks | Sample ticks | Routes in family | Highest mean family, among groups with ≥30 routes |
|---|---|---:|---:|---|
| Sport | 5.10 | 310,717 | 10,923 | 5.7 |
| Trad | 5.10 | 163,711 | 8,542 | 5.6 |
| Bouldering | V0 | 36,701 | 4,435 | V1 |

Grade families combine subgrades; YDS and V grades remain separate. Bouldering means for V0–V4 are closely grouped (about 8.2 records per route). The small numerical V1 lead is not persuasive evidence of a distinct preference. Five-record/climber sensitivity populations preserve the total-grade leaders but change some mean leaders. Denominators, medians and all grade groups are available in `grade_summary.csv`.

## 2. Geography

Colorado leads retained tick volume (386,042 records), followed by California (370,612) and Utah (207,597). California has more retained core routes than Colorado. Style shares and per-route averages answer different questions from totals. Inspect coverage and route availability alongside geographic comparisons.

The atlas offers total/mean ticks, route counts, summed route–climber pairs and dominant-style layers in fixed 0.2° cells. These are not equal-area densities. Coordinates represent climbing areas; one gross coordinate outlier is omitted from maps only. Some state labels disagree with coordinates, including Colorado-labeled routes located in California. State analyses use source labels, while maps use coordinates; finer geographic conclusions require further reconciliation.

## 3. Route characteristics, PCA and regression

PCA fits 61,282 complete sport/trad profiles using standardized log length, log pitches, ordinal YDS family, Kaggle stars and recorded PG-13/R/X flags. Popularity is an overlay. The first two components retain 48.0% of feature variance. Protection flags are poorly represented in those components; short arrows do not demonstrate weak relationships with ticks. Full scores, loadings and represented variance are exported.

The main roped log(1 + ticks) model fits 61,377 routes and has in-sample R² = 0.121. The quality extension fits 61,277 routes and has R² = 0.213. A matching baseline on exactly those 61,277 routes gives R² = 0.121, allowing a fair comparison.

The log-length coefficient changes from +0.157 in the same-case baseline (95% area-clustered interval +0.117 to +0.196) to −0.123 with stars (−0.162 to −0.085). These correspond to roughly +11.5% and −8.2% in geometric count-plus-one for a doubling in length, conditional on modeled covariates. They are not changes in arithmetic expected ticks or causal effects. Recorded PG-13/R/X labels have negative adjusted associations. Missing designation does not establish safety.

The separate bouldering model fits 26,488 routes with R² = 0.089. It does not invent missing length, pitch or quality measurements. Nine fitted specifications include alternative outcomes, quality adjustment, thresholds, length trimming and exclusion of archive-resolved grades. Design matrices are full rank; residual diagnostics and limitations accompany coefficients. Area-clustered intervals cannot remove collection bias or shared-user dependence across areas.

## Deliverables and remaining review

The executed notebook, modular code, figures, model tables, data exports, ten-page PDF review draft and local explorer are complete. Base44 hosting is pending an enabled integration and verified deployment. Actual team contributions, collaboration reflection, meeting/check-in evidence and course AI-disclosure requirements must be confirmed before removing report draft markings or submitting the ZIP.
