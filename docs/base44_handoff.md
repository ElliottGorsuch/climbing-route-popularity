# Base44 handoff: Climbing Popularity Atlas

Status: the local explorer is implemented and tested. No Base44 deployment has been created. The Base44 integration was discovered and suggested, but connection is unconfirmed. The existing 14er app is a design reference; no changes have been made to it.

## Proposed new application

Name: Climbing Popularity Atlas. Match the reference site's restrained green/gray palette, serif page headings, broad interactive explorer, simple controls, linked table and explanatory side panel. Preserve truthful source/sample labels.

The prototype source is `web/index.html`, `web/styles.css`, `web/app.js`. Generated `web/data/routes.json`, `pca.json` and `model_summary.json` are in the explorer ZIP release asset. Static delivery avoids storing personal user records and avoids a costly per-route Base44 entity import. Serve/fetch the exported aggregates as static assets or from a verified public release URL; keep large datasets out of database row limits. Verify actual Base44 asset storage and client fetch support after connection before choosing the final hosting arrangement. No secret keys or user identifiers are needed.

## Implemented pages

1. **Explore the map:** filters for style, U.S. state, grade family, recorded protection, length and name. Cells can show total sample ticks, per-route averages, route counts, route–climber pairs or leading style by ticks. Cell inspection links to top routes. Filtered CSV export preserves aggregate data.
2. **PCA biplot:** same seven-feature standardized fit as the notebook; fixed plotted route sample; style/tick coloring; selected-route details; feature arrows and explained variance. Popularity is an overlay, not a PCA input.
3. **How it works:** classification, primary/sensitivity metrics, source uncertainty, geography/PCA/regression limitations, privacy and provenance links.

## Data contract

`routes.json` contains `columns`, compact `rows`, and source metadata. Each row is one core rock route, retaining ticks and climbers as separate counts. `analysis_map_valid` excludes implausible coordinate outliers only from mapping. Columns include IDs, route names/links, state, analysis style and grade, area coordinates, counts, length, pitches and protection.

`pca.json` contains the plotted 6,000-route sample with component scores, fit metadata and loadings. All PCA scores remain available in the analytical outputs. Label arrows ×3, scores in component SD units, the two-component variance total, plot clipping and per-feature representation limitations.

Primary ticks count archive rows including ambiguous repeats. The archive commit date is 2019-04-21; observation dates are unknown. No UI label should imply current/full Mountain Project totals. Summed per-route climbers are participation pairs, not distinct people across an area. Coordinates represent climbing areas and cell bins are not equal-area densities.

## Local preview and checks

```bash
python scripts/eda.py
python -m http.server 8765 --directory web --bind 127.0.0.1
```

Open `http://127.0.0.1:8765`. Leaflet is pinned to stable 1.9.4 with CDN integrity hashes. OpenStreetMap tiles retain attribution and require internet. A loading failure is displayed rather than silently substituting fictional data.

Test state/style/grade filtering, all metric layers, Hawaii/Alaska coverage, unknown lengths, empty search results, filter reset, cell inspection/table synchronization, CSV export, PCA color/point details, method navigation and mobile width. Verify a published URL and its actual counts before declaring hosting complete.
