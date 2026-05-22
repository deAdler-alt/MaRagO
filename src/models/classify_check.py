from __future__ import annotations

import pandas as pd

from src.config import load_config


def _midpoint(min_val: int, max_val: int) -> float:
    return (min_val + max_val) / 2


def _range_score(value: float, min_val: int, max_val: int) -> float:
    midpoint = _midpoint(min_val, max_val)
    half_span = max(1, (max_val - min_val) / 2)
    distance = abs(value - midpoint)
    return max(0.0, 1.0 - distance / half_span)


def classify_gap(
    duration_days: int,
    same_base: bool,
    airport_near_mro: bool,
    config: dict | None = None,
) -> tuple[str, float]:
    config = config or load_config()
    checks = config["checks"]
    a_min, a_max = checks["a_check"]
    b_min, b_max = checks["b_check"]
    c_min, c_max = checks["c_check"]
    d_min = checks["d_check_min"]

    if duration_days >= d_min:
        check_type = "D-check"
        confidence = _range_score(duration_days, d_min, d_min + 30)
    elif c_min <= duration_days <= c_max:
        check_type = "C-check"
        confidence = _range_score(duration_days, c_min, c_max)
        if airport_near_mro:
            confidence = min(1.0, confidence + 0.15)
    elif b_min <= duration_days <= b_max:
        check_type = "B-check"
        confidence = _range_score(duration_days, b_min, b_max)
    elif a_min <= duration_days <= a_max:
        check_type = "A-check"
        confidence = _range_score(duration_days, a_min, a_max)
        if same_base:
            confidence = min(1.0, confidence + 0.1)
    else:
        check_type = "unknown"
        confidence = 0.2

    return check_type, round(confidence, 2)


def is_near_mro(airport: str | None, config: dict | None = None) -> bool:
    if airport is None or (isinstance(airport, float) and pd.isna(airport)):
        return False
    text = str(airport).strip()
    if not text or text.lower() == "nan":
        return False
    config = config or load_config()
    return text.upper() in {hub.upper() for hub in config["mro_hubs"]}


def is_strict_mro(airport: str | None, config: dict | None = None) -> bool:
    if airport is None or (isinstance(airport, float) and pd.isna(airport)):
        return False
    text = str(airport).strip()
    if not text or text.lower() == "nan":
        return False
    config = config or load_config()
    return text.upper() in {hub.upper() for hub in config.get("strict_mro_hubs", [])}


def classify_gaps(gaps_df, config: dict | None = None):
    import pandas as pd

    config = config or load_config()
    if gaps_df.empty:
        return gaps_df

    classified = gaps_df.copy()
    results = classified.apply(
        lambda row: classify_gap(
            int(row["duration_days"]),
            bool(row["same_base"]),
            is_near_mro(row["last_airport"], config) or is_near_mro(row["next_airport"], config),
            config,
        ),
        axis=1,
    )
    classified["check_type"] = results.apply(lambda item: item[0])
    classified["confidence"] = results.apply(lambda item: item[1])

    # Boost confidence dla C-checków przy strict MRO hubach (Warszawa, Sofia, Ostrava…)
    strict_boost_mask = (
        (classified["check_type"] == "C-check")
        & (
            classified["last_airport"].apply(lambda a: is_strict_mro(a, config))
            | classified["next_airport"].apply(lambda a: is_strict_mro(a, config))
        )
    )
    classified.loc[strict_boost_mask, "confidence"] = (
        classified.loc[strict_boost_mask, "confidence"].clip(upper=1.0) + 0.15
    ).clip(upper=1.0)

    return classified
