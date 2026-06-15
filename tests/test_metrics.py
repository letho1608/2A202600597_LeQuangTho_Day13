import app.metrics
from app.metrics import (
    ERRORS,
    QUALITY_SCORES,
    REQUEST_COSTS,
    REQUEST_LATENCIES,
    REQUEST_TOKENS_IN,
    REQUEST_TOKENS_OUT,
    percentile,
    record_error,
    record_request,
    snapshot,
)


def setup_function(_):
    REQUEST_LATENCIES.clear()
    REQUEST_COSTS.clear()
    REQUEST_TOKENS_IN.clear()
    REQUEST_TOKENS_OUT.clear()
    QUALITY_SCORES.clear()
    ERRORS.clear()
    app.metrics.TRAFFIC = 0


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100
    assert percentile([100, 200, 300, 400], 95) >= 100


def test_percentile_empty() -> None:
    assert percentile([], 50) == 0.0


def test_record_request_increments_traffic() -> None:
    record_request(100, 0.001, 50, 30, 0.8)
    record_request(200, 0.002, 60, 40, 0.7)
    assert app.metrics.TRAFFIC == 2
    assert sum(REQUEST_LATENCIES) == 300
    assert sum(REQUEST_TOKENS_IN) == 110
    assert sum(REQUEST_TOKENS_OUT) == 70


def test_record_error_counts() -> None:
    record_error("ValueError")
    record_error("ValueError")
    record_error("TimeoutError")
    assert ERRORS["ValueError"] == 2
    assert ERRORS["TimeoutError"] == 1


def test_snapshot_shape() -> None:
    record_request(150, 0.0001, 10, 20, 0.9)
    s = snapshot()
    for key in (
        "traffic",
        "latency_p50",
        "latency_p95",
        "latency_p99",
        "avg_cost_usd",
        "total_cost_usd",
        "tokens_in_total",
        "tokens_out_total",
        "error_breakdown",
        "quality_avg",
    ):
        assert key in s
