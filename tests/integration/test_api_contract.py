"""Pin the stable OpenAPI surface and closed wire shapes."""

from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx2")

from fastapi.testclient import TestClient  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from nowa_customer_intelligence.api.application import create_app  # noqa: E402
from nowa_customer_intelligence.api.contracts import ClvMetrics  # noqa: E402

OPERATIONS = {
    "/health/live": "getLiveness",
    "/health/ready": "getReadiness",
    "/v1/research/capabilities": "listResearchCapabilities",
    "/v1/research/models": "listResearchModels",
    "/v1/research/models/{model_id}": "getResearchModel",
    "/v1/research/models/{model_id}/evaluation": "getResearchEvaluation",
    "/v1/research/models/{model_id}/limitations": "getResearchLimitations",
    "/v1/research/models/{model_id}/explainability": "getResearchExplainability",
    "/v1/research/segmentation/status": "getResearchSegmentationStatus",
}


def resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    if "$ref" not in node:
        return node
    name = node["$ref"].rsplit("/", 1)[1]
    component: dict[str, Any] = schema["components"]["schemas"][name]
    return component


def test_openapi_matches_canonical_research_contract() -> None:
    schema = create_app().openapi()
    assert schema == create_app().openapi()
    assert schema["info"]["version"] == "1.0.0"
    assert set(schema["paths"]) == set(OPERATIONS)
    assert schema["components"]["securitySchemes"] == {
        "ResearchBearer": {"type": "http", "scheme": "bearer"},
    }
    for path, name in OPERATIONS.items():
        methods = schema["paths"][path]
        assert set(methods) == {"get"}
        operation = methods["get"]
        assert operation["operationId"] == name
        assert "requestBody" not in operation
        responses = operation["responses"]
        expected = {"200", "400", "405", "413", "414", "422", "431", "500"}
        if path.startswith("/v1/"):
            expected |= {"401", "403", "503"}
            assert operation["security"] == [{"ResearchBearer": []}]
            assert "research:read" in operation["description"]
            assert "WWW-Authenticate" in responses["401"]["headers"]
        else:
            assert not operation.get("security")
            if path == "/health/ready":
                expected.add("503")
        if "{model_id}" in path:
            expected.add("404")
            (parameter,) = operation["parameters"]
            assert parameter["in"] == "path" and parameter["required"]
            assert parameter["name"] == "model_id"
            assert parameter["schema"]["maxLength"] == 48
            assert "pattern" in parameter["schema"]
        else:
            assert not operation.get("parameters")
        assert set(responses) == expected
        for status in expected:
            assert {"X-Request-ID", "Cache-Control"} <= responses[status]["headers"].keys()
            shape = responses[status]["content"]["application/json"]["schema"]
            if status != "200":
                assert shape["$ref"].endswith("/ApiError")
                example = responses[status]["content"]["application/json"]["example"]
                assert example["schema_version"] == 1 and "request_id" in example
        assert "Allow" in responses["405"]["headers"]

    for suffix in ("evaluation", "explainability"):
        response = schema["paths"][f"/v1/research/models/{{model_id}}/{suffix}"]["get"][
            "responses"
        ]["200"]
        shape = resolve(schema, response["content"]["application/json"]["schema"])
        variants = [resolve(schema, member) for member in shape["oneOf"]]
        assert len(variants) == 2
        assert all(member["additionalProperties"] is False for member in variants)

    metrics = schema["components"]["schemas"]["ClvMetrics"]
    assert metrics["additionalProperties"] is False
    assert "r2" in metrics["required"] and "r2_unavailable_reason" not in metrics["required"]
    assert metrics["properties"]["mae_gbp"]["type"] == "string"
    assert metrics["properties"]["mae_gbp"]["pattern"] == r"^[0-9]{1,12}[.][0-9]{2}$"
    serialised_schema = str(schema)
    assert "bundle_root" not in serialised_schema
    assert "bearer_secret" not in serialised_schema


def test_money_is_precise_and_unknown_r2_has_a_reason() -> None:
    data: dict[str, object] = {
        "mae_gbp": "10.225",
        "rmse_gbp": "15.235",
        "median_ae_gbp": "0.004",
        "signed_bias_gbp": "-2.145",
        "r2": None,
        "r2_unavailable_reason": "undefined",
    }
    result = ClvMetrics.model_validate(data).model_dump(mode="json", exclude_unset=True)
    assert result == {
        "mae_gbp": "10.22",
        "rmse_gbp": "15.24",
        "median_ae_gbp": "0.00",
        "signed_bias_gbp": "-2.14",
        "r2": None,
        "r2_unavailable_reason": "undefined",
    }
    for faulty in (
        {"mae_gbp": 10.25},
        {"mae_gbp": "-0.004"},
        {"mae_gbp": "-1.00"},
        {"rmse_gbp": "NaN"},
        {"r2_unavailable_reason": None},
        {"r2": 0.1},
        {"unrecognised": "field"},
    ):
        with pytest.raises(ValidationError):
            ClvMetrics.model_validate(data | faulty)


def test_http_openapi_and_unapproved_methods_are_disabled() -> None:
    with TestClient(create_app()) as client:
        for path in ("/openapi.json", "/docs", "/redoc", "/v1/research/score"):
            assert client.get(path).status_code == 404
        for method in ("POST", "PUT", "HEAD", "OPTIONS"):
            response = client.request(method, "/health/live")
            assert response.status_code == 405
            assert response.headers["Allow"] == "GET"
