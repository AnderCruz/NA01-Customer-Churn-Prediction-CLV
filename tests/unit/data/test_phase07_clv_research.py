"""Check CLV financial scoring, isolation and training-only preprocessing."""

import numpy as np
import pandas as pd
import pytest

from nowa_customer_intelligence.models.clv.design import (
    MINIMUM,
    failed_partitions,
    training_account,
)
from nowa_customer_intelligence.models.clv.features import FEATURES
from nowa_customer_intelligence.models.clv.research import (
    MENU,
    _pipeline,
    evaluate,
    select_candidate,
)


def test_financial_metrics_and_selection_tie() -> None:
    actual, forecast = np.array([0.0, 10.0, 40.0]), np.array([10.0, 0.0, 45.0])
    errors = evaluate(actual, forecast)
    assert errors["MAE"] == pytest.approx(25 / 3)
    assert errors["Bias"] == pytest.approx(5 / 3)
    assert errors["Aggregate error"] == 5
    assert errors["RMSE"] == pytest.approx(np.sqrt(75))
    assert errors["Median AE"] == 10
    assert select_candidate({"Ridge": {"MAE": 10}, "Training median": {"MAE": 10.005}}) == (
        "Training median"
    )


def test_train_only_transformations_handle_unseen_categories() -> None:
    train = pd.DataFrame(
        {
            spec.name: ["seen", "seen", "seen"] if spec.units == "category" else [0.0, 1.0, 2.0]
            for spec in FEATURES
        }
    )
    pipeline = _pipeline(MENU["Ridge"]).fit(train, [10.0, 20.0, 30.0])
    validation = train.assign(tenure_days=1000, cadence="unseen")
    pipeline.predict(validation)
    preprocess = pipeline.steps[0][1]
    assert preprocess.named_transformers_["numeric"].steps[0][1].statistics_[0] == 1
    assert list(preprocess.named_transformers_["category"].categories_[1]) == ["seen"]


def test_fixed_account_assignment_and_support_gate() -> None:
    groups = {"train": set(), "validate": set()}
    keys = [f"customer-{n}" for n in range(100)]
    for key in keys * 2:
        groups["train" if training_account(key) else "validate"].add(key)
    assert groups["train"].isdisjoint(groups["validate"])
    assert len(groups["train"] | groups["validate"]) == 100
    counts = {
        k: dict(
            accounts=n,
            zero_accounts=15,
            positive_accounts=30,
            monthly_accounts=15,
            annual_accounts=15,
        )
        for k, n in MINIMUM.items()
    }
    assert not failed_partitions(counts)
    counts["reserve"]["zero_accounts"] -= 1
    assert failed_partitions(counts) == ["reserve"]
