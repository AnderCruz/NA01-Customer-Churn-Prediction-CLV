"""Structured events with an explicit allowlist of operational fields."""

import json
import logging
from datetime import UTC, datetime
from time import perf_counter_ns
from uuid import UUID

from fastapi.routing import APIRoute
from starlette.requests import Request

from .dependencies import get_foundation_state
from .errors import ErrorCode

LOGGER_NAME = "nowa_customer_intelligence.api.audit"


def _emit(event: str, fields: dict[str, object]) -> None:
    logging.getLogger(LOGGER_NAME).info(
        json.dumps(
            {"event": event, "time": datetime.now(UTC).isoformat(), **fields},
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )


def record_request(request: Request, request_id: UUID, status: int, started_ns: int) -> None:
    state = get_foundation_state(request)
    route = request.scope.get("route")
    operation = route.operation_id if isinstance(route, APIRoute) else None
    code = getattr(request.state, "error_code", None)
    fields: dict[str, object] = {
        "request_id": str(request_id),
        "operation_id": operation or "unmatched",
        "status": status,
        "duration_ms": (perf_counter_ns() - started_ns) / 1_000_000,
        "category": code.value if isinstance(code, ErrorCode) else "SUCCESS",
        "service_version": state.service.service_version,
    }
    if state.catalogue is not None:
        fields["release_id"] = state.catalogue.release_id
    _emit("api_request", fields)


def record_evidence(category: str, release_id: str | None = None) -> None:
    fields: dict[str, object] = {"category": category}
    if release_id is not None:
        fields["release_id"] = release_id
    _emit("research_catalogue", fields)
