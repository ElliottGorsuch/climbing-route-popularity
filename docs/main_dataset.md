# Building the main project dataset

The main dataset inner-joins normalized route features and historical sample aggregates on `mp_route_id`. The result has 97,437 unique route IDs and 46 fields. No name-based or geographic guess is used.

## Route features

1. Normalize all 151,037 Kaggle version 2 routes, preserving grades and adding type/protection flags.
2. Retain U.S. state locations from the historical metadata and select bouldering IDs absent from Kaggle. This adds 48,046 feature rows before the tick join.
3. Combine into a 199,083-row feature table with unique MP IDs. Kaggle takes precedence for shared IDs.

The old OpenBeta UUID supplement cannot join directly to MP tick IDs. Historical bouldering metadata supplies verified MP IDs for this main dataset.

## Tick aggregates and inner join

The archive has 2,115,034 tick-derived rows for 47,002 sampled users and 118,018 route IDs. Group by route to calculate archive rows and distinct sampled users. User identifiers are omitted from outputs.

```python
sample = ticks.groupby('RouteID').agg(
    sampled_tick_record_count=('UserID', 'size'),
    sampled_climber_count=('UserID', 'nunique'),
).reset_index().rename(columns={'RouteID': 'mp_route_id'})
main = features.merge(sample, on='mp_route_id', how='inner', validate='one_to_one')
```

The inner join retains 70,907 Kaggle routes and 26,530 added historical boulders. It removes 101,646 feature rows without sample ticks. Absence from the sample is not zero real-world activity. Tick-only IDs without eligible features are also excluded.

## Additional features

Left joins append historical name/grade/type/star fields and OpenBeta rating aggregates by route ID, preserving the inner-join population. Star scores stay separate. Missing feature values are retained without a complete-case filter.

Every main row has at least one sample tick record. The optional five-sampled-climber subset has 45,866 rows. This threshold differs from the proposal's five-tick criterion.

Coverage reports show retention by state and source. Interpret EDA as association within the historical sample. User selection, truncated histories, ambiguous repeat records, and mixed feature dates limit generalization.

## Validation

Tests cover repeated-record aggregation, distinct-user counts, inner-join exclusion, duplicate/missing IDs, and grade/protection parsing. Full-data checks verify unique IDs, positive complete counts, no personal columns, and CSV/Parquet equality. Versions, checksums, and date uncertainty accompany the outputs.
