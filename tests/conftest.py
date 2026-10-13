"""Shared pytest fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rpa_platform.config import Settings  # noqa: E402


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings pointing every output at a per-test temp directory."""
    ini = tmp_path / "config.ini"
    ini.write_text(
        f"""
[general]
company_name = Test GmbH
region = de

[database]
db_path = {tmp_path / "orders.db"}

[ingest]
mode = mock
mock_order_file = {tmp_path / "raw.csv"}
mock_order_count = 50
mock_seed = 7

[cleaning]
required_fields = order_id, customer, amount
duplicate_key = order_id
min_amount = 0
max_amount = 100000

[report]
output_dir = {tmp_path / "reports"}
currency_symbol = EUR

[alert]
smtp_host = smtp.test.local
smtp_port = 465
sender = sender@test.local
password = secret
receiver = receiver@test.local
retry_times = 1
retry_interval_sec = 0
alert_after_consecutive_failures = 2
""",
        encoding="utf-8",
    )
    return Settings(ini)


@pytest.fixture
def clean_df():
    import pandas as pd

    return pd.DataFrame(
        [
            {"order_id": "O1", "customer": "Alpha GmbH", "ordered_at": "2026-01-05", "product": "Chair", "amount": 120.0, "status": "completed"},
            {"order_id": "O2", "customer": "Beta e.K.", "ordered_at": "2026-02-11", "product": "Desk", "amount": 540.5, "status": "processing"},
            {"order_id": "O3", "customer": "Gamma KG", "ordered_at": "2026-03-03", "product": "Monitor", "amount": 210.0, "status": "completed"},
        ]
    )
