"""Normalize route features, aggregate ratings, and join verified tick snapshots."""
from pathlib import Path
import argparse
import json
import re
import uuid
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TYPE_FLAGS = {'Sport': 'is_sport', 'Trad': 'is_trad', 'Boulder': 'is_boulder', 'TR': 'is_top_rope', 'Alpine': 'is_alpine', 'Aid': 'is_aid', 'Ice': 'is_ice', 'Snow': 'is_snow'}


def parse_rating(value):
    """Preserve textual grades; YDS grades are not decimal numbers."""
    if pd.isna(value) or not str(value).strip():
        return {'grade': None, 'grade_system': None, 'grade_vscale': None, 'protection_rating': None, 'is_pg13': None, 'is_r': None, 'is_x': None}
    raw = str(value).strip()
    protection = re.search(r'(?<!\w)(PG[ -]?13|R|X)(?!\w)', raw, re.I)
    risk = protection.group(1).upper().replace(' ', '').replace('-', '') if protection else None
    if risk == 'PG13':
        risk = 'PG-13'
    yds = re.search(r'(?<!\w)5\.\d+(?:[abcd](?:/[abcd])?)?[+-]?', raw, re.I)
    vscale = re.search(r'(?<!\w)V(?:-easy|B|\d+(?:[-/]\d+)?[+-]?)(?!\w)', raw, re.I)
    grade = yds.group() if yds else vscale.group() if vscale else raw
    return {'grade': grade, 'grade_system': 'YDS' if yds else 'V' if vscale else 'other', 'grade_vscale': vscale.group() if vscale else None, 'protection_rating': risk, 'is_pg13': risk == 'PG-13', 'is_r': risk == 'R', 'is_x': risk == 'X'}


def add_ratings(frame):
    parsed = pd.DataFrame([parse_rating(value) for value in frame.rating_raw], index=frame.index)
    for col in parsed:
        frame[col] = parsed[col]
    for col in ['is_pg13', 'is_r', 'is_x']:
        frame[col] = frame[col].astype('boolean')
    return frame


def normalized_name(series):
    return series.astype('string').str.normalize('NFKC').str.strip().str.casefold().str.replace(r'\s+', ' ', regex=True)


def kaggle_routes(path):
    raw = pd.read_csv(path)
    renamed = raw.rename(columns={'Route': 'route_name', 'Location': 'location', 'URL': 'route_url', 'Avg.Stars': 'average_stars', 'Route.Type': 'route_type', 'Rating': 'rating_raw', 'Pitches': 'pitches', 'Length': 'length_feet', 'Area.Latitude': 'area_latitude', 'Area.Longitude': 'area_longitude'}).drop(columns=['Unnamed: 0'], errors='ignore')
    renamed['mp_route_id'] = renamed.route_url.str.extract(r'mountainproject\.com/route/(\d+)(?:/|$)', expand=False).astype('string')
    if renamed.mp_route_id.isna().any():
        raise ValueError('Unparseable Mountain Project route URL')
    if renamed.mp_route_id.duplicated().any():
        raise ValueError('Duplicate route IDs require review; refusing a many-to-many join')
    renamed['route_key'] = 'mp:' + renamed.mp_route_id
    renamed['openbeta_route_id'] = pd.NA
    renamed['route_source'] = 'kaggle_v2'
    renamed['state'] = renamed.location.str.split(' > ').str[-1]
    renamed['country'] = 'USA'
    tokens = renamed.route_type.str.split(', ').map(set)
    for label, col in TYPE_FLAGS.items():
        renamed[col] = tokens.map(lambda values: label in values).astype('boolean')
    for col in ['length_feet', 'pitches']:
        renamed[col] = pd.to_numeric(renamed[col], errors='coerce').where(lambda x: x > 0)
    renamed['length_meters'] = renamed.length_feet * 0.3048
    # -1 is a missing-star sentinel, not a valid quality score.
    renamed['average_stars'] = pd.to_numeric(renamed.average_stars, errors='coerce').where(lambda x: x.between(0, 4))
    return add_ratings(renamed)


def openbeta_boulders(path):
    raw = pd.read_parquet(path)
    raw = raw.loc[(raw.country == 'USA') & raw.is_boulder.fillna(False).astype(bool)].copy()
    exact_duplicates = int(raw.duplicated().sum())
    raw = raw.drop_duplicates()
    if raw.climb_id.duplicated().any():
        raise ValueError('Conflicting records for the same OpenBeta UUID require review')
    def identifier(value):
        return str(uuid.UUID(bytes=value)) if isinstance(value, bytes) else str(value)
    result = pd.DataFrame({
        'openbeta_route_id': raw.climb_id.map(identifier), 'route_name': raw.climb_name,
        'state': raw.state_province, 'country': raw.country,
        'area_latitude': raw.latitude, 'area_longitude': raw.longitude,
        'length_meters': pd.to_numeric(raw.length_meters, errors='coerce').where(lambda x: x > 0),
        'rating_raw': raw.grade_vscale.fillna(raw.grade_yds),
    })
    result['route_key'] = 'ob:' + result.openbeta_route_id
    result['route_url'] = 'https://openbeta.io/climbs/' + result.openbeta_route_id
    result['location'] = raw[['country', 'state_province', 'region', 'area', 'crag']].apply(lambda row: ' > '.join(str(x) for x in row if pd.notna(x) and str(x)), axis=1)
    result['route_source'] = 'openbeta_export_v2026-10-04'
    result['mp_route_id'] = pd.NA
    result['length_feet'] = result.length_meters / 0.3048
    for col in TYPE_FLAGS.values():
        result[col] = raw[col].astype('boolean') if col in raw else pd.Series(pd.NA, index=raw.index, dtype='boolean')
    result['route_type'] = result.apply(lambda row: ', '.join(label for label, col in TYPE_FLAGS.items() if pd.notna(row[col]) and row[col]), axis=1)
    result = add_ratings(result)
    safety = raw.safety.astype('string').str.upper().str.replace('PG13', 'PG-13', regex=False)
    specified = safety.isin(['PG-13', 'R', 'X'])
    result.loc[specified, 'protection_rating'] = safety[specified]
    for col, code in [('is_pg13', 'PG-13'), ('is_r', 'R'), ('is_x', 'X')]:
        result.loc[specified, col] = safety[specified] == code
    result['protection_rating'] = result.protection_rating.astype('string')
    # UNSPECIFIED means no protection code recorded, not an assurance of safety.
    result = result.reset_index(drop=True)
    result.attrs['exact_duplicate_source_rows_removed'] = exact_duplicates
    if result.route_key.duplicated().any():
        raise ValueError('Duplicate OpenBeta UUIDs require review')
    return result


def aggregate_votes(directory):
    partials = []
    for path in sorted(directory.glob('*-ratings.csv.zip')):
        # Never load or publish user identifiers; counts measure rating records.
        df = pd.read_csv(path, usecols=['route_id', 'ratings'], dtype={'route_id': 'string'})
        df = df[df.route_id.str.fullmatch(r'\d+', na=False)]
        values = pd.to_numeric(df.ratings, errors='coerce')
        df['valid_rating'] = values.where(values.between(0, 4))
        part = df.groupby('route_id').agg(rating_record_count=('route_id', 'size'), rating_valid_count=('valid_rating', 'count'), rating_sum=('valid_rating', 'sum')).reset_index()
        partials.append(part)
    if not partials:
        raise ValueError('No OpenBeta ratings downloaded; run scripts/download.py')
    result = pd.concat(partials).groupby('route_id', as_index=False)[['rating_record_count', 'rating_valid_count', 'rating_sum']].sum()
    result['historical_average_user_rating'] = result.rating_sum / result.rating_valid_count.where(result.rating_valid_count > 0)
    return result.rename(columns={'route_id': 'mp_route_id'}).drop(columns=['rating_sum'])


def join_ticks(routes, path):
    """One aggregate snapshot per MP route, imported from a documented source."""
    if path is None:
        result = routes.copy()
        result['tick_count'] = pd.Series(pd.NA, index=result.index, dtype='Int64')
        result['tick_observed_at_utc'] = pd.NA
        result['tick_source'] = pd.NA
        return result
    ticks = pd.read_csv(path, dtype={'mp_route_id': 'string'})
    required = ['mp_route_id', 'tick_count', 'tick_observed_at_utc', 'tick_source']
    if not set(required).issubset(ticks):
        raise ValueError('Tick input must contain: ' + ', '.join(required))
    ticks = ticks[required]
    if ticks.mp_route_id.isna().any() or not ticks.mp_route_id.str.fullmatch(r'\d+', na=False).all() or ticks.mp_route_id.duplicated().any():
        raise ValueError('Tick route IDs must be unique, nonmissing numeric strings')
    counts = pd.to_numeric(ticks.tick_count, errors='coerce')
    if counts.isna().any() or (counts < 0).any() or (counts % 1 != 0).any():
        raise ValueError('Tick counts must be nonnegative integers; missing is not zero')
    dates = pd.to_datetime(ticks.tick_observed_at_utc, errors='coerce', utc=True)
    if dates.isna().any() or ticks.tick_source.isna().any() or ticks.tick_source.str.strip().eq('').any():
        raise ValueError('Every tick snapshot needs a valid observation date and source')
    ticks['tick_count'] = counts.astype('Int64')
    ticks['tick_observed_at_utc'] = dates.dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    return routes.merge(ticks, on='mp_route_id', how='left', validate='many_to_one')


def build(ticks=None, state=None):
    primary = kaggle_routes(ROOT / 'data/raw/kaggle/routes-v2.zip')
    boulders = openbeta_boulders(ROOT / 'data/raw/openbeta/openbeta-climbs-v2026-10-04.parquet')
    # Different ID namespaces: keep both records and mark candidates, never fuzzy-merge.
    primary_keys = set(zip(primary.state, normalized_name(primary.route_name)))
    boulders['cross_source_duplicate_candidate'] = [key in primary_keys for key in zip(boulders.state, normalized_name(boulders.route_name))]
    candidate_keys = set(zip(boulders.loc[boulders.cross_source_duplicate_candidate, 'state'], normalized_name(boulders.loc[boulders.cross_source_duplicate_candidate, 'route_name'])))
    primary['cross_source_duplicate_candidate'] = [key in candidate_keys for key in zip(primary.state, normalized_name(primary.route_name))]
    routes = pd.concat([primary, boulders], ignore_index=True)
    votes = aggregate_votes(ROOT / 'data/raw/openbeta/ratings')
    result = routes.merge(votes, on='mp_route_id', how='left', validate='many_to_one')
    result['rating_record_count'] = result.rating_record_count.astype('Int64')
    result['rating_valid_count'] = result.rating_valid_count.astype('Int64')
    result['rating_snapshot'] = pd.NA
    result.loc[result.rating_record_count.notna(), 'rating_snapshot'] = 'OpenBeta historical archive; exact collection date unverified'
    result = join_ticks(result, ticks)
    result['popularity_status'] = result.tick_count.notna().map({True: 'tick_count_available', False: 'tick_count_missing'})
    for coord, low, high in [('area_latitude', -90, 90), ('area_longitude', -180, 180)]:
        result[coord] = pd.to_numeric(result[coord], errors='coerce').where(lambda x: x.between(low, high))
    if state:
        selected = result.state.str.casefold() == state.casefold()
        if not selected.any():
            raise ValueError(f'No routes for state {state!r}; use the full state name')
        result = result.loc[selected].copy()
    if result.route_key.duplicated().any():
        raise ValueError('Combined route keys must remain unique')
    output = ROOT / 'data/processed'
    output.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output / 'routes_combined.parquet', index=False)
    result.to_csv(output / 'routes_combined.csv', index=False)
    subset = result.loc[result.tick_count.ge(5).fillna(False)]
    subset.to_parquet(output / 'routes_analysis_ticks_ge5.parquet', index=False)
    votes.to_parquet(output / 'historical_rating_counts.parquet', index=False)
    summary = {
        'scope': state or 'USA', 'kaggle_routes': len(primary), 'openbeta_bouldering_routes': len(boulders),
        'openbeta_exact_duplicates_removed': boulders.attrs['exact_duplicate_source_rows_removed'],
        'combined_records': len(result), 'bouldering_records': int(result.is_boulder.fillna(False).sum()),
        'rating_archive_routes': len(votes), 'rating_archive_records': int(votes.rating_record_count.sum()),
        'routes_with_rating_records': int(result.rating_record_count.notna().sum()),
        'routes_with_tick_counts': int(result.tick_count.notna().sum()), 'analysis_ticks_ge5_records': len(subset),
        'duplicate_candidate_records': int(result.cross_source_duplicate_candidate.sum()),
        'source_counts': result.route_source.value_counts().to_dict(), 'state_counts': result.state.value_counts().to_dict(),
        'missing_by_column': result.isna().sum().to_dict(),
        'protection_counts': result.protection_rating.fillna('not_recorded').value_counts().to_dict(),
        'cautions': ['Rating record counts are not ticks or unique climber counts.', 'Kaggle v2 omits standalone bouldering; OpenBeta supplements this gap.', 'Cross-source duplicate candidates are retained and flagged, not verified duplicates.', 'Rating archive collection date is unverified; export date is not route freshness.', 'Coordinates describe climbing areas and may be shared by many routes.', 'The >=5-tick subset is empty until actual tick snapshots are supplied.'],
    }
    (ROOT / 'reports/data_quality.json').write_text(json.dumps(summary, indent=2) + '\n')
    (ROOT / 'reports/data_dictionary.csv').write_text(pd.DataFrame({'column': result.columns, 'dtype': [str(x) for x in result.dtypes], 'missing_records': result.isna().sum().values}).to_csv(index=False))
    print(json.dumps({k: v for k, v in summary.items() if k not in ['state_counts', 'missing_by_column', 'cautions']}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ticks', type=Path, help='Documented aggregate tick CSV; see docs/data_dictionary.md')
    parser.add_argument('--state', help='Optional full state name, e.g. Colorado or Michigan')
    args = parser.parse_args()
    build(args.ticks, args.state)
