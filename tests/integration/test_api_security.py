"""Exercise the explicit launcher and request security without opening sockets."""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from pydantic import SecretStr

pytest.importorskip("fastapi")
pytest.importorskip("httpx2")
pytest.importorskip("uvicorn")

from fastapi.testclient import TestClient  # noqa: E402

from nowa_customer_intelligence.api import launcher, security  # noqa: E402
from nowa_customer_intelligence.api.application import create_app  # noqa: E402
from nowa_customer_intelligence.api.audit import LOGGER_NAME  # noqa: E402
from nowa_customer_intelligence.api.configuration import (  # noqa: E402
    ApiConfiguration,
    ConfigurationError,
)

TOKEN = "synthetic_test_secret_for_api_security"
PATH = "/v1/research/models/churn/evaluation"


def loopback_settings() -> ApiConfiguration:
    return ApiConfiguration(
        mode="loopback",
        bundle_root=Path("/not-a-real-research-release"),
        release_sha256="a" * 64,
        bearer_secret=SecretStr(TOKEN),
        bearer_expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


def test_loopback_launcher_forwards_only_validated_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, Any] = {}

    def substitute(app: Any, **kwargs: Any) -> None:
        assert app.state.foundation.configuration.mode == "loopback"
        called.update(kwargs)

    monkeypatch.setattr(launcher, "run", substitute)
    with pytest.raises(ConfigurationError):
        launcher.run_loopback({})
    config = {
        "NCI_API_MODE": "loopback",
        "NCI_API_BUNDLE_ROOT": "/not-a-real-research-release",
        "NCI_API_RELEASE_SHA256": "a" * 64,
        "NCI_API_BEARER_SECRET": TOKEN,
        "NCI_API_BEARER_EXPIRES_AT": (datetime.now(UTC) + timedelta(hours=1))
        .isoformat()
        .replace("+00:00", "Z"),
    }
    with pytest.raises(ConfigurationError):
        launcher.run_loopback(config | {"NCI_API_BIND_HOST": "0.0.0.0"})
    assert not called
    launcher.run_loopback(config)
    assert (called["host"], called["port"]) == ("127.0.0.1", 8000)
    assert called["proxy_headers"] is False
    assert called["access_log"] is False
    assert called["log_config"]["loggers"][LOGGER_NAME]["level"] == "INFO"
    assert TOKEN not in str(called)


def test_request_auth_and_audit_redact_inputs(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app(loopback_settings())
    with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
        with TestClient(
            app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 1000)
        ) as client:
            valid = ("Authorization", f"Bearer {TOKEN}")
            for headers in (
                [],
                [("Authorization", "Bearer wrong")],
                [valid, valid],
                [("Authorization", f"Bearer\t{TOKEN}")],
            ):
                response = client.get(PATH + "?client_id=private-context", headers=headers)
                assert response.status_code == 401
                assert response.json()["code"] == "AUTH_REQUIRED"
            response = client.get(PATH, headers=[valid])
            assert response.status_code == 503
            request_id = response.headers["X-Request-ID"]

            class ExpiredClock:
                @staticmethod
                def now(tz: object) -> datetime:
                    return datetime.now(UTC) + timedelta(hours=2)

            monkeypatch.setattr(security, "datetime", ExpiredClock)
            assert client.get(PATH, headers=[valid]).status_code == 401

    events = [
        json.loads(record.getMessage()) for record in caplog.records if record.name == LOGGER_NAME
    ]
    selected = next(item for item in events if item.get("request_id") == request_id)
    assert selected["category"] == "EVIDENCE_UNAVAILABLE"
    assert selected["operation_id"] == "getResearchEvaluation"
    assert selected["status"] == 503
    assert UUID(selected["request_id"]).version == 4
    assert selected["duration_ms"] >= 0
    for private in (TOKEN, "private-context", "/not-a-real-research-release", PATH):
        assert private not in caplog.text


def test_loopback_rejects_nonlocal_peer_and_forwarding() -> None:
    with TestClient(
        create_app(loopback_settings()),
        base_url="http://127.0.0.1:8000",
        client=("192.0.2.1", 1000),
    ) as remote:
        assert remote.get("/health/live").status_code == 400
    with TestClient(
        create_app(loopback_settings()),
        base_url="http://127.0.0.1:8000",
        client=("127.0.0.1", 1000),
    ) as local:
        assert local.get("/health/live", headers={"Forwarded": "for=127.0.0.1"}).status_code == 400
