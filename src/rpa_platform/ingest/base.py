"""Ingestion channel abstraction.

Dual-channel architecture:
- ``MockOrderIngestor``  - demo/development channel, no external dependency
- ``ApiOrderIngestor``   - production channel (WooCommerce/Shopify style API)

Both channels produce the SAME output schema, so the rest of the pipeline
(cleaning -> reporting -> alerting) is completely channel-agnostic. This is
what lets a fresh GitHub clone run end-to-end without Yingdao RPA installed.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

OUTPUT_COLUMNS = ["order_id", "customer", "ordered_at", "product", "amount", "status"]


class OrderIngestor(ABC):
    """A channel that produces raw order data with a stable schema."""

    @abstractmethod
    def ingest(self) -> pd.DataFrame:
        """Return raw orders as a DataFrame with ``OUTPUT_COLUMNS``."""

    def _ensure_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[OUTPUT_COLUMNS]
