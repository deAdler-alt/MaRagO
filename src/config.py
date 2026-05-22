from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or CONFIG_PATH
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    for key, value in config.get("paths", {}).items():
        if isinstance(value, str) and not value.startswith("/"):
            config["paths"][key] = str(ROOT / value)
    config["root"] = str(ROOT)
    return config
