"""Email alerting with retry, plus a consecutive-failure tracker.

Two independent responsibilities:
- ``MailAlert.send`` - sends an email with configurable retries
- ``FailureTracker`` - persists consecutive pipeline failures to a small
  JSON state file, so an alert fires only after N consecutive failures
  (avoids alert spam on a single transient glitch).
"""
from __future__ import annotations

import json
import logging
import smtplib
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

from ..config import PROJECT_ROOT, Settings

logger = logging.getLogger("rpa.alerting")


class MailAlert:
    """Sends alert emails over SMTP (SSL or STARTTLS) with retry."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, subject: str, body: str) -> bool:
        """Try to send; retry ``retry_times`` times on failure."""
        if not self.settings.smtp_configured:
            logger.warning("SMTP not configured - skipping email alert")
            return False

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((self.settings.company_name, self.settings.smtp_sender))
        msg["To"] = self.settings.smtp_receiver

        attempts = 0
        max_attempts = self.settings.alert_retry_times + 1  # first try + retries
        while attempts < max_attempts:
            attempts += 1
            try:
                if self.settings.smtp_port == 465:
                    with smtplib.SMTP_SSL(
                        self.settings.smtp_host, self.settings.smtp_port, timeout=30
                    ) as server:
                        server.login(self.settings.smtp_sender, self.settings.smtp_password)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(
                        self.settings.smtp_host, self.settings.smtp_port, timeout=30
                    ) as server:
                        server.starttls()
                        server.login(self.settings.smtp_sender, self.settings.smtp_password)
                        server.send_message(msg)
                logger.info(
                    "Alert email sent to %s (attempt %d)",
                    self.settings.smtp_receiver,
                    attempts,
                )
                return True
            except smtplib.SMTPException as exc:
                logger.error("Alert send failed (attempt %d/%d): %s", attempts, max_attempts, exc)
                if attempts < max_attempts:
                    time.sleep(self.settings.alert_retry_interval_sec)
        return False


class FailureTracker:
    """Persists consecutive failure count across runs."""

    def __init__(self, state_path: str | Path | None = None) -> None:
        self.state_path = Path(state_path) if state_path else PROJECT_ROOT / "data" / "state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _save(self) -> None:
        payload = json.dumps(self._state, ensure_ascii=False, indent=2)
        self.state_path.write_text(payload, encoding="utf-8")

    @property
    def consecutive_failures(self) -> int:
        return int(self._state.get("consecutive_failures", 0))

    def record_success(self) -> None:
        self._state["consecutive_failures"] = 0
        self._save()

    def record_failure(self) -> int:
        count = self.consecutive_failures + 1
        self._state["consecutive_failures"] = count
        self._save()
        return count

    def should_alert(self, threshold: int) -> bool:
        return self.consecutive_failures >= threshold
