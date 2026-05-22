import pandas as pd
import pytest

from src.features.gaps import detect_gaps
from src.models.classify_check import classify_gap


def _sample_flights() -> pd.DataFrame:
    base = pd.Timestamp("2024-01-01", tz="UTC")
    rows = [
        {
            "flight_id": "1",
            "icao24": "abc123",
            "registration": "EI-FRK",
            "operator": "Ryanair",
            "typecode": "B738",
            "built": "2016",
            "dep_airport": "EGKK",
            "arr_airport": "EPWA",
            "dep_time_utc": base,
            "arr_time_utc": base + pd.Timedelta(hours=2),
        },
        {
            "flight_id": "2",
            "icao24": "abc123",
            "registration": "EI-FRK",
            "operator": "Ryanair",
            "typecode": "B738",
            "built": "2016",
            "dep_airport": "EPWA",
            "arr_airport": "EGKK",
            "dep_time_utc": base + pd.Timedelta(days=30),
            "arr_time_utc": base + pd.Timedelta(days=30, hours=2),
        },
    ]
    return pd.DataFrame(rows)


def test_detect_gaps_finds_maintenance_window():
    gaps = detect_gaps(_sample_flights())
    assert len(gaps) == 1
    assert gaps.iloc[0]["duration_days"] == 29


def test_classify_check_types():
    assert classify_gap(2, True, False)[0] == "A-check"
    assert classify_gap(5, False, False)[0] == "B-check"
    assert classify_gap(29, False, True)[0] == "C-check"
    assert classify_gap(89, False, False)[0] == "D-check"
