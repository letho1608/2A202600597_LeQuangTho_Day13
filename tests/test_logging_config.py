from pathlib import Path

from app.logging_config import JsonlFileProcessor, configure_logging, get_audit_logger, get_logger


def test_get_logger_returns_structlog() -> None:
    configure_logging()
    log = get_logger()
    assert log is not None


def test_get_audit_logger_binds_audit() -> None:
    configure_logging()
    log = get_audit_logger()
    assert log is not None


def test_jsonl_file_processor_writes(tmp_path: Path, monkeypatch) -> None:
    log_file = tmp_path / "sub" / "out.jsonl"
    monkeypatch.setenv("LOG_PATH", str(log_file))
    from app import logging_config

    logging_config.LOG_PATH = log_file
    proc = JsonlFileProcessor()
    proc(None, "info", {"event": "test", "level": "info"})
    assert log_file.exists()
    contents = log_file.read_text(encoding="utf-8").strip()
    assert '"event": "test"' in contents
