from __future__ import annotations

import os
from typing import Any

try:
    from langfuse import Langfuse, get_client, observe
except Exception:  # pragma: no cover
    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            return func
        return decorator

    def get_client() -> Any:
        return None

    class _DummyContext:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_observation(self, **kwargs: Any) -> None:
            return None

        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    langfuse_context = _DummyContext()
    Langfuse = None  # type: ignore[assignment]


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def flush_traces() -> None:
    """Flush pending traces to Langfuse (call before shutdown)."""
    try:
        client = get_client()
        if client is not None and hasattr(client, "flush"):
            client.flush()
    except Exception:
        pass
