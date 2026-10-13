"""Typed configuration access with environment-variable overrides.

Secrets (SMTP password, API tokens) should be supplied via environment
variables instead of the checked-in config file, e.g.::

    RPA_SMTP_PASSWORD=xxxx python run_demo.py
"""
from __future__ import annotations

import configparser
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config.ini"
EXAMPLE_CONFIG = PROJECT_ROOT / "config.example.ini"


class Settings:
    """Reads ``config.ini`` (falling back to ``config.example.ini``) and
    overlays environment variables where declared."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        path = Path(config_path) if config_path else DEFAULT_CONFIG
        if not path.exists():
            path = EXAMPLE_CONFIG
        self._path = path
        self._parser = configparser.ConfigParser()
        self._parser.read(path, encoding="utf-8")

    # ------------------------------------------------------------------
    # low-level accessors
    # ------------------------------------------------------------------
    def get(
        self,
        section: str,
        key: str,
        default: str | None = None,
        env_var: str | None = None,
    ) -> str | None:
        if env_var and env_var in os.environ:
            return os.environ[env_var]
        if self._parser.has_option(section, key):
            return self._parser.get(section, key)
        return default

    def get_int(self, section: str, key: str, default: int, env_var: str | None = None) -> int:
        raw = self.get(section, key, None, env_var)
        try:
            return int(raw) if raw is not None else default
        except ValueError:
            return default

    def get_bool(self, section: str, key: str, default: bool, env_var: str | None = None) -> bool:
        raw = self.get(section, key, None, env_var)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    def _resolve(self, raw: str) -> Path:
        path = Path(raw)
        return path if path.is_absolute() else PROJECT_ROOT / path

    # ------------------------------------------------------------------
    # domain properties
    # ------------------------------------------------------------------
    @property
    def company_name(self) -> str:
        return self.get("general", "company_name", "ACME GmbH") or "ACME GmbH"

    @property
    def database_path(self) -> Path:
        raw = self.get("database", "db_path", "data/orders.db", "RPA_DB_PATH") or "data/orders.db"
        return self._resolve(raw)

    @property
    def ingest_mode(self) -> str:
        return (self.get("ingest", "mode", "mock", "RPA_INGEST_MODE") or "mock").lower()

    @property
    def mock_order_file(self) -> Path:
        raw = (
            self.get("ingest", "mock_order_file", "data/raw/orders_raw.csv")
            or "data/raw/orders_raw.csv"
        )
        return self._resolve(raw)

    @property
    def mock_order_count(self) -> int:
        return self.get_int("ingest", "mock_order_count", 300)

    @property
    def mock_seed(self) -> int:
        return self.get_int("ingest", "mock_seed", 42)

    @property
    def api_url(self) -> str:
        return self.get("ingest", "api_url", "", "RPA_API_URL") or ""

    @property
    def api_consumer_key(self) -> str:
        return self.get("ingest", "api_consumer_key", "", "RPA_API_CONSUMER_KEY") or ""

    @property
    def api_consumer_secret(self) -> str:
        return self.get("ingest", "api_consumer_secret", "", "RPA_API_CONSUMER_SECRET") or ""

    @property
    def api_token(self) -> str:
        return self.get("ingest", "api_token", "", "RPA_API_TOKEN") or ""

    @property
    def api_fallback_to_mock(self) -> bool:
        return self.get_bool("ingest", "api_fallback_to_mock", True)

    @property
    def api_timeout_sec(self) -> int:
        return self.get_int("ingest", "api_timeout_sec", 30)

    @property
    def cleaning_required_fields(self) -> list[str]:
        raw = self.get("cleaning", "required_fields", "order_id, customer, amount") or ""
        return [c.strip() for c in raw.split(",") if c.strip()]

    @property
    def cleaning_duplicate_key(self) -> str:
        return self.get("cleaning", "duplicate_key", "order_id") or "order_id"

    @property
    def cleaning_min_amount(self) -> float:
        return float(self.get("cleaning", "min_amount", "0") or "0")

    @property
    def cleaning_max_amount(self) -> float:
        return float(self.get("cleaning", "max_amount", "100000") or "100000")

    @property
    def report_output_dir(self) -> Path:
        return self._resolve(self.get("report", "output_dir", "data/reports") or "data/reports")

    @property
    def report_currency_symbol(self) -> str:
        return self.get("report", "currency_symbol", "EUR") or "EUR"

    @property
    def smtp_host(self) -> str:
        return self.get("alert", "smtp_host", "smtp.qq.com", "RPA_SMTP_HOST") or ""

    @property
    def smtp_port(self) -> int:
        return self.get_int("alert", "smtp_port", 465, "RPA_SMTP_PORT")

    @property
    def smtp_sender(self) -> str:
        return self.get("alert", "sender", "", "RPA_SMTP_SENDER") or ""

    @property
    def smtp_password(self) -> str:
        return self.get("alert", "password", "", "RPA_SMTP_PASSWORD") or ""

    @property
    def smtp_receiver(self) -> str:
        return self.get("alert", "receiver", "", "RPA_SMTP_RECEIVER") or ""

    @property
    def alert_retry_times(self) -> int:
        return self.get_int("alert", "retry_times", 3)

    @property
    def alert_retry_interval_sec(self) -> int:
        return self.get_int("alert", "retry_interval_sec", 5)

    @property
    def alert_after_consecutive_failures(self) -> int:
        return self.get_int("alert", "alert_after_consecutive_failures", 2)

    @property
    def smtp_configured(self) -> bool:
        return bool(
            self.smtp_host and self.smtp_sender and self.smtp_password and self.smtp_receiver
        )
