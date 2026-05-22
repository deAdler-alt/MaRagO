from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.config import load_config


def _parse_built_year(built) -> int | None:
    if built is None or (isinstance(built, float) and pd.isna(built)):
        return None
    text = str(built).strip()
    if not text or text.lower() == "nan":
        return None
    try:
        return int(text[:4])
    except ValueError:
        return None


def _age_years(built_year: int | None, reference: datetime) -> float | None:
    if built_year is None:
        return None
    return round(reference.year - built_year + reference.month / 12, 1)


def _to_quarter(date: pd.Timestamp) -> str:
    quarter = (date.month - 1) // 3 + 1
    return f"Q{quarter} {date.year}"


def _flights_per_month(flights: pd.DataFrame, icao24: str) -> float:
    subset = flights[flights["icao24"] == icao24]
    if subset.empty:
        return 0.0
    months = subset["dep_time_utc"].dt.tz_convert("UTC").dt.strftime("%Y-%m").nunique()
    return len(subset) / max(months, 1)


def _pick_maintenance_gap(aircraft_gaps: pd.DataFrame) -> pd.Series | None:
    known = aircraft_gaps[aircraft_gaps["check_type"] != "unknown"]
    if known.empty:
        return None
    c_gaps = known[known["check_type"] == "C-check"]
    if not c_gaps.empty:
        return c_gaps.iloc[-1]
    d_gaps = known[known["check_type"] == "D-check"]
    if not d_gaps.empty:
        return d_gaps.loc[d_gaps["duration_days"].idxmax()]
    return known.loc[known["duration_days"].idxmax()]


def predict_ccheck(
    flights: pd.DataFrame,
    gaps: pd.DataFrame,
    config: dict | None = None,
    reference_date: datetime | None = None,
) -> pd.DataFrame:
    config = config or load_config()
    ccheck_cfg = config["ccheck"]
    reference = pd.Timestamp(reference_date or datetime.utcnow(), tz="UTC")

    aircraft_ids = flights["icao24"].unique()
    predictions: list[dict] = []

    for icao24 in aircraft_ids:
        aircraft_flights = flights[flights["icao24"] == icao24]
        aircraft_gaps = gaps[gaps["icao24"] == icao24].sort_values("gap_start")
        registration = aircraft_flights["registration"].iloc[0]
        operator = aircraft_flights["operator"].iloc[0]
        built_year = _parse_built_year(aircraft_flights["built"].iloc[0] if "built" in aircraft_flights.columns else None)
        age = _age_years(built_year, reference.to_pydatetime())

        known_gaps = aircraft_gaps[aircraft_gaps["check_type"] != "unknown"]
        c_gaps = aircraft_gaps[aircraft_gaps["check_type"] == "C-check"]
        last_maint = _pick_maintenance_gap(aircraft_gaps)
        last_c = c_gaps.iloc[-1] if not c_gaps.empty else None

        if last_maint is not None:
            last_check_date = pd.Timestamp(last_maint["gap_start"])
            last_check_type = last_maint["check_type"]
            last_gap_days = int(last_maint["duration_days"])
            confidence = float(last_maint["confidence"])
        else:
            last_check_date = None
            last_check_type = "unknown"
            last_gap_days = None
            confidence = 0.35

        interval_months = ccheck_cfg["base_interval_months"]
        if age is not None and age >= ccheck_cfg["old_aircraft_years"]:
            interval_months *= 1 - ccheck_cfg["old_aircraft_interval_reduction"]

        utilization = _flights_per_month(flights, icao24)
        if utilization >= ccheck_cfg["high_utilization_threshold"]:
            interval_months += ccheck_cfg["high_utilization_adjustment_months"]
        elif utilization <= ccheck_cfg["low_utilization_threshold"]:
            interval_months += ccheck_cfg["low_utilization_adjustment_months"]

        forecast_anchor = last_c if last_c is not None else last_maint
        if forecast_anchor is not None and last_c is None and last_check_type == "D-check":
            interval_months = max(interval_months, 96)

        if forecast_anchor is not None:
            anchor_date = pd.Timestamp(forecast_anchor["gap_start"])
            next_ccheck = anchor_date + pd.DateOffset(months=int(interval_months))
            contact_start = next_ccheck - pd.DateOffset(months=ccheck_cfg["contact_window_start_months"])
            contact_end = next_ccheck - pd.DateOffset(months=ccheck_cfg["contact_window_end_months"])
            forecast_quarter = _to_quarter(next_ccheck)
            suggested_contact = contact_start
            if last_c is None and last_check_type in {"A-check", "B-check"}:
                confidence = min(confidence, 0.45)
        else:
            next_ccheck = None
            contact_start = None
            contact_end = None
            forecast_quarter = "unknown"
            suggested_contact = None
            confidence = min(confidence, 0.3)

        predictions.append(
            {
                "icao24": icao24,
                "registration": registration,
                "operator": operator,
                "age_years": age,
                "last_check_date": last_check_date,
                "last_check_type": last_check_type,
                "last_gap_days": last_gap_days,
                "flights_per_month": round(utilization, 1),
                "forecast_quarter": forecast_quarter,
                "next_ccheck_date": next_ccheck,
                "contact_window_start": contact_start,
                "contact_window_end": contact_end,
                "suggested_contact_date": suggested_contact,
                "confidence": confidence,
            }
        )

    return pd.DataFrame(predictions)
