"""Offline tests for the independently pinned research catalogue."""

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx2")

from fastapi.testclient import TestClient  # noqa: E402

from nowa_customer_intelligence.api.application import create_app  # noqa: E402
from nowa_customer_intelligence.api.configuration import ApiConfiguration  # noqa: E402
from nowa_customer_intelligence.api.contracts import CHURN_SHA, CLV_SHA  # noqa: E402
from nowa_customer_intelligence.api.research import VerifiedCatalogue  # noqa: E402
from nowa_customer_intelligence.api.security import ResearchPrincipal  # noqa: E402

PRINCIPAL = ResearchPrincipal("research:read", "fieldwise-fictional")


def digest(value: bytes) -> str:
    return sha256(value).hexdigest()


def encode(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()


def method(scale: str, name: str, unit: str, terms: list[str]) -> dict:
    return {
        "method": name,
        "output_scale": scale,
        "unit": unit,
        "training_background_accounts": 8,
        "global_validation_accounts": 6,
        "reconciled_rows": 7,
        "failures": 0,
        "tolerance": 0.0001,
        "max_error": 0.0,
        "terms": [{"term_id": term, "mean_absolute": 0.1} for term in terms],
    }


def write_fixture(tmp_path: Path) -> tuple[Path, dict]:
    shared = {
        "data_origin": "fieldwise-fictional",
        "evaluation_status": "experimental-development-validation",
        "production_approved": False,
    }
    churn = {
        **shared,
        "model_id": "churn",
        "display_name": "Contractual subscription churn",
        "model_family": "HistGradientBoostingClassifier",
        "model_version": CHURN_SHA,
        "entity": "subscription-episode",
        "target": "contractual-churn",
        "horizon_value": 30,
        "horizon_unit": "day",
        "prediction_unit": "class-1-probability",
        "limitation_ids": [
            "synthetic-only",
            "weak-churn-validation",
            "uncalibrated-for-operational-use",
            "no-operational-risk-bands",
        ],
    }
    clv = {
        **shared,
        "model_id": "clv",
        "display_name": "Six-month billed value",
        "model_family": "HistGradientBoostingRegressor",
        "model_version": CLV_SHA,
        "entity": "customer-account",
        "target": "future_6m_issued_gbp",
        "horizon_value": 6,
        "horizon_unit": "calendar-month",
        "prediction_unit": "gross-issued-gbp",
        "limitation_ids": ["synthetic-only", "billed-value-proxy", "no-operational-use"],
    }
    evaluation = {"partition": "development-validation", "observations": 16, "accounts": 12}
    churn_eval: dict[str, Any] = dict(
        evaluation,
        model=churn,
        metrics={
            "average_precision": 0.1,
            "roc_auc": 0.2,
            "precision": 0.1,
            "recall": 0.2,
            "brier": 0.3,
            "research_threshold": 0.4,
            "positive_accounts": 3,
            "false_positives": 8,
        },
    )
    clv_eval: dict[str, Any] = dict(
        evaluation,
        model=clv,
        metrics={
            "mae_gbp": "10.00",
            "rmse_gbp": "12.00",
            "median_ae_gbp": "2.00",
            "signed_bias_gbp": "-1.00",
            "r2": None,
            "r2_unavailable_reason": "undefined",
        },
    )
    for record in (churn_eval, clv_eval):
        record["limitations"] = [
            {"id": key, "severity": "restriction", "description": "Synthetic test fixture."}
            for key in record["model"]["limitation_ids"]
        ]
    xai_limits = ["model-behaviour-only", "background-dependent", "no-causal-effects"]
    projections = {
        "churn-evaluation": ("nci-phase06-v1", churn, churn_eval),
        "clv-evaluation": ("fieldwise-clv-v1", clv, clv_eval),
        "churn-explainability": (
            "phase09-explainability-v1",
            churn,
            {
                "methods": [
                    method(
                        "class-1-probability",
                        "tree-shap-interventional",
                        "probability",
                        ["episode_age_days", "latest_sessions", "expected_usage_months"],
                    ),
                    method("class-1-log-odds", "tree-shap-interventional", "log-odds", []),
                ],
                "limitation_ids": [*xai_limits, "weak-churn-validation"],
            },
        ),
        "clv-explainability": (
            "phase09-explainability-v1",
            clv,
            {
                "methods": [
                    method(
                        "clipped-gross-issued-gbp",
                        "finite-background-block-shapley",
                        "GBP",
                        [
                            "account-lifecycle",
                            "invoice-history-and-cadence",
                            "contract-snapshots",
                            "calendar",
                        ],
                    )
                ],
                "limitation_ids": [*xai_limits, "correlated-billing-fields"],
            },
        ),
        "segmentation-status": (
            "fieldwise-segmentation-v0",
            None,
            {
                "method": "rfm",
                "method_version": "fieldwise-segmentation-v0",
                "data_origin": "fieldwise-fictional",
                "evaluation_scope": "synthetic-development-research",
                "nomination": "none",
                "operational_assignment_available": False,
                "dimensions": ["recency", "frequency", "monetary"],
                "limitation_ids": ["no-nominated-clustering-model"],
            },
        ),
    }
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "release_id": "fixture-v1",
        "audience": "fieldwise-fictional",
        "audited_commit": "a" * 40,
        "members": [],
    }
    for name, (experiment, identity, data) in projections.items():
        payload = encode({"schema_id": "research-projection-v1", "report_id": name, "data": data})
        filename = f"{name}.json"
        (tmp_path / filename).write_bytes(payload)
        member = {
            "report_id": name,
            "basename": filename,
            "experiment_id": experiment,
            "schema_id": "research-projection-v1",
            "sha256": digest(payload),
            "source_report_sha256": "b" * 64,
            "size_bytes": len(payload),
        }
        if identity:
            member.update(model_id=identity["model_id"], model_version=identity["model_version"])
            member["feature_contract_version"] = (
                "fieldwise-episode-features-v1" if name.startswith("churn") else "fieldwise-clv-v1"
            )
        manifest["members"].append(member)
    return tmp_path, manifest


@pytest.fixture
def release(tmp_path: Path) -> tuple[Path, dict]:
    return write_fixture(tmp_path)


def configuration(root: Path, manifest: dict) -> ApiConfiguration:
    raw = encode(manifest)
    (root / "release.json").write_bytes(raw)
    return ApiConfiguration(bundle_root=root, release_sha256=digest(raw))


def test_verified_models_and_immutable_snapshot(release: tuple[Path, dict]) -> None:
    root, manifest = release
    app = create_app(configuration(root, manifest), principal_provider=lambda: PRINCIPAL)
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 200
        catalogue = app.state.foundation.catalogue
        assert isinstance(catalogue, VerifiedCatalogue)
        models = client.get("/v1/research/models").json()
        assert [item["model_id"] for item in models["models"]] == ["churn", "clv"]
        churn = client.get("/v1/research/models/churn").json()["model"]
        assert churn["model_version"] == CHURN_SHA
        assert churn["prediction_unit"] == "class-1-probability"
        assert churn["provenance"]["experiment_id"] == "nci-phase06-v1"
        assert churn["production_approved"] is False
        assert "published_at" not in churn["provenance"]
        clv = client.get("/v1/research/models/clv").json()["model"]
        assert clv["target"] == "future_6m_issued_gbp"
        assert client.get("/v1/research/models/unknown").status_code == 404
        assert client.get("/v1/research/models/BAD").status_code == 422
        assert client.get("/v1/research/models/churn?client_id=other").status_code == 422
        (root / "clv-evaluation.json").write_bytes(b"replaced")
        assert client.get("/v1/research/models").json() == models
        with pytest.raises(ValueError):
            catalogue.cards.models[0].model_id = "clv"  # type: ignore[assignment]
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 503


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "member-digest",
        "manifest-digest",
        "schema",
        "duplicate-key",
        "unexpected-file",
        "symlink",
        "wrong-experiment",
        "wrong-model",
    ],
)
def test_rejects_unverified_release(release: tuple[Path, dict], defect: str) -> None:
    root, manifest = release
    path = root / "churn-evaluation.json"
    config = configuration(root, manifest)
    if defect == "missing":
        path.unlink()
    elif defect == "member-digest":
        path.write_bytes(b"replacement")
    elif defect == "manifest-digest":
        manifest["release_id"] = "substitute"
        (root / "release.json").write_bytes(encode(manifest))
    elif defect == "unexpected-file":
        (root / "extra.json").write_bytes(b"{}")
    elif defect == "symlink":
        target = root / "clv-evaluation.json"
        path.unlink()
        path.symlink_to(target)
    elif defect in {"wrong-experiment", "wrong-model"}:
        key = "experiment_id" if defect == "wrong-experiment" else "model_id"
        manifest["members"][0][key] = "clv"
        config = configuration(root, manifest)
    else:
        if defect == "schema":
            body = json.loads(path.read_bytes())
            body["data"]["customer_id"] = "private"
            raw = encode(body)
        else:
            raw = path.read_bytes().replace(
                b'"report_id":', b'"report_id":"duplicate","report_id":'
            )
        path.write_bytes(raw)
        manifest["members"][0].update(sha256=digest(raw), size_bytes=len(raw))
        config = configuration(root, manifest)
    with TestClient(create_app(config, principal_provider=lambda: PRINCIPAL)) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").json()["code"] == "SERVICE_UNAVAILABLE"
        response = client.get("/v1/research/models")
        assert response.status_code == 503
        assert response.json()["code"] == "EVIDENCE_UNAVAILABLE"
        assert str(root) not in response.text
        assert client.get("/v1/research/models/BAD").status_code == 422


def test_missing_access_hides_resource_status(release: tuple[Path, dict]) -> None:
    root, manifest = release
    with TestClient(create_app(configuration(root, manifest))) as client:
        for suffix in ("churn", "unknown", "BAD"):
            assert client.get(f"/v1/research/models/{suffix}").status_code == 401


def test_research_responses_preserve_scientific_units(release: tuple[Path, dict]) -> None:
    root, manifest = release
    with TestClient(
        create_app(configuration(root, manifest), principal_provider=lambda: PRINCIPAL)
    ) as client:
        prefix = "/v1/research/models"
        churn = client.get(f"{prefix}/churn/evaluation").json()
        assert churn["model"]["entity"] == "subscription-episode"
        assert (churn["model"]["horizon_value"], churn["model"]["horizon_unit"]) == (30, "day")
        assert churn["metrics"]["average_precision"] == 0.1
        assert churn["partition"] == "development-validation"
        clv = client.get(f"{prefix}/clv/evaluation").json()
        assert (clv["model"]["horizon_value"], clv["model"]["horizon_unit"]) == (
            6,
            "calendar-month",
        )
        assert clv["model"]["target"] == "future_6m_issued_gbp"
        assert clv["metrics"]["mae_gbp"] == "10.00"
        assert clv["metrics"]["r2"] is None
        assert clv["metrics"]["r2_unavailable_reason"] == "undefined"
        limitations = client.get(f"{prefix}/churn/limitations").json()
        assert {item["id"] for item in limitations["limitations"]} == set(
            churn["model"]["limitation_ids"]
        )
        churn_xai = client.get(f"{prefix}/churn/explainability").json()
        clv_xai = client.get(f"{prefix}/clv/explainability").json()
        assert [item["output_scale"] for item in churn_xai["methods"]] == [
            "class-1-probability",
            "class-1-log-odds",
        ]
        assert clv_xai["methods"][0]["method"] == "finite-background-block-shapley"
        assert len(clv_xai["methods"][0]["terms"]) == 4
        assert clv_xai["methods"][0]["unit"] == "GBP"
        assert clv_xai["provenance"]["experiment_id"] == "phase09-explainability-v1"
        assert clv_xai["causal"] is False and "cases" not in clv_xai
        segments = client.get("/v1/research/segmentation/status").json()
        assert segments["nomination"] == "none"
        assert segments["operational_assignment_available"] is False
        assert "feature_contract_version" not in segments["provenance"]
        assert "assignments" not in segments


@pytest.mark.parametrize(
    "path",
    [
        "/v1/research/models/churn/evaluation",
        "/v1/research/models/clv/limitations",
        "/v1/research/models/churn/explainability",
        "/v1/research/segmentation/status",
    ],
)
def test_research_summary_security_and_evidence_precedence(path: str) -> None:
    with TestClient(create_app()) as client:
        assert client.get(path).status_code == 401
    with TestClient(create_app(principal_provider=lambda: PRINCIPAL)) as client:
        assert client.get(path + "?client_id=private").status_code == 422
        response = client.get(path)
        assert response.status_code == 503
        assert response.json()["code"] == "EVIDENCE_UNAVAILABLE"


@pytest.mark.parametrize(
    "name,field,value",
    [
        ("clv-evaluation", "target", "profit"),
        ("clv-evaluation", "horizon_value", 6.0),
        ("churn-evaluation", "production_approved", 0),
        ("churn-evaluation", "entity", "customer-account"),
    ],
)
def test_incompatible_scientific_identity_blocks_publication(
    release: tuple[Path, dict],
    name: str,
    field: str,
    value: str,
) -> None:
    root, manifest = release
    path = root / f"{name}.json"
    data = json.loads(path.read_bytes())
    data["data"]["model"][field] = value
    content = encode(data)
    path.write_bytes(content)
    member = next(item for item in manifest["members"] if item["report_id"] == name)
    member.update(sha256=digest(content), size_bytes=len(content))
    with TestClient(
        create_app(configuration(root, manifest), principal_provider=lambda: PRINCIPAL)
    ) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503


def test_restart_failure_and_catalogue_isolation(tmp_path: Path) -> None:
    first_root, second_root = (tmp_path / name for name in ("first", "second"))
    first_root.mkdir()
    second_root.mkdir()
    _, first_manifest = write_fixture(first_root)
    _, second_manifest = write_fixture(second_root)
    first_manifest["release_id"] = "fixture-first"
    first_manifest["published_at"] = "2026-11-21T12:00:00Z"
    second_manifest["release_id"] = "fixture-second"
    first_config = configuration(first_root, first_manifest)
    second_config = configuration(second_root, second_manifest)
    first = create_app(first_config, principal_provider=lambda: PRINCIPAL)
    second = create_app(second_config, principal_provider=lambda: PRINCIPAL)
    path = "/v1/research/capabilities"
    with TestClient(first) as first_client, TestClient(second) as second_client:
        assert first_client.get(path).json()["evidence_version"] == "fixture-first"
        assert second_client.get(path).json()["evidence_version"] == "fixture-second"
        card = first_client.get("/v1/research/models/churn").json()["model"]
        assert card["provenance"]["published_at"] == first_manifest["published_at"]
        (first_root / "release.json").write_bytes(b"corrupt")
        assert first_client.get(path).status_code == second_client.get(path).status_code == 200
    with TestClient(first) as first_client, TestClient(second) as second_client:
        assert first_client.get("/health/live").status_code == 200
        assert first_client.get(path).status_code == 503
        assert second_client.get(path).json()["evidence_version"] == "fixture-second"
    configuration(first_root, first_manifest)
    with TestClient(first) as restarted:
        assert restarted.get(path).json()["evidence_version"] == "fixture-first"
