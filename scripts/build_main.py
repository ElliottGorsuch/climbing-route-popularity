"""Build the project's main route dataset with a strict inner join to sampled ticks."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from build import ROOT, TYPE_FLAGS, add_ratings, aggregate_votes, kaggle_routes
from evaluate_tick_archive import STATES, COMMIT


def aggregate_sample(ticks):
    required = {'UserID', 'RouteID'}
    if not required.issubset(ticks):
        raise ValueError('Tick records require UserID and RouteID')
    ticks = ticks[['UserID', 'RouteID']].copy()
    for column in ['UserID', 'RouteID']:
        ticks[column] = ticks[column].astype('string')
        if not ticks[column].str.fullmatch(r'\d+', na=False).all():
            raise ValueError(f'Invalid {column} in tick archive')
    return ticks.groupby('RouteID').agg(
        sampled_tick_record_count=('UserID', 'size'),
        sampled_climber_count=('UserID', 'nunique'),
    ).reset_index().rename(columns={'RouteID': 'mp_route_id'})


def inner_join_sample(features, sample):
    """Never retain an unobserved route or allow an ID to multiply rows."""
    if features.mp_route_id.isna().any() or sample.mp_route_id.isna().any():
        raise ValueError('Route IDs must be present on both sides of the join')
    if features.mp_route_id.duplicated().any() or sample.mp_route_id.duplicated().any():
        raise ValueError('Route IDs must be unique on both sides of the join')
    for col in ['sampled_tick_record_count', 'sampled_climber_count']:
        values = pd.to_numeric(sample[col], errors='coerce')
        if values.isna().any() or (values < 1).any() or (values % 1 != 0).any():
            raise ValueError('Sample counts must be positive integers')
    if (sample.sampled_climber_count > sample.sampled_tick_record_count).any():
        raise ValueError('Sampled climbers cannot exceed tick records')
    return features.merge(sample, on='mp_route_id', how='inner', validate='one_to_one')


def load_historical_metadata(path):
    with ZipFile(path) as z:
        with z.open('master_routes.json') as f:
            data = pd.DataFrame(json.load(f)['routes'])
    data['mp_route_id'] = data.id.astype('string')
    if data.mp_route_id.duplicated().any():
        raise ValueError('Duplicate IDs in historical route metadata')
    data['state'] = data.location.map(lambda x: x[0] if isinstance(x, list) and x else None)
    return data.loc[data.state.isin(STATES)].copy()


def bouldering_features(metadata, primary_ids):
    data = metadata.loc[metadata.type.str.contains('Boulder', na=False) & ~metadata.mp_route_id.isin(primary_ids)].copy()
    result = pd.DataFrame({
        'mp_route_id': data.mp_route_id, 'route_key': 'mp:' + data.mp_route_id,
        'route_name': data['name'], 'route_url': data.url,
        'route_type': data.type, 'rating_raw': data.rating,
        'state': data.state, 'country': 'USA',
        'location': data.location.map(lambda x: ' > '.join(reversed(x))),
        'area_latitude': data.latitude, 'area_longitude': data.longitude,
        'pitches': pd.to_numeric(data.pitches, errors='coerce').where(lambda x: x > 0),
    })
    result['route_source'] = 'gt_2019_archive_bouldering'
    types = result.route_type.str.split(', ').map(set)
    for label, column in TYPE_FLAGS.items():
        result[column] = types.map(lambda x: label in x).astype('boolean')
    return add_ratings(result)


def build_main(state=None):
    raw = ROOT / 'data/raw/research_candidates'
    with ZipFile(raw / 'gt_2019_user_routes_full.csv.zip') as z:
        with z.open('user_routes_full.csv') as f:
            # Personal IDs are used transiently for distinct-user aggregation only.
            ticks = pd.read_csv(f, usecols=['UserID', 'RouteID'], dtype='string')
    sample = aggregate_sample(ticks)
    metadata = load_historical_metadata(raw / 'gt_2019_master_routes.json.zip')
    primary = kaggle_routes(ROOT / 'data/raw/kaggle/routes-v2.zip').drop(columns=['openbeta_route_id'])
    supplement = bouldering_features(metadata, primary.mp_route_id)
    features = pd.concat([primary, supplement], ignore_index=True)
    if state:
        features = features.loc[features.state.str.casefold() == state.casefold()].copy()
        if features.empty:
            raise ValueError(f'No routes for state {state!r}')
    main = inner_join_sample(features, sample)
    historical = metadata[['mp_route_id', 'name', 'rating', 'type', 'stars', 'starVotes']].rename(columns={
        'name': 'archived_route_name', 'rating': 'archived_rating_raw', 'type': 'archived_route_type',
        'stars': 'archived_average_stars_raw', 'starVotes': 'archived_star_votes',
    })
    historical['archived_average_stars_raw'] = pd.to_numeric(historical.archived_average_stars_raw, errors='coerce').where(lambda x: x.between(0, 5))
    historical['archived_star_votes'] = pd.to_numeric(historical.archived_star_votes, errors='coerce').where(lambda x: x >= 0)
    main = main.merge(historical, on='mp_route_id', how='left', validate='one_to_one')
    votes = aggregate_votes(ROOT / 'data/raw/openbeta/ratings')
    main = main.merge(votes, on='mp_route_id', how='left', validate='one_to_one')
    for col in ['sampled_tick_record_count', 'sampled_climber_count', 'rating_record_count', 'rating_valid_count', 'archived_star_votes', 'pitches']:
        main[col] = main[col].astype('Int64')
    for col, lo, hi in [('area_latitude', -90, 90), ('area_longitude', -180, 180)]:
        main[col] = pd.to_numeric(main[col], errors='coerce').where(lambda x: x.between(lo, hi))
    main['sampled_tick_archive_date'] = '2019-04-21'
    main['sampled_tick_source'] = 'https://github.com/jdemeo/Rock_Climbing_Recommendation_System'
    main['sampled_tick_source_commit'] = COMMIT
    main['popularity_measure'] = 'sampled_climber_count'
    main['has_at_least_5_sampled_climbers'] = main.sampled_climber_count.ge(5)
    main = main.sort_values('mp_route_id').reset_index(drop=True)
    if main.empty or not main.route_key.is_unique or main.sampled_tick_record_count.isna().any():
        raise ValueError('Main dataset must contain unique routes with sample tick observations')
    if any(c in main for c in ['UserID', 'author', 'comment', 'users', 'tick_count']):
        raise ValueError('Personal records and misleading total tick fields must not reach the main dataset')
    output = ROOT / 'data/processed'
    output.mkdir(parents=True, exist_ok=True)
    main.to_parquet(output / 'climbing_routes_main.parquet', index=False)
    main.to_csv(output / 'climbing_routes_main.csv', index=False)
    main.loc[main.has_at_least_5_sampled_climbers].to_parquet(output / 'climbing_routes_main_ge5_climbers.parquet', index=False)
    sample.to_parquet(output / 'sampled_tick_counts.parquet', index=False)
    joined_ids = set(main.mp_route_id)
    coverage = features.assign(retained=features.mp_route_id.isin(joined_ids)).groupby(['state', 'route_source']).agg(
        input_routes=('route_key', 'size'), retained_routes=('retained', 'sum'),
    ).reset_index()
    coverage['dropped_routes'] = coverage.input_routes - coverage.retained_routes
    coverage['retained_percent'] = (100 * coverage.retained_routes / coverage.input_routes).round(2)
    coverage.to_csv(ROOT / 'reports/main_join_coverage.csv', index=False)
    dictionary = pd.DataFrame({'column': main.columns, 'dtype': [str(x) for x in main.dtypes], 'missing_records': main.isna().sum().values})
    dictionary.to_csv(ROOT / 'reports/main_data_dictionary.csv', index=False)
    metrics = {
        'scope': state or 'USA', 'join': 'inner on mp_route_id; one_to_one validation',
        'input_route_features': len(features), 'tick_archive_routes': len(sample),
        'main_routes': len(main), 'dropped_feature_routes_without_sample_ticks': len(features) - len(main),
        'bouldering_routes': int(main.is_boulder.sum()), 'kaggle_routes_retained': int((main.route_source == 'kaggle_v2').sum()),
        'historical_bouldering_routes_retained': int((main.route_source == 'gt_2019_archive_bouldering').sum()),
        'routes_ge5_sampled_climbers': int(main.has_at_least_5_sampled_climbers.sum()),
        'routes_with_historical_rating_counts': int(main.rating_record_count.notna().sum()),
        'tick_records_on_retained_routes': int(main.sampled_tick_record_count.sum()),
        'unique_route_ids': bool(main.mp_route_id.is_unique),
        'columns': len(main.columns), 'state_counts': main.state.value_counts().to_dict(),
        'missing_by_column': main.isna().sum().to_dict(),
        'protection_counts': main.protection_rating.fillna('not_recorded').value_counts().to_dict(),
        'cautions': ['Sample counts are not platform-wide totals.', 'The source archive caps histories at 1000 ticks per user and contains ambiguous repeated rows.', 'Archived route metadata and newer Kaggle features have different dates.', 'Historical star scores are preserved separately; no scale conversion is assumed.', 'The source archive declares no data license; code MIT licensing does not apply to its data.'],
    }
    (ROOT / 'reports/main_data_quality.json').write_text(json.dumps(metrics, indent=2) + '\n')
    print(json.dumps({k: v for k, v in metrics.items() if k not in ['state_counts', 'missing_by_column', 'cautions']}, indent=2))
    return main


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', help='Optional full state name; overwrites main outputs with this scope')
    build_main(parser.parse_args().state)
