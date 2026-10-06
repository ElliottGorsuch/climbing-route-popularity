# Main dataset validation

Validated October 5, 2026.

- All 23 unit cases pass, including grade/protection parsing, repeated-record aggregation, strict inner joins, duplicate ID rejection, and invalid sample counts.
- The main build retains 97,437 unique Mountain Project IDs with 46 columns, including 26,743 bouldering routes.
- Both sample count fields are complete and positive; distinct climbers never exceed record counts.
- Coverage reports reconcile 199,083 input routes, 97,437 retained routes, and 101,646 dropped routes.
- CSV and Parquet agree on shape, columns, ordered route IDs, and both sample counts.
- PG-13, R, and X flags agree with parsed protection values.
- The optional five-climber subset contains exactly the 45,866 qualifying routes.
- All exploration notebook code cells execute successfully against the main dataset.
- No individual user identifiers or misleading total-tick field exists in the main dataset.
- Raw archives are excluded from Git and release packages. Counts describe the historical sample; missing source-data licensing and sampling limitations are documented.

The original feature inventory remains available separately in v0.1.0; it is superseded for current analysis by the main dataset.

## EDA and deliverables validation

- All **26** unit tests pass, including classification precedence and historical grade resolution without overwriting source grades.
- The EDA notebook executes all ten code cells with no errors or warning output.
- Core population reconciles to 96,735 routes and 1,939,376 sample records, with no five-tick minimum.
- All nine regression design matrices are full rank. The quality comparison includes a same-case baseline.
- PCA uses complete sport/trad profiles, excludes popularity from its fitted features, and exports full scores and feature representation diagnostics.
- The ten-page PDF draft was rendered and visually inspected. It remains a draft pending actual collaboration facts.
- Browser checks confirm map rendering, filter-driven counts, dominant-style legend, linked tables and PCA navigation. The published Base44 atlas loads the same full population and its V0 filter matches the notebook. Base44 lint, typecheck and production build pass.
- One gross coordinate outlier is excluded only from maps; unresolved state/coordinate disagreements are disclosed.

- Phone-width preview has no horizontal page overflow (390 px). Filtered CSV export matches 4,435 V0 boulders and 36,701 sample ticks.
