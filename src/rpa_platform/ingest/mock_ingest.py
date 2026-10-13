"""Mock ingestion channel.

Reads the raw CSV produced by ``scripts/generate_mock_data.py``; if the file
is missing it generates a fresh synthetic dataset (with deliberately dirty
rows: empty fields, duplicate order ids, out-of-range amounts, malformed
dates) so the cleaning stage has something real to do.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..config import Settings
from .base import OUTPUT_COLUMNS, OrderIngestor

logger = logging.getLogger("rpa.ingest.mock")

CUSTOMERS = [
    "Müller GmbH", "Schmidt & Söhne", "Weber Handel", "Fischer KG", "Wagner & Co",
    "Becker GmbH", "Hoffmann OHG", "Koch e.K.", "Richter GmbH", "Klein & Partner",
    "Alpha Elektronik", "Bavaria Werkzeuge", "Rheinland Logistics", "Nordwind Trading",
    "Südstern GmbH",
]
PRODUCTS = [
    "Ergo Office Chair", "Height-adjustable Desk", "LED Monitor Arm", "Laptop Stand",
    "Mechanical Keyboard", "Wireless Mouse", "USB-C Dock", "4K Webcam",
    "Noise-cancel Headset", "Cable Organizer Kit",
]
STATUSES = ["completed", "processing", "pending", "cancelled", "refunded"]


def generate_raw_orders(
    count: int = 300,
    seed: int = 42,
    dirty_ratio: float = 0.15,
) -> pd.DataFrame:
    """Generate a synthetic order dataset containing deliberate dirty rows."""
    import random

    rng = random.Random(seed)
    rows: list[dict] = []
    for i in range(count):
        order_id = f"ORD-{10000 + i}"
        customer = rng.choice(CUSTOMERS)
        product = rng.choice(PRODUCTS)
        amount = round(rng.uniform(15, 4500), 2)
        day = rng.randint(1, 28)
        month = rng.randint(1, 12)
        ordered_at = f"2026-{month:02d}-{day:02d}"
        status = rng.choice(STATUSES)

        # ---- deliberately inject dirt (only on the RAW side) ----
        if rng.random() < dirty_ratio:
            kind = rng.random()
            if kind < 0.25:
                customer = ""  # missing customer
            elif kind < 0.45:
                order_id = f"ORD-{10000 + rng.randint(0, count - 1)}"  # duplicate id
            elif kind < 0.70:
                amount = round(rng.uniform(-50, 300000), 2)  # out-of-range amount
            elif kind < 0.85:
                ordered_at = "2026-13-45"  # malformed date
            else:
                product = ""  # missing product

        rows.append(
            {
                "order_id": order_id,
                "customer": customer,
                "ordered_at": ordered_at,
                "product": product,
                "amount": amount,
                "status": status,
            }
        )
    return pd.DataFrame(rows)[OUTPUT_COLUMNS]


class MockOrderIngestor(OrderIngestor):
    """Reads/generates the local mock order CSV."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def ingest(self) -> pd.DataFrame:
        path: Path = self.settings.mock_order_file
        if path.exists():
            logger.info("Loading mock orders from %s", path)
            df = pd.read_csv(path, encoding="utf-8")
        else:
            logger.info(
                "Mock file not found (%s) - generating %d rows (seed=%d)",
                path,
                self.settings.mock_order_count,
                self.settings.mock_seed,
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            df = generate_raw_orders(self.settings.mock_order_count, self.settings.mock_seed)
            df.to_csv(path, index=False, encoding="utf-8")
        return self._ensure_schema(df)
