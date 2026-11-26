"""Production-grade structured observability logging using Structlog."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def _drop_color_message_key(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Ensure Uvicorn's color_message does not leak into JSON output."""
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging(log_level: str = "INFO", *, json_format: bool = False) -> None:
    """Configure Structlog and standard library logging pipeline.

    Args:
        log_level: Minimum logging level (DEBUG, INFO, WARNING, ERROR).
        json_format: When True, output machine-readable JSON logs (production).
                     When False, output human-readable colored console logs (development).
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Common processors shared by all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _drop_color_message_key,
    ]

    if json_format:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging handler with structlog formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear pre-existing handlers
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)

    root_logger.addHandler(handler)


def get_logger(name: str = "") -> structlog.stdlib.BoundLogger:
    """Return a configured structlog bound logger instance."""
    return structlog.get_logger(name)
