from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd


def _flight(
    icao24: str,
    registration: str,
    operator: str,
    typecode: str,
    built: str,
    dep: str,
    arr: str,
    dep_time: datetime,
    arr_time: datetime,
) -> dict:
    return {
        "flight_id": f"{icao24}-{int(dep_time.timestamp())}",
        "icao24": icao24,
        "registration": registration,
        "typecode": typecode,
        "operator": operator,
        "built": built,
        "dep_airport": dep,
        "arr_airport": arr,
        "dep_time_utc": pd.Timestamp(dep_time, tz="UTC"),
        "arr_time_utc": pd.Timestamp(arr_time, tz="UTC"),
        "dof": pd.Timestamp(dep_time.date(), tz="UTC"),
        "opdi_month": dep_time.strftime("%Y%m"),
    }


def _generate_with_gap(
    icao24: str,
    registration: str,
    operator: str,
    built: str,
    base: str,
    start: datetime,
    end: datetime,
    gap_start: datetime,
    gap_days: int,
) -> list[dict]:
    flights: list[dict] = []
    dest = "EGKK" if base != "EGKK" else "EIDW"
    cursor = start

    while cursor < gap_start - timedelta(hours=12):
        dep_time = cursor
        arr_time = cursor + timedelta(hours=2)
        flights.append(_flight(icao24, registration, operator, "B738", built, base, dest, dep_time, arr_time))
        cursor += timedelta(days=2)

    last_arr = gap_start
    last_dep = last_arr - timedelta(hours=2)
    flights.append(_flight(icao24, registration, operator, "B738", built, base, dest, last_dep, last_arr))

    next_dep = gap_start + timedelta(days=gap_days)
    cursor = next_dep
    while cursor < end:
        dep_time = cursor
        arr_time = cursor + timedelta(hours=2)
        flights.append(_flight(icao24, registration, operator, "B738", built, dest, base, dep_time, arr_time))
        cursor += timedelta(days=2)

    return flights


DEMO_AIRCRAFT = [
    {"registration": "EI-FRK", "operator": "Ryanair", "built": "2016", "gap_start": datetime(2024, 3, 1), "gap_days": 29, "base": "EIDW"},
    {"registration": "SP-LVB", "operator": "LOT Polish", "built": "2018", "gap_start": datetime(2023, 11, 1), "gap_days": 34, "base": "EPWA"},
    {"registration": "OE-LNT", "operator": "TUI Fly", "built": "2019", "gap_start": datetime(2024, 1, 10), "gap_days": 2, "base": "LOWW"},
    {"registration": "G-JZHF", "operator": "Jet2", "built": "2013", "gap_start": datetime(2022, 9, 1), "gap_days": 26, "base": "EGKK"},
    {"registration": "OO-JAX", "operator": "TUI Fly BE", "built": "2015", "gap_start": datetime(2024, 2, 1), "gap_days": 4, "base": "EBBR"},
    {"registration": "TC-JFF", "operator": "SunExpress", "built": "2010", "gap_start": datetime(2021, 12, 1), "gap_days": 89, "base": "LTFM"},
]


def build_demo_flights(reference: datetime | None = None) -> pd.DataFrame:
    reference = reference or datetime.utcnow()
    start = reference - timedelta(days=365 * 4)
    all_flights: list[dict] = []

    for idx, meta in enumerate(DEMO_AIRCRAFT):
        icao24 = f"demo{idx:04x}"
        all_flights.extend(
            _generate_with_gap(
                icao24=icao24,
                registration=meta["registration"],
                operator=meta["operator"],
                built=meta["built"],
                base=meta["base"],
                start=start,
                end=reference,
                gap_start=meta["gap_start"],
                gap_days=meta["gap_days"],
            )
        )

    return pd.DataFrame(all_flights).sort_values(["icao24", "dep_time_utc"]).reset_index(drop=True)
