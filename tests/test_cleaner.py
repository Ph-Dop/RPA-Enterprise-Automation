"""Tests for the data cleaning stage."""
from __future__ import annotations

import pandas as pd

from rpa_platform.cleaning.cleaner import DataCleaner


def _dirty_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"order_id": "O1", "customer": "Alpha GmbH", "ordered_at": "2026-01-05", "product": "Chair", "amount": 120.0, "status": "completed"},
            {"order_id": "O2", "customer": "", "ordered_at": "2026-01-06", "product": "Desk", "amount": 540.5, "status": "processing"},  # missing customer
            {"order_id": "O3", "customer": "Beta e.K.", "ordered_at": "2026-01-07", "product": "Desk", "amount": 540.5, "status": "completed"},
            {"order_id": "O3", "customer": "Beta e.K.", "ordered_at": "2026-01-07", "product": "Desk", "amount": 540.5, "status": "completed"},  # duplicate id
            {"order_id": "O4", "customer": "Gamma KG", "ordered_at": "2026-01-08", "product": "Monitor", "amount": -10.0, "status": "completed"},  # negative amount
            {"order_id": "O5", "customer": "Delta OHG", "ordered_at": "2026-13-45", "product": "Keyboard", "amount": 80.0, "status": "pending"},  # bad date
        ]
    )


def test_clean_data_passes_through(clean_df):
    cleaned, report = DataCleaner().clean(clean_df)
    assert report["raw_count"] == 3
    assert report["cleaned_count"] == 3
    assert report["removed_total"] == 0
    assert all(len(v) == 0 for v in report["issues"].values())


def test_dirty_rows_are_removed_and_classified():
    cleaned, report = DataCleaner().clean(_dirty_frame())
    assert report["raw_count"] == 6
    assert report["cleaned_count"] == 2  # O1 and keep-first O3
    assert report["removed_total"] == 4
    assert report["issue_counts"] == {
        "missing_fields": 1,
        "duplicates": 1,
        "invalid_amount": 1,
        "invalid_date": 1,
    }
    order_ids = set(cleaned["order_id"])
    assert order_ids == {"O1", "O3"}


def test_nan_values_treated_as_missing():
    """CSV round-trips turn empty strings into NaN - must still be flagged."""
    df = pd.DataFrame(
        [
            {"order_id": "A", "customer": None, "ordered_at": "2026-01-01", "product": "X", "amount": 10.0, "status": "completed"},
            {"order_id": "B", "customer": "Y", "ordered_at": "2026-01-02", "product": "Y", "amount": 20.0, "status": "completed"},
        ]
    )
    cleaned, report = DataCleaner().clean(df)
    assert report["issue_counts"]["missing_fields"] == 1
    assert report["cleaned_count"] == 1
    assert set(cleaned["order_id"]) == {"B"}


def test_custom_rules_override_defaults():
    rules = {"required_fields": ["order_id"], "duplicate_key": "order_id", "min_amount": 0, "max_amount": 50}
    df = pd.DataFrame(
        [
            {"order_id": "A", "customer": "X", "ordered_at": "2026-01-01", "amount": 100.0},
            {"order_id": "B", "customer": "Y", "ordered_at": "2026-01-02", "amount": 10.0},
        ]
    )
    cleaned, report = DataCleaner(rules=rules).clean(df)
    assert report["cleaned_count"] == 1
    assert cleaned.iloc[0]["order_id"] == "B"
