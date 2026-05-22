from __future__ import annotations

import pandas as pd

from src.config import load_config


def detect_gaps(flights: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    config = config or load_config()
    min_gap_hours = config["checks"]["min_gap_hours"]
    records: list[dict] = []

    for icao24, group in flights.groupby("icao24"):
        group = group.sort_values("dep_time_utc")
        registration = group["registration"].iloc[0]
        operator = group["operator"].iloc[0]
        typecode = group["typecode"].iloc[0] if "typecode" in group.columns else None
        built = group["built"].iloc[0] if "built" in group.columns else None

        dep_times = group["dep_time_utc"].tolist()
        arr_times = group["arr_time_utc"].tolist()
        dep_airports = group["dep_airport"].tolist()
        arr_airports = group["arr_airport"].tolist()

        for idx in range(len(group) - 1):
            gap_start = arr_times[idx]
            gap_end = dep_times[idx + 1]
            gap_hours = (gap_end - gap_start).total_seconds() / 3600
            if gap_hours < min_gap_hours:
                continue
            duration_days = max(1, int(gap_hours // 24))
            last_airport = arr_airports[idx]
            next_airport = dep_airports[idx + 1]
            records.append(
                {
                    "icao24": icao24,
                    "registration": registration,
                    "operator": operator,
                    "typecode": typecode,
                    "built": built,
                    "gap_start": gap_start,
                    "gap_end": gap_end,
                    "duration_days": duration_days,
                    "duration_hours": gap_hours,
                    "last_airport": last_airport,
                    "next_airport": next_airport,
                    "same_base": last_airport == next_airport,
                }
            )

    if not records:
        return pd.DataFrame(
            columns=[
                "icao24",
                "registration",
                "operator",
                "typecode",
                "built",
                "gap_start",
                "gap_end",
                "duration_days",
                "duration_hours",
                "last_airport",
                "next_airport",
                "same_base",
            ]
        )
    return pd.DataFrame(records).sort_values(["icao24", "gap_start"]).reset_index(drop=True)
