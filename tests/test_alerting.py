"""Tests for email alerting and the failure tracker."""
from __future__ import annotations

import smtplib

from rpa_platform.alerting.mail_alert import FailureTracker, MailAlert


def test_alert_sends_successfully(settings, monkeypatch):
    calls: list[dict] = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs) -> None:
            calls.append({"args": args})

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def login(self, user, password) -> None:
            calls.append({"login": (user, password)})

        def send_message(self, msg) -> None:
            calls.append({"send": msg["To"]})

    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    alert = MailAlert(settings)
    assert alert.send("Test subject", "Test body") is True
    assert calls[0]["args"][0] == "smtp.test.local"
    assert calls[-1]["send"] == "receiver@test.local"


def test_alert_retries_then_fails(settings, monkeypatch):
    attempts: list[int] = []

    class FailingSMTP:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def login(self, user, password) -> None:
            attempts.append(1)
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

        def send_message(self, msg) -> None:
            raise AssertionError("should not be reached")

    monkeypatch.setattr(smtplib, "SMTP_SSL", FailingSMTP)
    alert = MailAlert(settings)  # retry_times=1 -> 2 attempts total
    assert alert.send("Subject", "Body") is False
    assert len(attempts) == 2


def test_alert_skips_when_smtp_not_configured(monkeypatch, tmp_path):
    ini = tmp_path / "empty.ini"
    ini.write_text("[alert]\n", encoding="utf-8")
    from rpa_platform.config import Settings

    alert = MailAlert(Settings(ini))
    assert alert.send("Subject", "Body") is False


def test_failure_tracker_counts_and_alert_threshold(tmp_path):
    state = tmp_path / "state.json"
    tracker = FailureTracker(state)
    assert tracker.consecutive_failures == 0

    tracker.record_failure()
    tracker.record_failure()
    assert tracker.consecutive_failures == 2
    assert tracker.should_alert(2) is True
    assert tracker.should_alert(3) is False

    tracker.record_success()
    assert tracker.consecutive_failures == 0
    assert tracker.should_alert(2) is False
