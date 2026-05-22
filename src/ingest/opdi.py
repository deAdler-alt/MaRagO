from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.config import load_config


def _normalize_icao24(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower()


def load_b737_registry(config: dict | None = None) -> pd.DataFrame:
    config = config or load_config()
    url = config["opensky"]["aircraft_db_url"]
    typecodes = config["opensky"]["typecodes"]
    acdb = pd.read_csv(url, low_memory=False)
    registry = acdb[acdb["typecode"].isin(typecodes)][
        ["icao24", "registration", "typecode", "operator", "built"]
    ].copy()
    registry["icao24"] = _normalize_icao24(registry["icao24"])
    registry = registry.drop_duplicates(subset=["icao24"], keep="first")
    return registry


def _opdi_url(config: dict, month: str) -> str:
    return config["opdi"]["base_url"].format(month=month)


def load_opdi(month: str, config: dict | None = None, use_cache: bool = True) -> pd.DataFrame:
    config = config or load_config()
    cache_dir = Path(config["root"]) / config["opdi"]["cache_dir"]
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"flight_list_{month}.parquet"

    if use_cache and cache_path.exists():
        return pd.read_parquet(cache_path)

    url = _opdi_url(config, month)
    df = pd.read_parquet(url)
    if use_cache:
        df.to_parquet(cache_path, index=False)
    return df


def _normalize_flights(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    column_map = config["column_map"]
    rename = {source: target for target, source in column_map.items() if source in df.columns}
    normalized = df.rename(columns=rename).copy()
    normalized["icao24"] = _normalize_icao24(normalized["icao24"])
    normalized["dep_time_utc"] = pd.to_datetime(normalized["dep_time_utc"], utc=True)
    normalized["arr_time_utc"] = pd.to_datetime(normalized["arr_time_utc"], utc=True)
    if "dof" in normalized.columns:
        normalized["dof"] = pd.to_datetime(normalized["dof"], utc=True)
    normalized["opdi_month"] = normalized["dep_time_utc"].dt.strftime("%Y%m")
    return normalized


def merge_flights(opdi_df: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    merged = opdi_df.merge(registry, on="icao24", how="inner", suffixes=("_opdi", "_os"))
    if "registration_opdi" in merged.columns:
        merged["registration"] = merged["registration_opdi"].fillna(merged.get("registration_os"))
    elif "registration_os" in merged.columns:
        merged["registration"] = merged["registration_os"]
    if "typecode_os" in merged.columns:
        merged["typecode"] = merged["typecode_os"].fillna(merged.get("typecode_opdi"))
    elif "typecode" not in merged.columns and "typecode_opdi" in merged.columns:
        merged["typecode"] = merged["typecode_opdi"]
    merged["operator"] = merged.get("operator", pd.Series(dtype=str)).fillna(
        merged.get("icao_operator", pd.Series(dtype=str))
    )
    keep = [
        "flight_id",
        "icao24",
        "registration",
        "typecode",
        "operator",
        "built",
        "dep_airport",
        "arr_airport",
        "dep_time_utc",
        "arr_time_utc",
        "dof",
        "opdi_month",
        "flt_id",
    ]
    keep = [col for col in keep if col in merged.columns]
    return merged[keep].drop_duplicates()


def build_flights(
    config: dict | None = None,
    months: list[str] | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    config = config or load_config()
    months = months or config["opdi"]["months"]
    registry = load_b737_registry(config)
    frames: list[pd.DataFrame] = []
    for month in months:
        raw = load_opdi(month, config=config, use_cache=use_cache)
        normalized = _normalize_flights(raw, config)
        frames.append(merge_flights(normalized, registry))
    flights = pd.concat(frames, ignore_index=True)
    flights = flights.drop_duplicates(subset=["flight_id"], keep="first")
    flights = flights.sort_values(["icao24", "dep_time_utc"]).reset_index(drop=True)
    return flights


def save_flights(flights: pd.DataFrame, config: dict | None = None) -> Path:
    config = config or load_config()
    output = Path(config["paths"]["flights"])
    output.parent.mkdir(parents=True, exist_ok=True)
    flights.to_parquet(output, index=False)
    return output


def explore_opdi(month: str | None = None, config: dict | None = None) -> None:
    config = config or load_config()
    month = month or config["opdi"]["months"][0]
    df = load_opdi(month, config=config, use_cache=True)
    registry = load_b737_registry(config)
    print(f"OPDI month: {month}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(df.dtypes)
    print(f"Unique icao24: {df['icao24'].nunique()}")
    df["icao24"] = _normalize_icao24(df["icao24"])
    registry["icao24"] = _normalize_icao24(registry["icao24"])
    merged = df.merge(registry, on="icao24", how="inner")
    print(f"B737 flights in month: {len(merged)}")
    print(f"Unique B737 aircraft: {merged['icao24'].nunique()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="OPDI + OpenSky ingest for B737 Europe")
    parser.add_argument("--explore", action="store_true", help="Print schema stats for one month")
    parser.add_argument("--build", action="store_true", help="Build and save flights.parquet")
    parser.add_argument("--month", type=str, default=None, help="Month for --explore (YYYYMM)")
    parser.add_argument("--no-cache", action="store_true", help="Skip local parquet cache")
    args = parser.parse_args()
    config = load_config()
    if args.explore:
        explore_opdi(month=args.month, config=config)
        return
    if args.build or not args.explore:
        flights = build_flights(config=config, use_cache=not args.no_cache)
        output = save_flights(flights, config=config)
        print(f"Saved {len(flights)} flights, {flights['icao24'].nunique()} aircraft -> {output}")


if __name__ == "__main__":
    main()
