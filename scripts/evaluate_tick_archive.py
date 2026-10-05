"""Optional diagnostic evaluation of the historical sample.

Run download.py first. build_main.py creates the canonical analysis dataset;
this diagnostic retains earlier candidate outputs for comparison only.
Original archive data licensing is unspecified.
"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from build import ROOT, TYPE_FLAGS, add_ratings

STATES = set('Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|District of Columbia'.split('|'))
COMMIT = 'd1d75bbeb143d4fc863dc1d36173b15b9c0f6ba3'


def evaluate():
    raw = ROOT / 'data/raw/research_candidates'
    output = ROOT / 'data/processed/research_candidates'
    output.mkdir(parents=True, exist_ok=True)
    ticks_path = raw / 'gt_2019_user_routes_full.csv.zip'
    metadata_path = raw / 'gt_2019_master_routes.json.zip'
    with ZipFile(ticks_path) as z:
        with z.open('user_routes_full.csv') as f:
            ticks = pd.read_csv(f, dtype={'UserID': 'string', 'RouteID': 'string'})
    if ticks.UserID.isna().any() or not ticks.RouteID.str.fullmatch(r'\d+', na=False).all():
        raise ValueError('Invalid user/route identifiers in candidate archive')
    counts = ticks.groupby('RouteID').agg(
        sampled_tick_record_count=('UserID', 'size'),
        sampled_climber_count=('UserID', 'nunique'),
    ).reset_index().rename(columns={'RouteID': 'mp_route_id'})
    counts.to_csv(output / 'gt_2019_sampled_tick_counts.csv', index=False)
    with ZipFile(metadata_path) as z:
        with z.open('master_routes.json') as f:
            metadata = pd.DataFrame(json.load(f)['routes'])
    metadata['mp_route_id'] = metadata.id.astype('string')
    if metadata.mp_route_id.duplicated().any():
        raise ValueError('Archive route IDs are not unique')
    metadata['state'] = metadata.location.map(lambda x: x[0] if isinstance(x, list) and x else None)
    metadata = metadata[metadata.state.isin(STATES)].copy()
    master = pd.read_parquet(ROOT / 'data/processed/routes_combined.parquet')
    primary = master[master.route_source == 'kaggle_v2'].copy()
    boulders = metadata[metadata.type.str.contains('Boulder', na=False) & ~metadata.mp_route_id.isin(primary.mp_route_id)].copy()
    supplement = pd.DataFrame({
        'mp_route_id': boulders.mp_route_id,
        'route_key': 'mp:' + boulders.mp_route_id,
        'route_name': boulders['name'], 'route_url': boulders.url,
        'route_type': boulders.type, 'rating_raw': boulders.rating,
        'state': boulders.state, 'country': 'USA',
        'location': boulders.location.map(lambda x: ' > '.join(reversed(x))),
        'area_latitude': boulders.latitude, 'area_longitude': boulders.longitude,
        'pitches': boulders.pitches,
        # Historical API star scores use a 0-5 scale; don't pool with Kaggle's 0-4.
        'archived_average_stars_0_5': boulders.stars,
        'archived_star_votes': boulders.starVotes,
    })
    supplement['route_source'] = 'gt_2019_archive_bouldering'
    for col in ['pitches', 'area_latitude', 'area_longitude', 'archived_average_stars_0_5', 'archived_star_votes']:
        supplement[col] = pd.to_numeric(supplement[col], errors='coerce')
    supplement['pitches'] = supplement.pitches.where(supplement.pitches > 0)
    supplement['archived_average_stars_0_5'] = supplement.archived_average_stars_0_5.where(supplement.archived_average_stars_0_5.between(0, 5))
    tokens = supplement.route_type.str.split(', ').map(set)
    for label, flag in TYPE_FLAGS.items():
        supplement[flag] = tokens.map(lambda values: label in values).astype('boolean')
    supplement = add_ratings(supplement)
    candidates = pd.concat([primary, supplement], ignore_index=True)
    candidates = candidates.merge(counts, on='mp_route_id', how='left', validate='one_to_one')
    for name in ['sampled_tick_record_count', 'sampled_climber_count']:
        candidates[name] = candidates[name].astype('Int64')
    candidates['sampled_tick_status'] = candidates.sampled_tick_record_count.notna().map({True: 'observed_in_2019_user_sample', False: 'not_observed_in_sample'})
    candidates['sampled_tick_source'] = pd.NA
    candidates.loc[candidates.sampled_tick_record_count.notna(), 'sampled_tick_source'] = f'Georgia Tech CSE 6242 archive {COMMIT}; reuse terms unverified'
    matched = candidates[candidates.sampled_tick_record_count.notna()].copy()
    if not candidates.route_key.is_unique or not matched.tick_count.isna().all():
        raise ValueError('Candidate join must not duplicate IDs or claim actual total tick counts')
    if any('UserID' in col for col in matched):
        raise ValueError('User identifiers must never reach aggregate output')
    matched.to_parquet(output / 'routes_eda_sampled_ticks.parquet', index=False)
    matched.to_csv(output / 'routes_eda_sampled_ticks.csv', index=False)
    candidates.to_parquet(output / 'routes_sampled_tick_candidate_universe.parquet', index=False)
    state = candidates.groupby('state').agg(candidate_routes=('route_key', 'size'), matched_routes=('sampled_tick_record_count', 'count'))
    state['coverage_percent'] = (100 * state.matched_routes / state.candidate_routes).round(2)
    state.to_csv(output / 'eda_candidate_coverage_by_state.csv')
    metrics = {
        'repository': 'https://github.com/jdemeo/Rock_Climbing_Recommendation_System',
        'source_commit': COMMIT, 'archive_committed_at_utc': '2019-04-21T05:58:59Z',
        'observation_cutoff': 'Unknown; archive commit date is not the collection cutoff',
        'reuse_status': 'No declared data license found; local evaluation only',
        'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [ticks_path, metadata_path]},
        'tick_derived_rows': len(ticks), 'sampled_users': int(ticks.UserID.nunique()),
        'archive_route_ids': int(counts.mp_route_id.nunique()),
        'identical_user_route_rating_rows_beyond_first': int(ticks.duplicated().sum()),
        'max_records_per_user': int(ticks.groupby('UserID').size().max()),
        'kaggle_routes_matched': int((matched.route_source == 'kaggle_v2').sum()),
        'kaggle_match_percent': round(100 * (matched.route_source == 'kaggle_v2').sum() / len(primary), 2),
        'candidate_universe_records': len(candidates), 'matched_eda_records': len(matched),
        'historical_bouldering_supplement_matched': int((matched.route_source == 'gt_2019_archive_bouldering').sum()),
        'matched_bouldering_records': int(matched.is_boulder.sum()),
        'matched_routes_ge5_sampled_climbers': int(matched.sampled_climber_count.ge(5).sum()),
        'colorado': state.loc['Colorado'].to_dict(), 'michigan': state.loc['Michigan'].to_dict(),
        'cautions': [
            'Counts represent the archived user sample, not all Mountain Project ticks.',
            'The collector requests at most five 200-record pages per user; histories can be truncated.',
            '235,763 rows repeat the same user, route, and rating; dates/tick IDs are absent, so legitimate repeats and erroneous duplicates cannot be distinguished.',
            'Sampled climber counts collapse repeated user-route pairs but are not complete platform-wide unique climber counts.',
            'User selection is not demonstrated to be random; route inclusion is not representative.',
            'Kaggle features are from a newer dataset than the 2019 archive; grade/name changes can affect interpretation.',
            'OpenBeta UUID supplement is not used in this candidate; historical boulders carry verified MP IDs from the archive.',
            'Historical API stars use a 0-5 scale and are kept separate from Kaggle 0-4 stars.',
            'Candidate outputs are local and excluded from published releases pending reuse clarification.',
        ],
    }
    (ROOT / 'reports/tick_eda_candidate.json').write_text(json.dumps(metrics, indent=2) + '\n')
    print(json.dumps({k: v for k, v in metrics.items() if k not in ['cautions', 'source_sha256']}, indent=2))


if __name__ == '__main__':
    evaluate()
