# U.S. climbing route popularity

SIADS 593 project by John Gorsuch and Victor Lee exploring **what characteristics popular rock climbing routes have in common**.

The main project dataset is **`climbing_routes_main.parquet`**: **97,437 U.S. routes, 46 columns, and 26,743 bouldering routes**. A strict inner join on Mountain Project route ID retains only routes observed in a historical tick sample. The recommended popularity measure is **`sampled_climber_count`**, the number of distinct sampled users who logged a route. It measures participation in the archive, not total Mountain Project popularity.

[Download the main dataset release](https://github.com/ElliottGorsuch/climbing-route-popularity/releases/tag/v0.2.0). Parquet preserves nullable types; the CSV ZIP includes definitions, provenance, and quality reports.

## What is combined

- **70,907 Kaggle routes** with historical tick records: grades, protection designations, climbing types, pitches, lengths, quality scores, and location.
- **26,530 additional U.S. bouldering routes** from the historical archive, with verified MP IDs and tick records. Existing Kaggle IDs take precedence.
- Sample record and distinct-climber counts aggregated from **2,115,034 records for 47,002 users** in an archive committed April 2019.
- Historical rating-record counts for **63,639 routes**, kept separate from ticks.
- Archived route names, grades, types, raw star scores, and star-vote counts where available for comparison with newer features.

The feature table contains 199,083 eligible route IDs before the tick join. The inner join removes 101,646 routes with no tick records in this sample and validates one row per ID. Missing feature values are preserved. The main dataset keeps every matched route; **45,866 routes** have at least five sampled climbers and are exported as an optional subset.

## Reproduce the dataset

Python 3.12 or later is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download.py
python scripts/build_main.py
python -m pytest -q
```

Downloads use published Kaggle and GitHub files. Source versions and commits are pinned; files are cached with SHA-256 checksums. Use `python scripts/download.py --refresh` to retrieve those versions again. No Mountain Project crawler is used.

## Main outputs

| File | Purpose |
| --- | --- |
| `data/processed/climbing_routes_main.parquet` | Main dataset, recommended for analysis |
| `data/processed/climbing_routes_main.csv` | Readable equivalent; import IDs as strings |
| `data/processed/climbing_routes_main_ge5_climbers.parquet` | Optional subset with at least five distinct sampled climbers |
| `data/processed/sampled_tick_counts.parquet` | Aggregate historical sample counts by route ID |
| `reports/main_data_quality.json` | Counts, missingness, source coverage, and cautions |
| `reports/main_join_coverage.csv` | Retained and dropped routes by state and source |
| `reports/main_data_dictionary.csv` | Actual column types and missing counts |

See [field definitions](docs/data_dictionary.md), [sources](docs/sources.md), [join details](docs/main_dataset.md), and [the exploration notebook](notebooks/01_explore.ipynb).

Optionally install JupyterLab with `python -m pip install jupyterlab`, then run `python -m jupyterlab`. The notebook is also readable on GitHub.

## Optional state focus

```bash
python scripts/build_main.py --state Colorado
python scripts/build_main.py --state Michigan
```

These overwrite the main outputs and reports with the selected state. Run without `--state` to restore all U.S. routes.

## Interpretation for EDA

The archive samples users and caps histories at 1,000 tick records per user. It lacks individual tick dates and IDs. Repeated user-route-rating rows cannot reliably be distinguished as repeat climbs or collection duplicates. `sampled_climber_count` collapses repeated user-route pairs; `sampled_tick_record_count` preserves every archive record. Neither is a complete platform-wide count. Ticks can include attempts rather than successful sends.

Routes absent from the sample are excluded; absence does not mean zero activity. Report coverage by location and climbing type before interpreting correlations. Five sampled climbers differs from five ticks. Grades remain text with YDS and V scales identified separately. Missing lengths, protection codes, and scores stay missing. Historical raw star scores stay separate from Kaggle scores without an assumed conversion. Newer features and historical participation may describe different conditions.

## Collaboration and source terms

Code, documentation, tests, and aggregate reports live in Git. Raw archives and generated tables are ignored. The release contains derived route features and aggregate counts, with no user identifiers, individual ascent records, descriptions, photos, or comments.

Code is MIT licensed. Kaggle and OpenBeta declare CC0 for their respective datasets. The tick research repository declares no data license; public availability and this project's code license do not establish a license for its original records. Provenance and that limitation accompany the derived snapshot. No publisher endorsement or complete census is claimed.

The earlier inventory remains available in release v0.1.0. `python scripts/build.py` rebuilds that inventory; **use `build_main.py` for the project's current analysis dataset**.
