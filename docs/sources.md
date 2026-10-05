# Sources and collection decisions

## Kaggle route features

- Publisher: Matthias Galban.
- Dataset: https://www.kaggle.com/datasets/matthiasgalban/mountain-project-rock-climbing-routes
- Version: 2. Downloaded October 5, 2026. Kaggle metadata lists a May 7, 2026 update and CC0 Public Domain licensing. The update date does not establish when routes were observed.
- File: `MP_routes.csv` inside the archive, 151,037 records, 11 source columns including the exported row index.
- Scope gap: no standalone `Boulder` type in this file, though mixed types include bouldering. Thus its description should not be interpreted as complete coverage of all U.S. climbing.
- The source `Length` column is treated as feet, following Mountain Project's U.S. convention. The CSV itself contains no unit annotation; confirm this assumption before making length-based claims. OpenBeta export lengths are explicitly labeled meters.

## OpenBeta route supplement

- Publisher: OpenBeta.
- Exporter: https://github.com/OpenBeta/parquet-exporter
- Pinned release: https://github.com/OpenBeta/parquet-exporter/releases/tag/v2026-10-04
- Publisher states data is CC0: https://github.com/OpenBeta/parquet-exporter#license
- Only USA records with bouldering flagged true are appended. Descriptions and first-ascent text are omitted from processed outputs.
- The pinned export repeats 945 U.S. bouldering rows exactly. Those duplicates are removed across all original fields before normalization. Conflicting records sharing a UUID would fail the build for review.
- The export contains OpenBeta UUIDs, not Mountain Project IDs. Exact name plus state overlaps are flagged; no automatic fuzzy crosswalk is inferred. Coordinates often represent shared areas, so they do not prove identity.

## Historical rating records

- Publisher: OpenBeta.
- Repository: https://github.com/OpenBeta/climbing-data/tree/main/ratings
- Pinned commit: `51a0461a44078148135561c651d25a9203330609`.
- Repository declares CC0. All 41 available state archives are downloaded; some U.S. states are absent.
- Historical archive collection dates are unverified. A commit/download date is not an observation date.
- Raw files include user identifiers. Build reads only route IDs and ratings and publishes aggregate route counts and means. Raw archives are ignored by Git and excluded from release packages.
- Every record contributes to the record count; this is not a unique-person count and does not remove repeated users. There is no evidence these records represent completed ascents or ticks.

## Mountain Project ticks

No Mountain Project scraping is performed. On October 5, 2026, Mountain Project linked to https://www.adventureprojects.net/ap-terms, whose section 8(g) prohibits automated collection. https://www.mountainproject.com/robots.txt specifies a 60-second crawl delay, which does not grant collection or redistribution rights. No suitable aggregate tick snapshot has yet been acquired.

The pipeline accepts a documented tick CSV later. To pursue current tick counts, options include asking Mountain Project for an authorized academic export, locating a published dataset containing actual totals, or recording a small manual pilot. These are alternatives to investigate, not sources already available. No request to the publisher has been sent.

## Reproducibility and interpretation

`data/raw/manifest.json` records source URLs, file sizes, download times, and SHA-256 checksums. Source metadata is retained locally. Download scripts pin versions and cache files. Never equate logged participation with total real-world traffic: platform usage, reporting habits, route age, and geography may influence counts.

The proposal uses one Kaggle source plus additional sources, as planned. Both Kaggle route features and historical ratings ultimately originate from Mountain Project; explain this shared origin when describing the secondary dataset. The class may need to confirm that published archive aggregation meets its intended access-method requirements if fresh scraping is replaced.
