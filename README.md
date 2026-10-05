# U.S. climbing route popularity

SIADS 593 project by John Gorsuch and Victor Lee exploring **what characteristics popular rock climbing routes have in common**.

The first dataset combines Kaggle route features, a U.S. OpenBeta bouldering supplement, and historical counts of OpenBeta rating records joined by Mountain Project route ID. Actual tick counts are still missing. Rating counts are a separate engagement measure and must not be described as ticks.

Initial snapshot: **227,812 source route records**, including **77,282 bouldering records** and **97,137 routes with historical rating counts**. The OpenBeta supplement contributes 76,775 records after removing 945 exact duplicates. There are 10,799 records flagged for possible cross-source overlap; these are review candidates, not confirmed duplicates. Colorado has 32,746 combined records and Michigan has 1,168.

## Start here

Python 3.12 or later is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download.py
python scripts/build.py
python -m pytest -q
```

Downloads come from Kaggle and publisher-provided GitHub files; the pipeline does not crawl Mountain Project. Kaggle version 2, the ratings commit, and the OpenBeta export release are pinned. Files are cached with checksums. Use `python scripts/download.py --refresh` to retrieve those pinned versions again.

The processed outputs are:

- `data/processed/routes_combined.parquet`: typed master dataset; recommended for analysis.
- `data/processed/routes_combined.csv`: readable equivalent; CSV readers must restore nullable types and string IDs.
- `data/processed/historical_rating_counts.parquet`: aggregate rating counts by MP ID.
- `data/processed/routes_analysis_ticks_ge5.parquet`: analysis subset, empty until actual ticks are imported.
- `reports/data_quality.json`: coverage, missingness, protection ratings, and caveats.

See [field definitions](docs/data_dictionary.md), [source provenance](docs/sources.md), and [the initial exploration notebook](notebooks/01_explore.ipynb).

To open the notebook locally, optionally install JupyterLab with `python -m pip install jupyterlab` and run `python -m jupyterlab` from the project folder. The notebook is also readable on GitHub.

## Optional state focus

```bash
python scripts/build.py --state Colorado
python scripts/build.py --state Michigan
```

These commands overwrite the processed files and quality report with the selected state. Run without `--state` to restore all U.S. source records. The full sources remain cached.

## Add actual popularity totals

Supply an aggregate CSV with `mp_route_id,tick_count,tick_observed_at_utc,tick_source`:

```bash
python scripts/build.py --ticks /path/to/aggregate_ticks.csv
```

Missing counts remain missing, confirmed zeros stay zero, and ambiguous IDs cannot multiply records. [The import contract](docs/data_dictionary.md#importing-aggregate-ticks) explains validation.

## Collaboration and data storage

Code, documentation, tests, and aggregate quality reports live in Git. Raw archives and processed datasets are ignored. Release assets contain processed snapshots only; they do not contain raw user rating records. Victor can clone the repo and reproduce the dataset or download the published snapshot from Releases. Future changes can use branches and pull requests.

Keep the master rows regardless of tick threshold. Apply `>=5` only for the planned analysis and report how that threshold changes the sample. Review cross-source duplicate candidates before computing counts of distinct physical routes. YDS and V grades are different scales; do not convert their strings to decimal numbers or compare them as one numeric scale.

The code is MIT licensed. Source data uses its publishers' declared licenses; see [sources](docs/sources.md). Snapshot availability, reporting bias, and incomplete coverage limit popularity conclusions.
