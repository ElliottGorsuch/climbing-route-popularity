# Base44 deployment: Climbing Popularity Atlas

The atlas is published at **https://climb-data-viz.base44.app**. Editor: https://app.base44.com/apps/6ac426cac49047cf8269638b/editor/preview. App ID: `6ac426cac49047cf8269638b` (Base44 builder name: ClimbInsights). The existing Colorado 14er app served as a design reference.

## Deployment structure

The complete tested `web/` prototype and aggregate JSON exports are served from `public/atlas/` in the Base44 app. `src/pages/AtlasHome.jsx` redirects the React entry page to `/atlas/index.html`, using the supplied `web/base44/AtlasHome.jsx`. `src/App.jsx` imports this page and uses it for the wildcard route, retaining the existing Base44 providers. A direct static entry avoids Base44's iframe restrictions. Data load from the same origin; no per-route database import, runtime ZIP proxy or user histories are needed.

The Base44 checkpoint **Public atlas entry point and passing scaffold checks** saves the deployed integration. The public root resolves to the atlas. Publish changes from the Base44 editor after updating the hosted assets and creating a checkpoint. The GitHub atlas ZIP includes all prototype files and real uncompressed JSON exports. `eda.py` also writes deterministic compressed snapshots in `web/snapshots/` for alternative static delivery.

## Implemented exploration

- Map filters: sport/trad/bouldering, state, separate YDS/V grade families, recorded protection, length and route name.
- Layers: total sample ticks, mean ticks per route, recorded route count, summed route–climber pairs and leading style by ticks.
- Cell inspection, linked top-25 route table and CSV export.
- PCA: the notebook's seven-feature sport/trad fit; style/tick overlays, loadings, variance and clicked-route details. The projection is not recomputed in the browser.
- Methods: sampling, provenance, classification and interpretation limits. Regression results and diagnostics remain in the primary notebook and report.

## Data contract and caveats

`routes.json` has compact `columns` and `rows`: one record per core rock route, 96,735 total and 1,939,376 tick records. Counts of records and sampled climbers remain separate. No five-tick minimum applies. `analysis_map_valid` excludes one gross coordinate outlier from mapping only; unresolved state/coordinate disagreements remain disclosed.

`pca.json` contains 6,000 plotted sample routes, scores, fitted metadata and loadings. 5,968 fall within the displayed ±4.5 component SD window; full scores remain in the analytical package. PC1+PC2 represent 48.0% of feature variance. Popularity is an overlay; protection flags are poorly represented in these components.

Primary ticks are archive rows including ambiguous repeats. The archive commit date is April 21, 2019; observation dates are unknown and histories were capped at 1,000. These are not current/full Mountain Project totals. Summed climbers are route–climber pairs, not distinct people across an area. Coordinates describe climbing areas; 0.2° bins are not equal-area densities. The source archive specifies no data license.

## Verification and local preview

The public page loads the complete counts above. V0 bouldering filters agree with the notebook: 4,435 routes and 36,701 ticks. Local browser checks include map/style layers, cell-linked tables, Hawaii/Alaska, PCA navigation, CSV export and phone-width layout. Base44 lint, typecheck and production build pass; scaffold prop annotations and Vite types were corrected during integration.

```bash
python scripts/eda.py
python -m http.server 8765 --directory web --bind 127.0.0.1
```

Leaflet is pinned to 1.9.4 with integrity hashes; OpenStreetMap retains attribution. Library/tiles require internet. Missing exports or failed library loads display an error rather than substituting invented records.
