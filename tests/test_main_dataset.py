import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_main import aggregate_sample, inner_join_sample


def test_tick_aggregation_keeps_repeat_records_but_counts_distinct_users():
    data = pd.DataFrame({'UserID': ['10', '10', '20', '30'], 'RouteID': ['100', '100', '100', '200']})
    result = aggregate_sample(data).set_index('mp_route_id')
    assert result.loc['100', 'sampled_tick_record_count'] == 3
    assert result.loc['100', 'sampled_climber_count'] == 2
    assert result.loc['200', 'sampled_climber_count'] == 1
    assert 'UserID' not in result


def test_inner_join_drops_tickless_routes_and_unmatched_tick_ids():
    features = pd.DataFrame({'mp_route_id': ['100', '300'], 'grade': ['5.9 PG13', 'V3']})
    sample = aggregate_sample(pd.DataFrame({'UserID': ['10', '20'], 'RouteID': ['100', '200']}))
    result = inner_join_sample(features, sample)
    assert result.mp_route_id.tolist() == ['100']
    assert result.grade.tolist() == ['5.9 PG13']
    assert result.sampled_tick_record_count.tolist() == [1]


@pytest.mark.parametrize('side', ['features', 'sample'])
def test_inner_join_rejects_duplicate_ids(side):
    features = pd.DataFrame({'mp_route_id': ['100']})
    sample = pd.DataFrame({'mp_route_id': ['100'], 'sampled_tick_record_count': [2], 'sampled_climber_count': [1]})
    if side == 'features': features = pd.concat([features, features])
    else: sample = pd.concat([sample, sample])
    with pytest.raises(ValueError, match='unique'):
        inner_join_sample(features, sample)


@pytest.mark.parametrize('user,route', [(None,'100'), ('10',None), ('bad','100')])
def test_aggregation_rejects_missing_or_invalid_ids(user, route):
    with pytest.raises(ValueError, match='Invalid'):
        aggregate_sample(pd.DataFrame({'UserID': [user], 'RouteID': [route]}))
