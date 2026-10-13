"""Data cleaning with an explicit quality report.

Cleaning rules (all configurable via ``config.ini``):
- required fields must be non-empty       -> row removed
- duplicate order ids                     -> keep first, remove rest
- amount must be numeric & within range   -> row removed
- ordered_at must parse as a date         -> row removed

The returned quality report classifies every removed row so downstream
reporting can show exactly what was wrong - the "data quality report"
feature that makes the platform visibly more than a toy script.
"""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from ..config import Settings

logger = logging.getLogger("rpa.cleaning")

DEFAULT_RULES = {
    "required_fields": ["order_id", "customer", "amount"],
    "duplicate_key": "order_id",
    "min_amount": 0.0,
    "max_amount": 100000.0,
}


class DataCleaner:
    """Applies configured validation rules to a raw order DataFrame."""

    def __init__(self, settings: Settings | None = None, rules: dict | None = None) -> None:
        base = dict(DEFAULT_RULES)
        if settings is not None:
            base["required_fields"] = settings.cleaning_required_fields
            base["duplicate_key"] = settings.cleaning_duplicate_key
            base["min_amount"] = settings.cleaning_min_amount
            base["max_amount"] = settings.cleaning_max_amount
        if rules:
            base.update(rules)
        self.rules = base

    # ------------------------------------------------------------------
    def clean(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        """Return ``(cleaned_df, quality_report)``."""
        issues: dict[str, list[dict]] = {
            "missing_fields": [],
            "duplicates": [],
            "invalid_amount": [],
            "invalid_date": [],
        }

        work = df.copy()
        for col in self.rules["required_fields"]:
            if col not in work.columns:
                work[col] = ""

        # 1) required fields -------------------------------------------------
        mask_missing = work[self.rules["required_fields"]].apply(
            lambda row: any(pd.isna(v) or str(v).strip() == "" for v in row), axis=1
        )
        for order_id in work.loc[mask_missing, self.rules["duplicate_key"]]:
            issues["missing_fields"].append(
                {"order_id": order_id, "reason": "missing required field"}
            )
        work = work[~mask_missing]

        # 2) duplicates ------------------------------------------------------
        key = self.rules["duplicate_key"]
        if key in work.columns:
            dup_mask = work[key].duplicated(keep="first")
            for order_id in work.loc[dup_mask, key]:
                issues["duplicates"].append({"order_id": order_id, "reason": "duplicate order id"})
            work = work[~dup_mask]

        # 3) amount range ----------------------------------------------------
        def _bad_amount(row: pd.Series) -> bool:
            try:
                value = float(row.get("amount", float("nan")))
            except (TypeError, ValueError):
                return True
            return (
                pd.isna(value)
                or value < self.rules["min_amount"]
                or value > self.rules["max_amount"]
            )

        mask_amount = work.apply(_bad_amount, axis=1)
        for order_id in work.loc[mask_amount, key]:
            issues["invalid_amount"].append(
                {"order_id": order_id, "reason": "amount out of range / not numeric"}
            )
        work = work[~mask_amount]

        # 4) date format -----------------------------------------------------
        def _bad_date(row: pd.Series) -> bool:
            raw = str(row.get("ordered_at", "")).strip()
            try:
                datetime.strptime(raw[:10], "%Y-%m-%d")
                return False
            except ValueError:
                return True

        mask_date = work.apply(_bad_date, axis=1)
        for order_id in work.loc[mask_date, key]:
            issues["invalid_date"].append({"order_id": order_id, "reason": "malformed order date"})
        work = work[~mask_date]

        # normalise date & amount --------------------------------------------
        if not work.empty:
            work["ordered_at"] = work["ordered_at"].astype(str).str[:10]
            work["amount"] = pd.to_numeric(work["amount"], errors="coerce")

        report = self.build_quality_report(df, work, issues)
        logger.info(
            "Cleaning done: %d raw -> %d valid (removed %d)",
            report["raw_count"],
            report["cleaned_count"],
            report["removed_total"],
        )
        return work.reset_index(drop=True), report

    # ------------------------------------------------------------------
    @staticmethod
    def build_quality_report(raw: pd.DataFrame, cleaned: pd.DataFrame, issues: dict) -> dict:
        """Aggregate the per-row issues into a summary report dict."""
        counts = {k: len(v) for k, v in issues.items()}
        return {
            "raw_count": int(len(raw)),
            "cleaned_count": int(len(cleaned)),
            "removed_total": int(len(raw) - len(cleaned)),
            "issue_counts": counts,
            "issues": issues,
            "total_revenue_after": float(cleaned["amount"].sum()) if not cleaned.empty else 0.0,
            "order_count_after": int(len(cleaned)),
        }
