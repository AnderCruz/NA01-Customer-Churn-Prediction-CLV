"""Check health and protected capabilities using isolated ASGI evidence doubles."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import SecretStr

pytest.importorskip("fastapi")
pytest.importorskip("httpx2")

from fastapi.testclient import TestClient  # noqa: E402

from nowa_customer_intelligence.api.application import create_app  # noqa: E402
from nowa_customer_intelligence.api.configuration import ApiConfiguration  # noqa: E402
from nowa_customer_intelligence.api.dependencies import CatalogueLifespan, ResearchCatalogue  # noqa: E402
from nowa_customer_intelligence.api.security import ResearchPrincipal  # noqa: E402

CAPABILITIES = "/v1/research/capabilities"
PRINCIPAL = ResearchPrincipal("research:read", "fieldwise-fictional")
TOKEN = "synthetic_token_for_offline_checks_1234"


@dataclass(frozen=True)
class Fixture:
    release_id: str


def fixture_lifespan(release_id: str) -> CatalogueLifespan:
    @asynccontextmanager
    async def owner(settings: ApiConfiguration) -> AsyncIterator[ResearchCatalogue]:
        yield Fixture(release_id)

    return owner


@pytest.mark.parametrize("release", [None, "invalid release"])
def test_liveness_survives_unavailable_catalogue(release: str | None) -> None:
    app = create_app(
        catalogue_lifespan=fixture_lifespan(release) if release else None,
        principal_provider=lambda: PRINCIPAL,
    )
    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "live"}
        for path, code in (
            ("/health/ready", "SERVICE_UNAVAILABLE"),
            (CAPABILITIES, "EVIDENCE_UNAVAILABLE"),
        ):
            response = client.get(path)
            assert response.status_code == 503
            assert response.json()["code"] == code
            assert response.json()["request_id"] == response.headers["X-Request-ID"]
            assert UUID(response.headers["X-Request-ID"]).version == 4


def test_capabilities_auth_precedes_query_and_evidence() -> None:
    with TestClient(create_app()) as client:
        response = client.get(
            CAPABILITIES + "?client_id=private", headers={"Authorization": f"Bearer {TOKEN}"}
        )
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"
        assert "private" not in response.text
    with TestClient(
        create_app(principal_provider=lambda: ResearchPrincipal("research:read", "wrong"))
    ) as client:
        assert client.get(CAPABILITIES).status_code == 403
    with TestClient(create_app(principal_provider=lambda: PRINCIPAL)) as client:
        assert client.get(CAPABILITIES + "?client_id=private").status_code == 422


def test_authorised_capabilities_contract_and_schema() -> None:
    app = create_app(
        catalogue_lifespan=fixture_lifespan("test-bundle"), principal_provider=lambda: PRINCIPAL
    )
    with TestClient(app) as client:
        assert client.get("/health/ready").json() == {"status": "ready"}
        assert client.get(CAPABILITIES).json() == {
            "api_version": "v1",
            "service_version": app.state.foundation.service.service_version,
            "schema_version": 1,
            "evidence_version": "test-bundle",
            "capabilities": [
                {"capability_id": key, "status": "available"}
                for key in (
                    "models",
                    "evaluation",
                    "limitations",
                    "explainability",
                    "segmentation-status",
                )
            ],
        }
    schema = app.openapi()
    assert schema["paths"][CAPABILITIES]["get"]["security"] == [{"ResearchBearer": []}]
    assert schema["paths"]["/health/live"]["get"].get("security", []) == []


def test_loopback_requires_exact_authority_and_bearer() -> None:
    app = create_app(
        ApiConfiguration(
            mode="loopback",
            bundle_root=Path("/test/bundle"),
            release_sha256="a" * 64,
            bearer_secret=SecretStr(TOKEN),
            bearer_expires_at=datetime.now(UTC) + timedelta(hours=1),
        ),
        catalogue_lifespan=fixture_lifespan("test-bundle"),
    )
    with TestClient(app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 1234)) as client:
        assert client.get("/health/live").status_code == 200
        assert (
            client.get(CAPABILITIES, headers={"Authorization": f"bEaReR {TOKEN}"}).status_code
            == 200
        )
        assert (
            client.get(CAPABILITIES, headers={"Authorization": f"Bearer  {TOKEN}"}).status_code
            == 401
        )
        assert (
            client.get(CAPABILITIES, headers={"Authorization": f"Bearer {TOKEN}x"}).status_code
            == 401
        )
        assert client.get("/health/live", headers={"Host": "invalid"}).status_code == 400


def test_transport_rejects_oversized_or_unexpected_requests() -> None:
    with TestClient(create_app()) as client:
        live = "/health/live"
        assert client.get(live + "?x=1").status_code == 422
        assert client.get(live + "?" + "a" * 2048).status_code == 414
        assert client.get(live, headers={"X-Filler": "a" * 8192}).status_code == 431
        assert client.request("GET", live, content=b"a" * 1025).status_code == 413
        assert client.request("GET", live, content=b"a").status_code == 400
        assert client.get(live, headers={"X-Forwarded-For": "127.0.0.1"}).status_code == 400
