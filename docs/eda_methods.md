# Agreed EDA specification and interpretation

The project's primary outcome is **absolute historical sample tick records**, `sampled_tick_record_count`. Distinct sampled climbers are a sensitivity comparison. No five-tick minimum applies. The outcomes count archived participation; they are not verified sends, complete MP totals, or dated traffic measures.

## Population and classification

Keep all 97,437 matched routes in the main dataset. Core comparisons include 96,735 routes: 36,856 sport, 33,349 trad and 26,530 bouldering. Exclude any ice/aid/snow flag before rock classification (630 routes); document other/top-rope-only routes separately (72). Among remaining routes, trad takes precedence over bouldering and sport, and bouldering precedes sport. Route labels identify reported types rather than independently verified protection requirements.

Keep YDS and V comparisons separate. Coarse grade families group letter/suffix subgrades; V ranges use the lower bound. YDS numbers are never decimal arithmetic. Apparent Kaggle `5.1` export ambiguity is handled only in an analysis field: 1,604 archived `5.1`/`5.10` families support a resolution, 29 cases remain unresolved. Historical resolution may introduce temporal differences, so it is flagged and checked by exclusion. Original grades are preserved.

Keep missing values rather than replacing them with zero or dropping incomplete rows from every analysis. `Not recorded` protection is not an assurance of safety. Bouldering length/pitch/star coverage is too limited for the same physical-feature model as sport/trad. One route's coordinates are outside a broad U.S. envelope and are omitted from maps only. The envelope check does not verify state borders or precise locations.

## Descriptive comparisons

Report total, mean, median and number of routes together. Totals reflect activity volume plus available routes. Mean ticks per route divide by retained route count, not exposure time, visits or attempts. Rankings of group means require at least 30 routes to avoid tiny groups; this is not a route-popularity filter. Missing/unresolved grades retain their audit counts.

State/style/grade tables accompany geographic maps. The static spatial chart focuses on the contiguous U.S.; nationwide tables and the interactive atlas include Alaska and Hawaii. Map cells are fixed 0.2-degree latitude/longitude bins, not equal-area densities. Empty cells mean no matching records. Shared climbing-area coordinates can stack many routes. Color intensity uses a log scale, while popups show absolute counts.

Pairwise Spearman feature correlations use available sport/trad cases with pair-count matrices. They are unadjusted associations. Log ticks and log lengths preserve rankings, so these transformations do not change the corresponding Spearman ranking relationships.

## PCA

Fit complete sport/trad records: 61,282 from 70,205 eligible. Use standardized log length, log pitches, coarse ordinal YDS family, Kaggle stars, PG-13, R and X flags. Exclude popularity and coordinates from fitted features. Record all components, variance, loadings, scaler means and scales, and all route scores.

The biplot plots scores divided by component standard deviations. Arrows are component/feature correlations (`components.T * sqrt(explained_variance) / standardized_feature_sample_SD`), enlarged threefold for display. Leaders separate text labels from arrow tips. The sample/population standardization difference is corrected in the loading calculation. First two components explain about 48.0% of total variance. Per-feature represented variance (`PC1_loading² + PC2_loading²`) exposes weak representation of protection flags. Do not infer full-space relationships from short arrows. Display samples 6,000 routes using seed 593 and clips scores outside ±4.5; the complete score export preserves those routes.

Binary-flag scaling and ordinal grade encoding affect PCA geometry. This is descriptive EDA, not a validated similarity or safety score. Bouldering does not enter the roped PCA.

## Regression

Fit OLS to `log(1 + sample count)`, conditional on routes observed in the archive. This provides an exploratory transformed-outcome association model; it is not a full count-process model and does not fix zero truncation or sampling selection. Roped models use categorical grade families and states, trad versus sport, log length, log pitches and recorded protection flags. Quality models add only Kaggle stars, without pooling score scales. The quality baseline is fit to exactly the same eligible records as the quality extension. Bouldering models are separate and omit unavailable physical/quality measurements. Grade groups with fewer than 30 complete cases remain descriptive but leave model estimation.

Area-clustered intervals use state plus coordinates rounded to 0.001 degrees. They address dependence within a recorded area, but not unknown shared users across areas or collection bias. Full-rank design checks and residual plots accompany estimation. R² is in-sample variance explained in the log outcome, not raw-count fit or prediction accuracy. Coefficients describe geometric `(count + 1)` associations; a log-length coefficient β implies `100 * (exp(β * log(2)) - 1)` percent association for doubling length, conditional on the specification. Do not describe that as an arithmetic expected-count ratio or causal effect.

P-values are exploratory, with no multiple-testing-adjusted confirmatory claim. State and grade dummy coefficients depend on reference levels. The source does not include route age, exposure/visits, approach/access or comparable observation windows. Quality scores can both relate to participation and be influenced by who visits.

## Sensitivity checks

Compare tick and climber outcomes, >=5 record and >=5 climber populations, source-only populations, omission of archive-resolved grades, and roped lengths <=3,000 feet. Outcome-based thresholds change the target population and can change mean-grade leaders. They are robustness comparisons, not corrections guaranteed to reduce bias.

## Reproduction

Run `download.py`, `build_main.py`, then `eda.py`. The EDA notebook calls the same modular functions and regenerates its tables/figures. `execute_notebook.py` runs a real temporary kernel from the project's Python environment using local IPC and cleans it up. It rejects error/warning output. Tests verify critical grade/type/retention decisions. The report builder requires `requirements-report.txt` in addition to the core environment.

References: [scikit-learn PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html), [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html), [statsmodels clustered covariance](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html).

Geographic source labels and coordinates are not fully reconciled. Some Colorado-labeled routes have California coordinates, for example. State summaries and filters follow source labels; maps follow coordinates. The broad U.S. envelope check catches one gross outlier, but does not validate state boundaries or every location.
