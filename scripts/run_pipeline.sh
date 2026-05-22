#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

MODE="${1:-opdi}"
if [[ "$MODE" == "demo" ]]; then
  python scripts/run_pipeline.py --demo
else
  python scripts/run_pipeline.py --rebuild-flights
fi

echo "Done. Run: streamlit run app/main.py"
