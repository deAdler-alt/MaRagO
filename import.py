"""Backward-compatible entry point — delegates to src.ingest.opdi."""

from src.ingest.opdi import explore_opdi, main

if __name__ == "__main__":
    main()
