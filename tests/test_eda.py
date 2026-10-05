"""Critical analysis decisions: mixed types, grade ambiguity, and cohort integrity."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from eda import classify_route, grade_family, prepare_routes


def test_trad_precedence_and_nonrock_exclusions():
    assert classify_route({"is_sport": True, "is_trad": True}) == "Trad"
    assert classify_route({"is_boulder": True, "is_trad": True}) == "Trad"
    assert classify_route({"is_trad": True, "is_ice": True}) == "Excluded: ice/aid/snow"
    assert (
        classify_route({"is_sport": True, "is_aid": True}) == "Excluded: ice/aid/snow"
    )
    assert (
        classify_route({"is_sport": True, "is_snow": True}) == "Excluded: ice/aid/snow"
    )


def test_grade_scales_and_ranges_remain_distinct():
    assert grade_family("5.10b/c PG-13") == "5.10"
    assert grade_family("5.1") == "5.1"
    assert grade_family("5.10 V2", boulder=True) == "V2"
    assert grade_family("V0-1", boulder=True) == "V0"
    assert grade_family("V-easy", boulder=True) == "V-easy"
    assert grade_family("WI3") is None


def test_historical_resolution_never_silently_changes_source_grade():
    data = pd.DataFrame(
        {
            "mp_route_id": ["1", "2", "3"],
            "state": ["Colorado"] * 3,
            "route_source": ["kaggle_v2"] * 3,
            "grade": ["5.1"] * 3,
            "rating_raw": ["5.1"] * 3,
            "archived_rating_raw": ["5.10a", "5.1", "5.9"],
            "is_sport": [True] * 3,
            "sampled_tick_record_count": [1, 3, 6],
            "sampled_climber_count": [1, 2, 5],
            "length_feet": [60, 70, None],
            "pitches": [1, 1, 1],
            "protection_rating": [None, "R", None],
            "is_pg13": [False] * 3,
            "is_r": [False, True, False],
            "is_x": [False] * 3,
            "area_latitude": [40.0] * 3,
            "area_longitude": [-105.0] * 3,
        }
    )
    result = prepare_routes(data)
    assert len(result) == 3  # No five-tick or complete-case filter in the cohort.
    assert result.analysis_grade_family.iloc[0] == "5.10"
    assert result.analysis_grade_family.iloc[1] == "5.1"
    assert pd.isna(result.analysis_grade_family.iloc[2])
    assert result.rating_raw.eq("5.1").all()
    assert result.protection_group.iloc[0] == "Not recorded"
    assert result.ticks.tolist() == [1, 3, 6]
