# Sources and collection decisions

## Kaggle route features

- Publisher: Matthias Galban.
- Dataset: https://www.kaggle.com/datasets/matthiasgalban/mountain-project-rock-climbing-routes
- Version: 2. Downloaded October 5, 2026. Kaggle metadata lists a May 7, 2026 update and CC0 Public Domain licensing. The update date does not establish when routes were observed.
- File: `MP_routes.csv` inside the archive, 151,037 records, 11 source columns including the exported row index.
- Scope gap: no standalone `Boulder` type in this file, though mixed types include bouldering. Thus its description should not be interpreted as complete coverage of all U.S. climbing.
- The source `Length` column is treated as feet, following Mountain Project's U.S. convention. The CSV itself contains no unit annotation; confirm this assumption before making length-based claims. OpenBeta export lengths are explicitly labeled meters.

## OpenBeta route supplement (earlier inventory)

- Publisher: OpenBeta.
- Exporter: https://github.com/OpenBeta/parquet-exporter
- Pinned release: https://github.com/OpenBeta/parquet-exporter/releases/tag/v2026-10-04
- Publisher states data is CC0: https://github.com/OpenBeta/parquet-exporter#license
- In the earlier `build.py` inventory, only USA records with bouldering flagged true are appended. The main `build_main.py` dataset uses the historical MP-ID bouldering supplement instead. Descriptions and first-ascent text are omitted from processed outputs.
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

## Historical Mountain Project tick sample

- Publisher: the Georgia Tech CSE 6242 project by Oluwadamini Ajayi, Benjamin Croft, Joshua Demeo, Jeff Sayre, and Jiandao Zhu.
- Repository: https://github.com/jdemeo/Rock_Climbing_Recommendation_System
- Pinned commit: `d1d75bbeb143d4fc863dc1d36173b15b9c0f6ba3`, committed April 21, 2019. This is not a verified observation cutoff.
- Tick archive: `data_manipulation_SVD/data/user_routes/user_routes_full.csv.zip`, with 2,115,034 records, 47,002 users, and 118,018 route IDs.
- Route metadata archive: `master_routes.json.zip`. Its U.S. bouldering records supply MP IDs and features absent from Kaggle. Names, grades, types, coordinates, pitches, and numeric score fields are used; images and descriptions are omitted.
- The source notebook creates records from the former MP API's ticks, including unrated ticks. The collector requests at most five 200-record pages per user.
- There are 235,763 repeated user-route-rating rows beyond the first. Dates/tick IDs are absent, so these cannot be classified reliably as legitimate repeat climbs or errors. Absolute record counts are primary by project choice; distinct sampled users provide a sensitivity comparison.
- Raw user identifiers are used transiently for aggregation and excluded from all derived tables and release assets.
- No data license is declared in this research repository. The derived snapshot records that limitation and does not label these source records CC0 or MIT. Code licensing and source-data licensing are distinct.

## Current Mountain Project access

No Mountain Project scraping is performed. On October 5, 2026, Mountain Project linked to https://www.adventureprojects.net/ap-terms, whose section 8(g) prohibits automated collection. https://www.mountainproject.com/robots.txt specifies a 60-second crawl delay. The acquired historical user sample does not establish current or complete platform-wide tick totals.

The earlier inventory pipeline can accept a documented total-tick CSV later. Current platform-wide counts remain a separate extension. No request to the publisher has been sent.

## Reproducibility and interpretation

`data/raw/manifest.json` records source URLs, file sizes, download times, and SHA-256 checksums. Source metadata is retained locally. Download scripts pin versions and cache files. Never equate logged participation with total real-world traffic: platform usage, reporting habits, route age, and geography may influence counts.

The proposal uses one Kaggle source plus additional sources, as planned. Both Kaggle route features and historical ratings ultimately originate from Mountain Project; explain this shared origin when describing the secondary dataset. The class may need to confirm that published archive aggregation meets its intended access-method requirements if fresh scraping is replaced.
