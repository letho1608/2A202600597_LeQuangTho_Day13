from app.pii import hash_user_id, scrub_text, summarize_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_phone_vn() -> None:
    out = scrub_text("Call 0987654321 now")
    assert "0987654321" not in out
    assert "REDACTED_PHONE_VN" in out


def test_scrub_phone_with_separators() -> None:
    out = scrub_text("My phone is 090-123-4567")
    assert "REDACTED_PHONE_VN" in out


def test_scrub_credit_card() -> None:
    out = scrub_text("Card 4111 1111 1111 1111 leaked")
    assert "4111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_scrub_cccd() -> None:
    out = scrub_text("CCCD 012345678901")
    assert "012345678901" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_ip() -> None:
    out = scrub_text("server 10.0.0.1 down")
    assert "10.0.0.1" not in out
    assert "REDACTED_IP_V4" in out


def test_scrub_bearer_token() -> None:
    out = scrub_text("Authorization: Bearer abc.def-ghi_jkl")
    assert "REDACTED_BEARER_TOKEN" in out


def test_scrub_jwt() -> None:
    out = scrub_text("token=eyJabcdefghij1234567890.eyJabcdefghij1234567890.sig12345")
    assert "REDACTED_JWT" in out


def test_scrub_passes_clean_text() -> None:
    out = scrub_text("Explain the monitoring policy please")
    assert out == "Explain the monitoring policy please"


def test_summarize_text_truncates() -> None:
    long = "word " * 50
    out = summarize_text(long, max_len=20)
    assert len(out) <= 23  # 20 + "..."
    assert out.endswith("...")


def test_summarize_text_redacts() -> None:
    out = summarize_text("Mail me at test@example.com right now")
    assert "test@" not in out


def test_hash_user_id_stable_and_short() -> None:
    h1 = hash_user_id("u01")
    h2 = hash_user_id("u01")
    h3 = hash_user_id("u02")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 12
