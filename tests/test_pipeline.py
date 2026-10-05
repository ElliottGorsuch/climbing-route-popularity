import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build import parse_rating, join_ticks


@pytest.mark.parametrize('raw,grade,system,risk', [
    ('5.9 PG13', '5.9', 'YDS', 'PG-13'),
    ('5.9 PG-13', '5.9', 'YDS', 'PG-13'),
    ('5.10b/c R', '5.10b/c', 'YDS', 'R'),
    ('5.12a X', '5.12a', 'YDS', 'X'),
    ('V0-1 PG13', 'V0-1', 'V', 'PG-13'),
    ('V-easy', 'V-easy', 'V', None),
    ('5.9+ V2 R', '5.9+', 'YDS', 'R'),
    ('WI3', 'WI3', 'other', None),
])
def test_rating_parsing(raw, grade, system, risk):
    result = parse_rating(raw)
    assert (result['grade'], result['grade_system'], result['protection_rating']) == (grade, system, risk)


def test_missing_rating_flags_remain_unknown():
    assert parse_rating(None)['is_pg13'] is None
    assert parse_rating('')['grade'] is None


def test_missing_ticks_are_not_zero():
    routes = pd.DataFrame({'mp_route_id': pd.Series(['123', '456', None], dtype='string')})
    result = join_ticks(routes, None)
    assert result.tick_count.isna().all()


def test_tick_join_preserves_routes_and_confirmed_zero(tmp_path):
    routes = pd.DataFrame({'mp_route_id': pd.Series(['123', '456', None], dtype='string')})
    path = tmp_path / 'ticks.csv'
    pd.DataFrame({'mp_route_id': ['123'], 'tick_count': [0], 'tick_observed_at_utc': ['2026-10-05T12:00:00Z'], 'tick_source': ['test fixture only']}).to_csv(path, index=False)
    result = join_ticks(routes, path)
    assert len(result) == 3
    assert result.tick_count.iloc[0] == 0
    assert result.tick_count.iloc[1:].isna().all()


@pytest.mark.parametrize('count', [-1, 1.5, None, 'unknown'])
def test_invalid_ticks_rejected(tmp_path, count):
    path = tmp_path / 'ticks.csv'
    pd.DataFrame({'mp_route_id': ['123'], 'tick_count': [count], 'tick_observed_at_utc': ['2026-10-05T12:00:00Z'], 'tick_source': ['test fixture only']}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        join_ticks(pd.DataFrame({'mp_route_id': ['123']}), path)


def test_duplicate_tick_ids_rejected(tmp_path):
    path = tmp_path / 'ticks.csv'
    pd.DataFrame({'mp_route_id': ['123', '123'], 'tick_count': [5, 6], 'tick_observed_at_utc': ['2026-10-05T12:00:00Z'] * 2, 'tick_source': ['test fixture only'] * 2}).to_csv(path, index=False)
    with pytest.raises(ValueError, match='unique'):
        join_ticks(pd.DataFrame({'mp_route_id': ['123']}), path)
