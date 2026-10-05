# Route dataset fields

Each row represents a source route record. `route_key` uniquely identifies a row across sources. Mountain Project and OpenBeta use different identifiers. Possible overlaps are retained and marked for review; row counts therefore are not guaranteed counts of distinct physical climbs.

| Field | Meaning |
| --- | --- |
| route_key | `mp:<numeric ID>` for Kaggle or `ob:<UUID>` for the OpenBeta supplement |
| mp_route_id / openbeta_route_id | Source identifiers; missing when that source does not supply the ID |
| route_name / route_url | Original route name and link to the source |
| route_source | Kaggle version 2 or OpenBeta export v2026-10-04 |
| location / state / country | Source location hierarchy and state; only USA records included |
| rating_raw | Original grade text preserved for auditing |
| grade / grade_system | Textual grade and YDS, V, or other; grades are not decimal numbers |
| grade_vscale | V-scale grade when present, including mixed YDS/V ratings |
| protection_rating | PG-13, R, X, or missing when no recognized designation was recorded |
| is_pg13 / is_r / is_x | Explicit protection-designation flags; no recorded designation does not mean a climb is safe |
| route_type | Source type labels; routes may have several types |
| is_sport / is_trad / is_boulder / is_top_rope / is_alpine / is_aid / is_ice / is_snow | Nullable flags; unknown source types stay missing |
| pitches | Positive pitch count; OpenBeta supplement does not supply it |
| length_feet / length_meters | Positive source length or converted equivalent; source sentinels become missing |
| area_latitude / area_longitude | Coordinates of the climbing area; not necessarily precise route coordinates |
| average_stars | Kaggle source quality score, 0–4; invalid values become missing |
| rating_record_count | Number of historical OpenBeta rating rows for an MP route ID; not ticks, sends, visits, or unique climbers |
| rating_valid_count | Historical rows with a rating in the 0–4 range |
| historical_average_user_rating | Mean of valid historical ratings, separate from Kaggle average stars |
| rating_snapshot | Historical archive label; exact observation dates are unverified |
| tick_count | Actual total recorded tick count, nullable until a documented snapshot is imported |
| tick_observed_at_utc / tick_source | Observation time and source of the actual tick count |
| popularity_status | Whether an actual tick count was supplied |
| cross_source_duplicate_candidate | Same normalized name and state across sources; a review flag, not a verified match |

The generated `reports/data_dictionary.csv` lists actual output dtypes and missing counts. A missing popularity count stays missing; it is never replaced with zero. The analysis file includes only routes with verified imported `tick_count >= 5` and is initially empty.

## Importing aggregate ticks

Use an authorized export, a dataset with suitable terms, or manually observed route totals. Do not include names, profiles, dates of individual ascents, or comments. Save one observation per Mountain Project ID:

```csv
mp_route_id,tick_count,tick_observed_at_utc,tick_source
```

Populate with real observations and documented provenance, then run:

```bash
python scripts/build.py --ticks /path/to/aggregate_ticks.csv
```

Duplicate IDs, negative/fractional/missing counts, missing sources, and invalid timestamps fail validation. Choose the desired snapshot before importing multiple observations of a route. OpenBeta-only UUID rows cannot be joined to MP tick IDs without a verified crosswalk.
