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
