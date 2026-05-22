from datetime import datetime

import pandas as pd

from src.models.predict_ccheck import predict_ccheck
from src.scoring.priority import assign_priority


def test_predict_ccheck_from_march_2024_gap():
    gap_start = pd.Timestamp("2024-03-05", tz="UTC")
    flights = pd.DataFrame(
        [
            {
                "flight_id": "1",
                "icao24": "abc123",
                "registration": "EI-FRK",
                "operator": "Ryanair",
                "built": "2016",
                "dep_airport": "EGKK",
                "arr_airport": "EPWA",
                "dep_time_utc": gap_start - pd.Timedelta(days=10),
                "arr_time_utc": gap_start - pd.Timedelta(days=10, hours=-2),
            },
            {
                "flight_id": "2",
                "icao24": "abc123",
                "registration": "EI-FRK",
                "operator": "Ryanair",
                "built": "2016",
                "dep_airport": "EPWA",
                "arr_airport": "EGKK",
                "dep_time_utc": gap_start + pd.Timedelta(days=29),
                "arr_time_utc": gap_start + pd.Timedelta(days=29, hours=2),
            },
        ]
    )
    gaps = pd.DataFrame(
        [
            {
                "icao24": "abc123",
                "registration": "EI-FRK",
                "operator": "Ryanair",
                "gap_start": gap_start,
                "gap_end": gap_start + pd.Timedelta(days=29),
                "duration_days": 29,
                "check_type": "C-check",
                "confidence": 0.9,
            }
        ]
    )
    predictions = predict_ccheck(flights, gaps, reference_date=datetime(2025, 1, 1))
    forecast = predictions.iloc[0]["forecast_quarter"]
    assert "2026" in forecast or "2027" in forecast

    scored = assign_priority(predictions, reference_date=datetime(2025, 6, 1))
    assert scored.iloc[0]["priority_band"] in {"TERAZ", "6 mies.", "12 mies.", "Daleko"}
