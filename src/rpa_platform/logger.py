"""Centralised, audit-friendly logging.

Every step of a run is written to ``data/logs/rpa.log`` with a rotating
handler, plus mirrored to the console. Timestamps make every entry
traceable - an important point for European enterprise compliance.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import PROJECT_ROOT

_configured = False


def setup_logger(
    name: str = "rpa",
    log_dir: str | Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Initialise (once) the platform logger and return it."""
    global _configured

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if _configured:
        return logger

    log_dir_path = Path(log_dir) if log_dir else PROJECT_ROOT / "data" / "logs"
    log_dir_path.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    file_handler = RotatingFileHandler(
        log_dir_path / "rpa.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    _configured = True
    return logger
