"""Production API ingestion channel (WooCommerce / Shopify style REST API).

Demonstrates that the platform can talk to real business systems - the
key difference from a toy script. Credentials are read from config or
environment variables. On failure the pipeline can degrade gracefully
to the mock channel (configurable via ``api_fallback_to_mock``).
"""
from __future__ import annotations

import logging

import pandas as pd
import requests

from ..config import Settings
from .base import OrderIngestor
from .mock_ingest import MockOrderIngestor

logger = logging.getLogger("rpa.ingest.api")


class ApiOrderIngestor(OrderIngestor):
    """Pulls orders from a WooCommerce-style REST API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict:
        if self.settings.api_token:
            return {"Authorization": f"Bearer {self.settings.api_token}"}
        return {}

    def _auth(self) -> tuple | None:
        if self.settings.api_consumer_key and self.settings.api_consumer_secret:
            return (self.settings.api_consumer_key, self.settings.api_consumer_secret)
        return None

    def ingest(self) -> pd.DataFrame:
        if not self.settings.api_url:
            logger.warning("api_url is empty - switching to mock channel")
            return MockOrderIngestor(self.settings).ingest()

        logger.info("Fetching orders from %s", self.settings.api_url)
        try:
            resp = requests.get(
                self.settings.api_url,
                headers=self._headers(),
                auth=self._auth(),
                timeout=self.settings.api_timeout_sec,
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            logger.error("API request failed: %s", exc)
            if self.settings.api_fallback_to_mock:
                logger.warning("Falling back to mock channel")
                return MockOrderIngestor(self.settings).ingest()
            raise

        rows = [self._map_order(item) for item in payload]
        logger.info("API returned %d orders", len(rows))
        return self._ensure_schema(pd.DataFrame(rows))

    @staticmethod
    def _map_order(item: dict) -> dict:
        """Map a WooCommerce order object to the unified schema."""
        line_total = 0.0
        for line in item.get("line_items", []) or []:
            line_total += float(line.get("total", 0) or 0)
        billing = item.get("billing", {}) or {}
        customer = " ".join(
            filter(None, [billing.get("first_name", ""), billing.get("last_name", "")])
        ).strip()
        return {
            "order_id": str(item.get("id", "")),
            "customer": customer,
            "ordered_at": str(item.get("date_created", ""))[:10],
            "product": " / ".join(
                line.get("name", "") for line in (item.get("line_items", []) or [])
            ),
            "amount": line_total,
            "status": str(item.get("status", "")),
        }
