from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import load_config
from src.features.gaps import detect_gaps
from src.ingest.demo import build_demo_flights
from src.ingest.opdi import build_flights, save_flights
from src.models.classify_check import classify_gaps
from src.models.predict_ccheck import predict_ccheck
from src.scoring.priority import assign_priority


def load_or_build_flights(config: dict | None = None) -> pd.DataFrame:
    config = config or load_config()
    flights_path = Path(config["paths"]["flights"])
    if config.get("data_mode") == "demo":
        flights = build_demo_flights()
        flights_path.parent.mkdir(parents=True, exist_ok=True)
        flights.to_parquet(flights_path, index=False)
        return flights
    if flights_path.exists():
        return pd.read_parquet(flights_path)
    flights = build_flights(config=config)
    save_flights(flights, config=config)
    return flights


def run_pipeline(config: dict | None = None, rebuild_flights: bool = False) -> dict[str, Path]:
    config = config or load_config()
    processed_dir = Path(config["paths"]["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    flights_path = Path(config["paths"]["flights"])
    if rebuild_flights or not flights_path.exists() or config.get("data_mode") == "demo":
        if config.get("data_mode") == "demo":
            flights = build_demo_flights()
        else:
            flights = build_flights(config=config)
        save_flights(flights, config=config)
    else:
        flights = pd.read_parquet(flights_path)

    gaps = classify_gaps(detect_gaps(flights, config=config), config=config)
    gaps_path = Path(config["paths"]["gaps"])
    gaps.to_parquet(gaps_path, index=False)

    predictions = predict_ccheck(flights, gaps, config=config)
    predictions = assign_priority(predictions, config=config)
    predictions_path = Path(config["paths"]["predictions"])
    predictions.to_parquet(predictions_path, index=False)

    return {
        "flights": flights_path,
        "gaps": gaps_path,
        "predictions": predictions_path,
    }
