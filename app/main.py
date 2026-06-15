from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars

load_dotenv()

from .agent import LabAgent
from .dashboard import mount_dashboard
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_audit_logger, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import flush_traces, tracing_enabled

configure_logging()
log = get_logger()
audit_log = get_audit_logger()
APP_ENV = os.getenv("APP_ENV", "dev")
APP_NAME = os.getenv("APP_NAME", "day13-observability-lab")
DEFAULT_MODEL = "claude-sonnet-4-5"

app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
mount_dashboard(app)
agent = LabAgent(model=DEFAULT_MODEL)


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service="startup",
        env=APP_ENV,
        payload={"name": APP_NAME, "tracing_enabled": tracing_enabled()},
    )
    audit_log.info(
        "service_started",
        service="startup",
        env=APP_ENV,
        payload={"name": APP_NAME},
    )


@app.on_event("shutdown")
async def shutdown() -> None:
    flush_traces()
    log.info("app_stopped", service="startup", env=APP_ENV)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=DEFAULT_MODEL,
        env=APP_ENV,
    )

    log.info(
        "request_received",
        service="api",
        payload={"message_preview": summarize_text(body.message)},
    )
    try:
        result = agent.run(
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            message=body.message,
        )
        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            payload={"answer_preview": summarize_text(result.answer)},
        )
        audit_log.info(
            "chat_completed",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            payload={"user_id_hash": hash_user_id(body.user_id), "feature": body.feature},
        )
        return ChatResponse(
            answer=result.answer,
            correlation_id=request.state.correlation_id,
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
        )
    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
        )
        audit_log.error(
            "chat_failed",
            service="api",
            error_type=error_type,
            payload={"user_id_hash": hash_user_id(body.user_id), "feature": body.feature},
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        audit_log.warning(
            "incident_enabled",
            service="control",
            payload={"name": name, "actor": "operator"},
        )
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        audit_log.warning(
            "incident_disabled",
            service="control",
            payload={"name": name, "actor": "operator"},
        )
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
