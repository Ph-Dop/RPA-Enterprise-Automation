"""Generate the mock order dataset (with intentional dirty rows).

Usage: python scripts/generate_mock_data.py [--count 500] [--seed 42]

Writes ``data/raw/orders_raw.csv`` which the mock ingestion channel reads.
Running it manually lets you inspect/commit the demo data separately from
the pipeline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rpa_platform.ingest.mock_ingest import generate_raw_orders  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mock order CSV with dirty rows")
    parser.add_argument("--count", type=int, default=500, help="Number of order rows")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/orders_raw.csv")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df = generate_raw_orders(args.count, args.seed)
    df.to_csv(output, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} rows to {output}")


if __name__ == "__main__":
    main()
