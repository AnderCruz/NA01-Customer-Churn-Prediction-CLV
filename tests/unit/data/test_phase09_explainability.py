"""Deterministic Phase 09 controls on bounded offline fixtures."""

from hashlib import sha256
from itertools import permutations
from json import dumps
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import MissingIndicator, SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from nowa_customer_intelligence.explainability import frozen, methods, research


def test_transformed_positions_include_indicators_and_filter_constants():
    command = Pipeline(
        [
            (
                "prepare",
                ColumnTransformer(
                    [
                        (
                            "numeric",
                            Pipeline([("median", SimpleImputer(strategy="median"))]),
                            ["usage"],
                        ),
                        ("missing", MissingIndicator(features="all"), ["usage"]),
                        (
                            "category",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                            ["cadence", "plan"],
                        ),
                    ]
                ),
            ),
            ("filter", VarianceThreshold()),
            ("regressor", LinearRegression()),
        ]
    )
    table = pd.DataFrame(
        {
            "usage": [1.0, np.nan, 3.0],
            "cadence": ["monthly", "annual", "monthly"],
            "plan": ["launch"] * 3,
        }
    )
    command.fit(table, [1.0, 2.0, 3.0])
    before, kept = frozen.feature_lineage(command)
    assert before.original.tolist() == ["usage", "usage", "cadence", "cadence", "plan"]
    assert kept.original.tolist() == ["usage", "usage", "cadence", "cadence"]
    assert kept.component.iloc[1] == "missing indicator"
    assert before.loc[~before.retained, "original"].tolist() == ["plan"]
    values = methods.Attribution(
        tuple(kept.transformed),
        np.array([[2.0, -1.0, 3.0, -2.0]]),
        np.array([4.0]),
        np.array([6.0]),
    )
    grouped = methods.group_transformed(values, kept.original.tolist())
    assert grouped.columns == ("usage", "cadence")
    np.testing.assert_array_equal(grouped.values, [[1.0, 1.0]])
    assert grouped.reconciliation(1e-12)["failures"] == 0


def test_prediction_wrappers_preserve_positive_label_and_clip():
    predictor = SimpleNamespace(
        feature_names_in_=["value"],
        classes_=[1, 0],
        decision_function=lambda f: f.value.to_numpy(),
        predict_proba=lambda f: np.column_stack((expit(f.value), 1 - expit(f.value))),
        predict=lambda f: f.value.to_numpy(),
    )
    frame = pd.DataFrame({"value": [-2.0, 3.0]})
    predictors = SimpleNamespace(pipeline=predictor, name="churn")
    np.testing.assert_allclose(
        frozen.FrozenModel.predict(predictors, frame, output="final"), expit(frame.value)
    )
    np.testing.assert_array_equal(
        frozen.FrozenModel.predict(predictors, frame, output="raw"), frame.value
    )
    predictors.name = "clv"
    np.testing.assert_array_equal(
        frozen.FrozenModel.predict(predictors, frame, output="final"), [0, 3]
    )
    with pytest.raises(ValueError, match="feature order"):
        frozen.FrozenModel.predict(
            predictors, frame.rename(columns={"value": "other"}), output="raw"
        )


def test_frozen_checksum_checked_before_deserialisation(tmp_path, monkeypatch):
    data = b'{"protocol":"example"}'
    (tmp_path / "design.json").write_bytes(data)
    result = tmp_path / "results"
    result.mkdir()
    (result / "selected.joblib").write_bytes(b"wrong binary")
    freeze = {
        "design_sha256": sha256(data).hexdigest(),
        "model_sha256": frozen.MODEL_HASHES["churn"],
    }
    (tmp_path / "frozen.json").write_text(dumps(freeze))

    def prohibit_load(*args):
        pytest.fail("An unverified pickle reached deserialisation.")

    monkeypatch.setattr(frozen, "load", prohibit_load)
    with pytest.raises(ValueError, match="fingerprints"):
        frozen._frozen_pipeline(
            "churn", tmp_path, {"design": {"protocol": "example"}, "frozen": freeze}
        )


def test_forbidden_population_rejected_before_file_access(tmp_path):
    with pytest.raises(ValueError, match="development evidence"):
        frozen.load_development("reserve", tmp_path)


def test_grouped_game_targets_clipped_callable_and_reconciles():
    base = pd.DataFrame({"a": [0.0, 0.0], "b": [0.0, 0.0]})
    example = pd.DataFrame({"a": [1.0], "b": [1.0]})

    def predict(frame):
        return np.maximum(0, -5 + frame.a.to_numpy() * 8 + frame.b.to_numpy() * 2)

    result = methods.grouped_shapley(predict, example, base, {"A": ("a",), "B": ("b",)})
    np.testing.assert_array_equal(result.values, [[4.0, 1.0]])
    assert result.base[0] == 0 and result.predictions[0] == 5
    assert result.reconciliation(1e-12)["max_abs_error"] == 0
    with pytest.raises(ValueError, match="partition"):
        methods.grouped_shapley(predict, example, base, {"A": ("a", "b"), "B": ("b",)})


def test_four_block_game_matches_all_insertion_orders():
    groups = {"A": ("a", "a2"), "B": ("b",), "C": ("c",), "D": ("d",)}
    background = pd.DataFrame({"a": [0, 2], "a2": [1, 3], "b": [2, 1], "c": [1, 3], "d": [0, 2]})
    example = pd.DataFrame({"a": [4], "a2": [6], "b": [3], "c": [2], "d": [4]})

    def predict(frame):
        return np.maximum(0, frame.a * frame.b + frame.a2 + frame.c * frame.d - 8).to_numpy()

    result = methods.grouped_shapley(predict, example, background, groups)
    orders = list(permutations(groups))
    marginals = {name: [] for name in groups}
    for order in orders:
        hybrid = background.copy()
        previous = predict(hybrid).mean()
        for name in order:
            for column in groups[name]:
                hybrid[column] = example[column].iat[0]
            current = predict(hybrid).mean()
            marginals[name].append(current - previous)
            previous = current

    assert result.columns == tuple(groups)
    np.testing.assert_allclose(result.values[0], [np.mean(marginals[name]) for name in groups])
    assert result.base[0] == pytest.approx(1.5)
    assert result.predictions[0] == pytest.approx(18)
    assert result.reconciliation(1e-12)["failures"] == 0


def test_reconciliation_reports_failure_and_rejects_invalid_shapes():
    values = methods.Attribution(
        ("a",), np.array([[2.0], [1.0]]), np.zeros(2), np.array([2.0, 1.002])
    )
    assert values.reconciliation(0.001)["failures"] == 1
    invalid = methods.Attribution(("a",), np.ones((2, 2)), np.zeros(2), np.ones(2))
    with pytest.raises(ValueError, match="dimensions"):
        invalid.reconciliation(0.001)


@pytest.fixture
def trajectories():
    account = ["a", "b", "a", "b", "c", "d"]
    time = pd.to_datetime(
        ["2023-01-01", "2023-01-01", "2023-02-01", "2023-02-01", "2023-01-01", "2023-03-01"],
        utc=True,
    )
    return pd.DataFrame(
        {
            "account": account,
            "time": time,
            "cadence": ["monthly", "annual", "monthly", "annual", "monthly", "monthly"],
        }
    )


def test_background_samples_distinct_accounts_and_is_reproducible(trajectories):
    rows = methods.stratified_sample(trajectories, 4, 909)
    assert rows.equals(methods.stratified_sample(trajectories, 4, 909))
    assert trajectories.loc[rows, "account"].nunique() == 4
    assert set(rows) == {2, 3, 4, 5}


def test_account_permutation_preserves_dates_and_moves_joint_fields(trajectories):
    order, eligible = methods.account_permutation(trajectories, np.random.default_rng(1))
    assert eligible == 2
    assert set(order) == set(range(len(trajectories)))
    assert trajectories.iloc[order].time.tolist() == trajectories.time.tolist()
    frame = pd.DataFrame(
        {"amount": [1.0, 3.0, 2.0, 4.0, 0.0, 5.0], "scale": [2.0, 6.0, 4.0, 8.0, 0.0, 10.0]}
    )
    groups = {"joint": ("amount", "scale")}
    params = dict(repeats=15, seed=912)
    result = methods.permutation_mae(
        lambda values: values.amount.to_numpy(),
        frame,
        trajectories,
        frame.amount.to_numpy(),
        groups,
        **params,
    )
    assert result == methods.permutation_mae(
        lambda values: values.amount.to_numpy(),
        frame,
        trajectories,
        frame.amount.to_numpy(),
        groups,
        **params,
    )
    assert result["groups"]["joint"]["mean"] > 0


def test_supported_ice_and_pdp_exclude_implausible_cells():
    training = pd.DataFrame({"amount": [0.0, 1.0, 2.0], "cadence": ["m", "m", "m"]})
    lines = [
        methods.supported_predictions(
            lambda table: 2 * table.amount.to_numpy(),
            training,
            training,
            {"amount": amount},
            cadence="cadence",
            coordinates=("amount",),
            radius=0.3,
        )
        for amount in (0.0, 2.0, 10.0)
    ]
    np.testing.assert_allclose(lines[0], [0, 0, 0])
    np.testing.assert_allclose(lines[1], [4, 4, 4])
    assert np.isnan(lines[2]).all()
    np.testing.assert_allclose([np.mean(row) for row in lines[:2]], [0, 4])


def test_stability_resampling_reproducible_and_uses_real_top_set():
    points = np.array([[7.0, 3.0, -2.0, 1.0], [10.0, 2.0, 1.0, 0.0], [3.0, -12.0, -2.0, 1.0]])
    result = methods.sampling_stability(points, seed=913, repeats=10)
    assert result == methods.sampling_stability(points, seed=913, repeats=10)
    assert len(result) == 10
    assert methods.rank_agreement(
        np.array([4.0, 3.0, 2.0, 1.0]), np.array([1.0, 2.0, 3.0, 4.0])
    ) == {
        "spearman": -1.0,
        "top_jaccard": 0.0,
    }


def test_report_hashes_and_frozen_identity_fail_closed(tmp_path):
    protocol = tmp_path / "protocol.json"
    protocol.write_text(dumps(research.PROTOCOL))
    path = tmp_path / "clv.json"
    payload = {
        "schema": research.SCHEMA,
        "model": {"name": "clv", "sha256": frozen.MODEL_HASHES["clv"]},
        "protocol_sha256": frozen.digest(protocol),
    }
    path.write_text(dumps(payload))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(dumps({name.name: frozen.digest(name) for name in (protocol, path)}))
    assert research.load_report(tmp_path, "clv") == payload
    path.write_text("{}")
    with pytest.raises(ValueError, match="integrity"):
        research.load_report(tmp_path, "clv")


def test_tree_gate_checks_background_mean_even_when_sum_is_additive(monkeypatch):
    rows = pd.DataFrame({"score": [0.2, 0.4]})
    model = SimpleNamespace(
        name="churn", pipeline=None, predict=lambda frame, output: frame.score.to_numpy()
    )
    values = methods.Attribution(
        ("score",), np.array([[0.1], [0.3]]), np.array([0.1, 0.1]), rows.score.to_numpy()
    )
    monkeypatch.setattr(methods, "tree_attribution", lambda *args, **kwargs: values)
    explanation, check = research._check_tree(model, rows, rows, "final")
    assert explanation is None
    assert check["failures"] == 0 and not check["supported"]
    assert check["reference_base_max_error"] == pytest.approx(0.2)
