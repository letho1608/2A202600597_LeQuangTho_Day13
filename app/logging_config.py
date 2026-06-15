from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from .pii import scrub_text

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))
AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))


def _write_jsonl(path: Path, event_dict: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = structlog.processors.JSONRenderer()(None, "info", event_dict)
    with path.open("a", encoding="utf-8") as f:
        f.write(rendered + "\n")


class JsonlFileProcessor:
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        _write_jsonl(LOG_PATH, event_dict)
        return event_dict


class AuditFileProcessor:
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        if event_dict.get("audit"):
            audit_record = {k: v for k, v in event_dict.items() if k != "audit"}
            audit_record["audit"] = True
            _write_jsonl(AUDIT_LOG_PATH, audit_record)
        return event_dict


def scrub_event(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    payload = event_dict.get("payload")
    if isinstance(payload, dict):
        event_dict["payload"] = {
            k: scrub_text(v) if isinstance(v, str) else v for k, v in payload.items()
        }
    if "event" in event_dict and isinstance(event_dict["event"], str):
        event_dict["event"] = scrub_text(event_dict["event"])
    return event_dict


def _iso_second_timestamp(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime, timezone
    event_dict["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return event_dict


def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            _iso_second_timestamp,
            scrub_event,
            AuditFileProcessor(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JsonlFileProcessor(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger()


def get_audit_logger() -> structlog.typing.FilteringBoundLogger:
    logger = structlog.get_logger("audit")
    return logger.bind(audit=True)
