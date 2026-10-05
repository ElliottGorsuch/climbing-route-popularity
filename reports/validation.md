# Initial snapshot validation

Validated October 5, 2026.

- All 16 unit cases pass: YDS and V grade parsing, protection codes, missing grades, tick missingness, confirmed zero ticks, invalid counts, and duplicate tick IDs.
- Full source build completes with 227,812 unique source keys and no repeated nonmissing MP IDs.
- PG-13, R, and X flags agree with parsed protection values.
- CSV and Parquet have equal row counts and route-key values.
- The analysis subset is empty, consistent with zero actual tick observations.
- All exploration notebook code cells execute successfully against the built dataset.
- No user-identifier column exists in the processed dataset or release bundle.
- Raw and processed files are excluded from Git; releases include processed data only.
