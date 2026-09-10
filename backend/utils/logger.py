"""
backend/utils/logger.py

Shared logging configuration for F1 PitWall AI.

Usage
-----
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")

Output format
-------------
    2026-08-01 10:30:00 | INFO     | backend.main | F1 PitWall AI API started
"""

import logging
import sys
from typing import Optional


# ------------------------------------------------------------------ #
# Format                                                               #
# ------------------------------------------------------------------ #
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Track whether the root logger has been configured already.
_configured: bool = False


def _configure_root_logger(level: int = logging.DEBUG) -> None:
    """
    Set up the root logger with a StreamHandler pointed at stdout.
    Called automatically the first time get_logger() is invoked.
    """
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid adding duplicate handlers if something else already added one.
    if not root.handlers:
        root.addHandler(handler)

    # Suppress noisy third-party loggers at WARNING and above.
    for noisy in ("uvicorn.access", "httpx", "httpcore", "fastf1"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: Optional[str] = None, level: int = logging.DEBUG) -> logging.Logger:
    """
    Return a named logger, configuring the root logger on first call.

    Parameters
    ----------
    name:
        Typically ``__name__`` of the calling module.
    level:
        Minimum severity level for this specific logger.

    Returns
    -------
    logging.Logger
    """
    _configure_root_logger(level=level)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
