"""Check the frozen segmentation protocol using small controlled inputs."""

from contextlib import contextmanager
from decimal import Decimal
from json import loads
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

from nowa_customer_intelligence.models.segmentation import research
from nowa_customer_intelligence.models.segmentation.clustering import (
    Fit,
    evaluate,
    fit_candidate,
    fit_preprocessing,
)
from nowa_customer_intelligence.models.segmentation.evaluation import (
    FrozenAssignment,
    migration,
    profiles,
    stability,
    stability_passes,
)
from nowa_customer_intelligence.models.segmentation.population import choose_dates
from nowa_customer_intelligence.models.segmentation.protocol import PROTOCOL
from nowa_customer_intelligence.models.segmentation.rfm import fit_score_rule


@pytest.fixture
def inputs() -> pd.DataFrame:
    size = 18
    return pd.DataFrame(
        {
            "recency_days": np.r_[np.arange(size), 100 + np.arange(size)],
            "frequency": [3] * size + [12] * size,
            "monetary_gbp": [Decimal("100.30")] * size + [Decimal("948")] * size,
            "tenure_days": np.tile(np.arange(size) + 400, 2),
            "active_episodes": [1] * (2 * size),
            "cadence": ["annual"] * size + ["monthly"] * size,
            "disposition": ["eligible"] * (2 * size),
        },
        index=[f"account-{number:02}" for number in range(2 * size)],
    )


@pytest.fixture(autouse=True)
def single_thread():
    with threadpool_limits(limits=1):
        yield


def test_tie_pooling_and_boundary_equality() -> None:
    rule = fit_score_rule([1] * 19 + [5] * 5 + [9], reverse=True)
    assert rule.thresholds == (1,)
    assert [rule.apply(value) for value in (0, 1, 2, 200)] == [3, 3, 1, 1]
    assert fit_score_rule([1] * 40).apply(100) == 2


def test_coverage_only_chronological_fallback() -> None:
    good = {"eligible": 200, "cadence_eligible": {"monthly": 130, "annual": 70}}
    bad = {"eligible": 199, "cadence_eligible": {"monthly": 129, "annual": 70}}
    dates = {
        "2023-03-31": bad,
        "2023-04-30": good,
        "2023-06-30": good,
        "2023-07-31": good,
        "2023-12-31": good,
        "2024-03-31": good,
    }
    assert choose_dates(dates) == ("2023-04-30", "2023-07-31", "2024-03-31")
    with pytest.raises(ValueError, match="chronologically"):
        choose_dates({"2023-03-31": bad, "2024-03-31": good})


def test_standardisation_block_weights_constants_and_unknown_categories(inputs) -> None:
    blocks = {
        "financial": ("recency_days", "frequency"),
        "contractual": ("tenure_days", "active_episodes", "cadence"),
    }
    pipeline = fit_preprocessing(inputs, blocks)
    coordinates = pipeline.transform(inputs)
    assert pipeline.dropped == ("active_episodes",)
    np.testing.assert_allclose(coordinates[:, :2].std(axis=0), [1 / np.sqrt(2)] * 2)
    assert coordinates[0, -2] == pytest.approx(1 / np.sqrt(3))
    assert coordinates[0, -1] == 0
    later = inputs.iloc[:3].copy()
    later.loc[later.index[0], "cadence"] = "mixed"
    later.loc[later.index[1], "recency_days"] = np.nan
    assert pipeline.eligible(later).tolist() == [False, False, True]
    with pytest.raises(ValueError, match="Unassignable"):
        pipeline.transform(later)
    assert pipeline.transform(later.iloc[2:]).tolist() == coordinates[2:3].tolist()


@pytest.mark.parametrize("family", ["K-Means", "Ward", "GMM"])
def test_repeatable_candidates_and_native_assignment(inputs, family: str) -> None:
    pipeline = fit_preprocessing(inputs, {"financial": ("recency_days", "frequency")})
    points = pipeline.transform(inputs)
    first = fit_candidate(family, 2, points, 42)
    second = fit_candidate(family, 2, points, 42)
    assert first.converged and adjusted_rand_score(first.labels, second.labels) == 1
    assert evaluate(points, first.labels, 2)["counts"] == [18, 18]
    if family == "Ward":
        assert first.hierarchy.shape == (35, 4)
        with pytest.raises(ValueError, match="frozen assignment"):
            first.assign(points)
    else:
        later = inputs.iloc[[0, -1]].copy()
        later.iloc[0, later.columns.get_loc("disposition")] = "short_history"
        labels, _, _ = FrozenAssignment(pipeline, first).apply(later)
        assert list(labels) == [first.labels[-1]]


def test_metric_values_and_degenerate_labels() -> None:
    point = np.array([[0], [2], [10], [12]])
    labels = np.array([0, 0, 1, 1])
    result = evaluate(point, labels, 2)
    assert result["silhouette_by_group"]["0"][0] == pytest.approx(9 / 11)
    assert result["davies_bouldin"] == pytest.approx(0.2)
    assert result["calinski_harabasz"] == pytest.approx(50)
    assert result["within_sse"] == 4
    degenerate = evaluate(point, np.zeros(4, dtype=int), 2)
    assert degenerate["silhouette"] is None and not degenerate["supported"]


def test_non_converged_is_unassignable() -> None:
    broken = Fit("GMM", 2, False, np.array([0, 1]), None)
    with pytest.raises(ValueError, match="frozen assignment"):
        broken.assign(np.array([[0], [1]]))


def test_stability_shared_accounts_and_label_permutation(inputs, monkeypatch) -> None:
    monkeypatch.setitem(PROTOCOL, "resample_repetitions", 2)
    pipeline = fit_preprocessing(inputs, {"financial": ("recency_days", "frequency")})
    candidate = fit_candidate("K-Means", 2, pipeline.transform(inputs), 42)
    assert adjusted_rand_score(candidate.labels, 1 - candidate.labels) == 1
    diagnostics = stability(inputs, pipeline, candidate)
    assert stability_passes(diagnostics)
    assert [trial["shared_accounts"] for trial in diagnostics["resamples"]] == [29, 29]
    diagnostics["resamples"][0]["complete_workflow"]["ari"] = None
    assert not stability_passes(diagnostics)


def test_profile_gbp_and_migration_denominators(inputs) -> None:
    group = pd.Series([0, 1, 0], index=inputs.index[:3])
    report = profiles(inputs, group)
    assert report["accounts"] == 3 and report["issued_gbp"] == "300.90"
    assert report["groups"]["0"]["issued_gbp"] == "200.60"
    after = inputs.iloc[1:5]
    later = pd.Series([1, 1, 0], index=after.index[:3])
    changes = migration(group, later, inputs.iloc[:3], after)
    assert changes["shared_assigned"] == 2
    assert changes["stable"] == changes["changed"] == 1
    assert changes["newly_visible"] == 2
    assert changes["ceased_to_be_visible"] == 1


def test_reserve_only_gets_count_audit_without_nominee(tmp_path, monkeypatch) -> None:
    from nowa_customer_intelligence.models.segmentation.protocol import RESERVE_SCOPE, RESERVE_SEED

    calls = []
    export = tmp_path / "accepted-export"
    export.mkdir()
    (export / "customers.csv").write_text("fictional_account\n")
    observation = pd.Timestamp("2024-03-31T23:59:59Z").to_pydatetime()
    stages = [
        SimpleNamespace(observation=stamp.to_pydatetime(), eligible=(), frame=lambda: None)
        for stamp in pd.to_datetime(PROTOCOL["preferred_observations"], utc=True)
    ]
    source = SimpleNamespace(
        provenance={}, usage_lag_days=1, ledger=SimpleNamespace(cutoff=observation)
    )

    @contextmanager
    def fake_reference(*, registry_path, master_seed=42, client_scope="default"):
        calls.append((registry_path, master_seed, client_scope))
        registry_path.write_text(f"{master_seed}-{client_scope}")
        yield object(), export

    def reserve_count_only(supplied, when, *, include_usage):
        assert supplied is source and when == observation and not include_usage
        return SimpleNamespace(
            audit=lambda: {
                "eligible": 2,
                "usage_period_counts": {},
                "eligible_with_any_usage": 0,
                "eligible_with_full_usage": 0,
                "cadence_eligible": {},
            }
        )

    def no_model_scoring(*args):
        pytest.fail("Reserve or temporal scoring ran without a nominee.")

    monkeypatch.setattr(research, "fieldwise_reference", fake_reference)
    monkeypatch.setattr(research.SourceEvidence, "from_verified_reference", lambda _: source)
    monkeypatch.setattr(research, "development_populations", lambda _: (stages, []))
    monkeypatch.setattr(research, "behaviour_gate", lambda *args: {"passed": False})
    rule = fit_score_rule([1] * 40)
    monkeypatch.setattr(
        research, "fit_references", lambda _: research.ReferenceScores((rule,) * 3, {})
    )
    monkeypatch.setattr(research, "_fit_all", lambda *args: ({}, [{"gates": ["support"]}], {}, []))
    monkeypatch.setattr(research, "reference_report", lambda *args: [])
    monkeypatch.setattr(research, "observe", reserve_count_only)
    monkeypatch.setattr(research, "_evaluate_frozen", no_model_scoring)

    workspace = tmp_path / "review"
    research.run(workspace)
    assert calls[0][0] != calls[1][0]
    assert calls[1][1:] == (RESERVE_SEED, RESERVE_SCOPE)
    assert (workspace / "reserve/source/customers.csv").is_file()
    assert not (workspace / "reserve/evaluation-started.json").exists()
    assert research.load_report(workspace)["reserve"]["status"] == "unscored_no_nominee"
    proof = loads((workspace / "reserve/manifest.json").read_text())
    assert proof["registry_sha256"] == research.digest(workspace / "reserve/registry.sqlite")
    with pytest.raises(FileExistsError):
        research.run(workspace)
    (workspace / "report.json").write_text("{}")
    with pytest.raises(ValueError, match="Integrity check failed"):
        research.load_report(workspace)


def test_phase08_workspace_is_distinct_from_earlier_research() -> None:
    folder = research.DEFAULT_WORKSPACE
    assert folder == Path("data/processed/phase08-segmentation-research")
    assert PROTOCOL["reserve_seed"] not in {42, 731, 2027}
