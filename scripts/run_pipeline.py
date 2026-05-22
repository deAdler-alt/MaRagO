#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_config
from src.pipeline.build import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MRO prediction pipeline outputs")
    parser.add_argument("--demo", action="store_true", help="Use demo dataset from brief")
    parser.add_argument("--rebuild-flights", action="store_true", help="Re-download OPDI and rebuild flights")
    args = parser.parse_args()

    config = load_config()
    if args.demo:
        config["data_mode"] = "demo"

    outputs = run_pipeline(config=config, rebuild_flights=args.rebuild_flights or args.demo)
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
