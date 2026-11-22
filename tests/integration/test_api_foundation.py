"""Offline ASGI tests for the Phase 10 application foundation."""

import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, tzinfo
from pathlib import Path
from typing import Annotated
from uuid import UUID

import pytest
from pydantic import SecretStr

pytest.importorskip("fastapi")
pytest.importorskip("httpx2", reason="WP-10.3 ASGI tests require the API test environment")

from fastapi import Depends, HTTPException, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from nowa_customer_intelligence import __version__  # noqa: E402
from nowa_customer_intelligence.api.application import LifecycleError, create_app  # noqa: E402
from nowa_customer_intelligence.api.configuration import (  # noqa: E402
    ApiConfiguration,
    ConfigurationError,
)
from nowa_customer_intelligence.api.dependencies import (  # noqa: E402
    ResearchCatalogue,
    get_foundation_state,
    require_catalogue,
)


def test_factory_is_independent_and_has_approved_metadata() -> None:
    configuration = ApiConfiguration(log_level="WARNING")
    app = create_app(configuration)
    other = create_app()
    assert app.title == "Nowa Customer Intelligence — Internal Research & Analytics API"
    assert app.version == "1.0.0"
    assert app.state.foundation.service.service_version == __version__
    assert app.state.foundation.configuration == configuration
    assert other.state.foundation.configuration.log_level == "INFO"
    assert app.state.foundation is not other.state.foundation
    assert type(app.routes) is list and app.routes == []
    assert app.openapi()["paths"] == {}
    assert not app.router.redirect_slashes


def test_factory_revalidates_settings_before_exposing_app() -> None:
    unvalidated = ApiConfiguration().model_copy(update={"bind_host": "0.0.0.0"})
    with pytest.raises(ConfigurationError):
        create_app(unvalidated)


def test_factory_starts_no_listener_and_imports_no_research_stack() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import socket
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from pydantic import SecretStr

def refuse(*args, **kwargs):
    raise AssertionError("Factory attempted socket I/O")

socket.socket.bind = refuse
socket.socket.connect = refuse
from nowa_customer_intelligence.api.application import create_app
from nowa_customer_intelligence.api.configuration import ApiConfiguration
demo = ApiConfiguration(
    mode="loopback",
    bundle_root=Path("/fixtures/research"),
    release_sha256="a" * 64,
    bearer_secret=SecretStr("fixture_secret_for_validation_123456"),
    bearer_expires_at=datetime.now(UTC) + timedelta(hours=1),
)
assert create_app().routes == create_app(demo).routes == []
for name in ("uvicorn", "pandas", "numpy", "sklearn", "joblib", "shap"):
    assert name not in sys.modules, name
""",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[2] / "src",
        timeout=15,
    )


@dataclass(frozen=True)
class CatalogueFixture:
    release_id: str


def test_lifespan_owns_injected_dependency_and_clears_state() -> None:
    events: list[str] = []
    fixture = CatalogueFixture("test-release")

    @asynccontextmanager
    async def catalogue(settings: ApiConfiguration) -> AsyncIterator[ResearchCatalogue]:
        assert settings.log_level == "WARNING"
        events.append("start")
        yield fixture
        events.append("stop")

    app = create_app(ApiConfiguration(log_level="WARNING"), catalogue_lifespan=catalogue)
    other = create_app()
    assert events == []
    assert app.state.foundation.catalogue is None
    for _ in range(2):
        with TestClient(app):
            assert app.state.foundation.catalogue is fixture
            assert other.state.foundation.catalogue is None
        assert app.state.foundation.catalogue is None
    assert events == ["start", "stop", "start", "stop"]


@pytest.mark.parametrize("inject_unavailable", [False, True])
def test_unavailable_catalogue_is_not_fabricated(
    inject_unavailable: bool,
) -> None:
    @asynccontextmanager
    async def unavailable(settings: ApiConfiguration) -> AsyncIterator[None]:
        yield None

    app = create_app(catalogue_lifespan=unavailable if inject_unavailable else None)

    @app.get("/fixture")
    async def fixture(
        catalogue: Annotated[ResearchCatalogue, Depends(require_catalogue)],
    ) -> dict[str, str]:
        return {"release": catalogue.release_id}

    with TestClient(app) as client:
        assert app.state.foundation.catalogue is None
        response = client.get("/fixture")
        assert response.status_code == 503
        assert response.json()["code"] == "EVIDENCE_UNAVAILABLE"
    assert app.state.foundation.catalogue is None


@pytest.mark.parametrize("fail_on_start", [True, False])
def test_unexpected_lifespan_failure_is_sanitised(fail_on_start: bool) -> None:
    @asynccontextmanager
    async def broken(settings: ApiConfiguration) -> AsyncIterator[ResearchCatalogue]:
        if not fail_on_start:
            yield CatalogueFixture("test-release")
        raise RuntimeError("/private/internal/path: fixture-secret-value")

    app = create_app(catalogue_lifespan=broken)
    with pytest.raises(LifecycleError, match="API dependency failed") as raised, TestClient(app):
        assert not fail_on_start
    assert raised.value.__context__ is None
    assert app.state.foundation.catalogue is None


@pytest.mark.parametrize(
    "path",
    [
        "/health/live",
        "/health/ready",
        "/v1/research/capabilities",
        "/v1/research/models",
        "/v1/research/models/churn",
        "/v1/research/models/clv/evaluation",
        "/v1/research/segmentation/status",
        "/v1/internal/clv/predict",
        "/v1/score",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    ],
)
def test_foundation_has_no_listener_routes(path: str) -> None:
    with TestClient(create_app()) as client:
        response = client.get(path, headers={"X-Request-ID": "untrusted"})
    body = response.json()
    assert response.status_code == 404
    assert body["code"] == "NOT_FOUND"
    assert UUID(response.headers["X-Request-ID"]).version == 4
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert body["schema_version"] == 1
    assert response.headers["Cache-Control"] == "no-store"
    assert "untrusted" not in response.text


def test_http_failures_are_sanitised_without_rethrowing(caplog: pytest.LogCaptureFixture) -> None:
    app = create_app()
    private = "/private/internal/path: fixture-secret-value"

    @app.get("/fixture/unauthenticated")
    async def unauthenticated() -> None:
        raise HTTPException(401, detail=private, headers={"X-Private": private})

    @app.get("/fixture/forbidden")
    async def forbidden() -> None:
        raise HTTPException(403, detail=private)

    @app.get("/fixture/items/{item}")
    async def item(item: int, request: Request) -> dict[str, str]:
        return {"title": get_foundation_state(request).service.title}

    @app.get("/fixture/internal")
    async def internal() -> None:
        raise RuntimeError(private)

    with TestClient(app) as client:
        cases = [
            (client.get("/fixture/unauthenticated"), 401, "AUTH_REQUIRED"),
            (client.get("/fixture/forbidden"), 403, "FORBIDDEN"),
            (client.get("/fixture/items/fixture-secret-value"), 422, "VALIDATION_ERROR"),
            (client.post("/fixture/items/1"), 405, "METHOD_NOT_ALLOWED"),
            (client.get("/fixture/internal"), 500, "INTERNAL_ERROR"),
        ]
        assert client.get("/fixture/items/1").json() == {"title": app.title}

    for response, status, code in cases:
        assert response.status_code == status
        payload = response.json()
        assert payload["code"] == code
        assert payload["request_id"] == response.headers["X-Request-ID"]
        assert "fixture-secret-value" not in response.text
        assert "/private/internal/path" not in response.text
        assert "Traceback" not in response.text
        assert "X-Private" not in response.headers
    assert len({response.headers["X-Request-ID"] for response, _, _ in cases}) == len(cases)
    assert cases[0][0].headers["WWW-Authenticate"] == "Bearer"
    assert cases[3][0].headers["Allow"] == "GET"
    assert private not in caplog.text


def test_expired_loopback_settings_fail_before_a_dependency_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_now = datetime(2026, 11, 21, 12, tzinfo=UTC)

    class Clock:
        current = fixed_now

        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            return cls.current

    monkeypatch.setattr("nowa_customer_intelligence.api.configuration.datetime", Clock)
    demo = ApiConfiguration(
        mode="loopback",
        bundle_root=Path("/fixtures/research"),
        release_sha256="a" * 64,
        bearer_secret=SecretStr("fixture_secret_for_validation_123456"),
        bearer_expires_at=fixed_now + timedelta(hours=1),
    )
    started: list[str] = []

    @asynccontextmanager
    async def catalogue(settings: ApiConfiguration) -> AsyncIterator[None]:
        started.append(settings.mode)
        yield None

    app = create_app(demo, catalogue_lifespan=catalogue)
    Clock.current = fixed_now + timedelta(hours=1)
    with pytest.raises(ConfigurationError, match="expiry"), TestClient(app):
        pytest.fail("Expired loopback credentials permitted startup.")
    assert not started
