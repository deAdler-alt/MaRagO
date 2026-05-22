from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.config import load_config


PRIORITY_BANDS = {
    "TERAZ": {"label": "TERAZ", "emoji": "🔴", "sort": 0},
    "6 mies.": {"label": "6 mies.", "emoji": "🟡", "sort": 1},
    "12 mies.": {"label": "12 mies.", "emoji": "🔵", "sort": 2},
    "Daleko": {"label": "Daleko", "emoji": "⚪", "sort": 3},
}


def _months_until(date: pd.Timestamp | None, reference: pd.Timestamp) -> float | None:
    if date is None or pd.isna(date):
        return None
    delta = (date - reference).days / 30.44
    return delta


def assign_priority(
    predictions: pd.DataFrame,
    config: dict | None = None,
    reference_date: datetime | None = None,
) -> pd.DataFrame:
    config = config or load_config()
    reference = pd.Timestamp(reference_date or datetime.utcnow(), tz="UTC")
    scored = predictions.copy()
    bands: list[str] = []
    urgency_scores: list[float] = []
    priority_labels: list[str] = []

    for _, row in scored.iterrows():
        contact_start = row.get("contact_window_start")
        contact_end = row.get("contact_window_end")
        next_ccheck = row.get("next_ccheck_date")
        months_to_contact = _months_until(contact_start, reference)
        months_to_ccheck = _months_until(next_ccheck, reference)

        if contact_start is not None and not pd.isna(contact_start):
            in_window = contact_start <= reference <= contact_end if contact_end is not None else False
        else:
            in_window = False

        if in_window or (months_to_ccheck is not None and months_to_ccheck < 3):
            band = "TERAZ"
            urgency = 100 - min(months_to_ccheck or 0, 100)
        elif months_to_contact is not None and 0 <= months_to_contact <= 9:
            band = "6 mies."
            urgency = 70 - months_to_contact
        elif months_to_contact is not None and 9 < months_to_contact <= 18:
            band = "12 mies."
            urgency = 40 - (months_to_contact - 9)
        else:
            band = "Daleko"
            urgency = max(0, 10 - (months_to_contact or 30))

        meta = PRIORITY_BANDS[band]
        bands.append(band)
        urgency_scores.append(round(urgency, 2))
        priority_labels.append(f"{meta['emoji']} {meta['label']}")

    scored["priority_band"] = bands
    scored["priority_label"] = priority_labels
    scored["urgency_score"] = urgency_scores
    scored = scored.sort_values("urgency_score", ascending=False).reset_index(drop=True)
    return scored


def format_predictions_table(predictions: pd.DataFrame) -> pd.DataFrame:
    display = predictions.copy()
    if "last_check_date" in display.columns:
        display["Ostatnie okno"] = pd.to_datetime(display["last_check_date"]).dt.strftime("%b %Y")
    display = display.rename(
        columns={
            "registration": "Rejestracja",
            "operator": "Operator",
            "age_years": "Wiek",
            "last_gap_days": "Czas trwania",
            "last_check_type": "Typ check",
            "forecast_quarter": "Prognoza C-check",
            "priority_label": "Priorytet",
        }
    )
    columns = [
        "Rejestracja",
        "Operator",
        "Wiek",
        "Ostatnie okno",
        "Czas trwania",
        "Typ check",
        "Prognoza C-check",
        "Priorytet",
        "urgency_score",
        "confidence",
        "icao24",
    ]
    return display[[col for col in columns if col in display.columns]]
