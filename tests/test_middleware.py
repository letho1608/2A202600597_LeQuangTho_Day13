from app.middleware import _new_correlation_id, _normalize_correlation_id


def test_new_correlation_id_format() -> None:
    cid = _new_correlation_id()
    assert cid.startswith("req-")
    assert len(cid) == len("req-") + 8


def test_normalize_correlation_id_from_header() -> None:
    assert _normalize_correlation_id("abc12345") == "req-abc12345"


def test_normalize_correlation_id_empty() -> None:
    cid = _normalize_correlation_id("")
    assert cid.startswith("req-")
    assert len(cid) == len("req-") + 8


def test_normalize_correlation_id_too_long() -> None:
    cid = _normalize_correlation_id("a" * 200)
    assert cid.startswith("req-")
    assert len(cid) <= 64


def test_normalize_correlation_id_unsafe_chars() -> None:
    cid = _normalize_correlation_id("!@#$%^&*()")
    assert cid.startswith("req-")
    assert "!" not in cid and "@" not in cid
