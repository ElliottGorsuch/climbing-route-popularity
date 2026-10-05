# Main dataset field definitions

Each row is a U.S. Mountain Project route with at least one record in the historical tick sample. `mp_route_id` is the unique inner-join key. Use `data/processed/climbing_routes_main.parquet`.

| Field | Meaning |
| --- | --- |
| mp_route_id / route_key | Source ID as a string, and unique `mp:<ID>` key |
| route_name / route_url | Route name and source link |
| route_source | `kaggle_v2` or `gt_2019_archive_bouldering` |
| location / state / country | Location hierarchy, U.S. state, and `USA` |
| rating_raw | Original grade text |
| grade / grade_system | Textual grade and YDS, V, or other; grades are not decimal numbers |
| grade_vscale | V-scale grade where present, including mixed YDS/V ratings |
| protection_rating | PG-13, R, X, or missing when no recognized code was recorded |
| is_pg13 / is_r / is_x | Flags for explicit protection codes; unrecorded protection does not establish safety |
| route_type | Source labels; routes can have several types |
| is_sport / is_trad / is_boulder / is_top_rope / is_alpine / is_aid / is_ice / is_snow | Climbing-type flags |
| pitches | Positive pitch count; blanks/nonpositive values become missing |
| length_feet / length_meters | Kaggle length and converted equivalent; missing for historical boulder additions |
| area_latitude / area_longitude | Climbing-area coordinates, not necessarily individual route locations |
| average_stars | Kaggle score, valid range 0-4; missing for historical boulder additions |
| archived_route_name / archived_rating_raw / archived_route_type | Historical feature values for the same MP ID |
| archived_average_stars_raw | Raw historical API score, observed in the 0-5 range; no scale conversion assumed |
| archived_star_votes | Historical number of star votes; not ticks or unique users |
| sampled_tick_record_count | Archive rows for this route, including unresolved repeated records |
| sampled_climber_count | Distinct sampled user IDs per route; recommended participation measure |
| sampled_tick_archive_date | `2019-04-21`, archive commit date, not observation date or collection cutoff |
| sampled_tick_source / sampled_tick_source_commit | Research repository URL and pinned commit |
| popularity_measure | `sampled_climber_count`, recommended EDA measure |
| has_at_least_5_sampled_climbers | Optional threshold flag; the main dataset does not apply this filter |
| rating_record_count / rating_valid_count | OpenBeta historical rating rows and rows with a valid 0-4 score |
| historical_average_user_rating | Mean valid OpenBeta rating, separate from other score fields |

`reports/main_data_dictionary.csv` lists all 46 columns individually with dtypes and missing counts. Parquet preserves nullable integers and strings. CSV readers must restore types. Counts are positive and present in every main row because of the inner join. Missing feature values are not replaced by zero.

The archive does not supply complete MP totals or reliable individual dates, so `tick_count` and `tick_observed_at_utc` are not main-dataset fields. User IDs are transient aggregation inputs and excluded from outputs. The older inventory's total-tick import via `scripts/build.py --ticks` is a separate workflow.
