"""Structured logging configuration and logger factory."""

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """Configure standard library root logger with clean formatting."""
    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance for the given module name."""
    return logging.getLogger(name)
