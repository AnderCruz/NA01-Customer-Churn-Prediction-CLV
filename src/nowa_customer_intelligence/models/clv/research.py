"""Run the frozen CLV research menu and publish local checksum-verified evidence."""

import argparse
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
from json import dumps, loads
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

from .design import (
    DEVELOPMENT_SEED,
    MINIMUM,
    PROTOCOL,
    RESERVE_NAMESPACE,
    RESERVE_SEED,
    RESERVE_START,
    TRAIN_LAST,
    TRAIN_START,
    VALIDATION_LAST,
    VALIDATION_START,
    ResearchRow,
    assemble,
    failed_partitions,
    support,
)
from .features import FEATURES
from .reference import load_reference_history

MODEL_SEED = 42
WORKSPACE = Path("data/processed/phase07-clv-research")
MENU = {
    "Training median": DummyRegressor(strategy="median"),
    "Ridge": Ridge(alpha=10),
    "Random Forest": RandomForestRegressor(
        n_estimators=100, max_depth=8, min_samples_leaf=15, random_state=MODEL_SEED, n_jobs=1
    ),
    "Histogram Gradient Boosting": HistGradientBoostingRegressor(
        max_iter=100,
        learning_rate=0.06,
        max_leaf_nodes=15,
        min_samples_leaf=25,
        l2_regularization=1,
        early_stopping=False,
        random_state=MODEL_SEED,
    ),
}


def model_inputs(rows: list[ResearchRow]) -> pd.DataFrame:
    """Convert Decimal GBP only at the numerical model input boundary."""
    frame = pd.DataFrame([row.predictors for row in rows], columns=[spec.name for spec in FEATURES])
    for spec in FEATURES:
        if spec.units != "category":
            frame[spec.name] = frame[spec.name].astype(float)
    return frame


def evaluate(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Report GBP error with bias defined as prediction minus outcome."""
    error = predicted - actual
    return {
        "MAE": float(np.abs(error).mean()),
        "RMSE": float(np.sqrt(np.mean(error**2))),
        "Median AE": float(np.median(np.abs(error))),
        "Bias": float(error.mean()),
        "Aggregate error": float(error.sum()),
        "R²": float(r2_score(actual, predicted)) if len(actual) > 1 and np.ptp(actual) else None,
    }


def select_candidate(rows: dict[str, dict]) -> str:
    """Select validation MAE with a one-penny tolerance and fixed menu order."""
    lowest = min(row["MAE"] for row in rows.values())
    return next(name for name in MENU if name in rows and rows[name]["MAE"] <= lowest + 0.01)


def _pipeline(estimator):
    from sklearn.base import clone

    numeric = [spec.name for spec in FEATURES if spec.units != "category"]
    categorical = [spec.name for spec in FEATURES if spec.units == "category"]
    preparation = ColumnTransformer(
        [
            (
                "numeric",
                make_pipeline(
                    SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                    StandardScaler(),
                ),
                numeric,
            ),
            ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
        ]
    )
    return make_pipeline(preparation, clone(estimator))


def _target(rows: list[ResearchRow]) -> np.ndarray:
    return np.array([float(row.target.future_6m_issued_gbp) for row in rows])


def _details(rows: list[ResearchRow], predictions: np.ndarray) -> list[dict]:
    return [
        {
            "Actual GBP": float(row.target.future_6m_issued_gbp),
            "Predicted GBP": float(p),
            "Observation month": row.target.observed_at.strftime("%Y-%m"),
            "Cadence": row.predictors["cadence"],
            "Tenure days": row.predictors["tenure_days"],
            "Historical GBP": float(row.predictors["issued_gbp"]),
        }
        for row, p in zip(rows, predictions, strict=True)
    ]


def _interval(rows: list[ResearchRow], actual: np.ndarray, predictions: np.ndarray) -> list[float]:
    grouped = {}
    for row, error in zip(rows, np.abs(predictions - actual), strict=True):
        total, count = grouped.get(row.target.customer_id, (0.0, 0))
        grouped[row.target.customer_id] = (total + error, count + 1)
    blocks = np.array(list(grouped.values()))
    indexes = np.random.default_rng(MODEL_SEED).integers(0, len(blocks), (400, len(blocks)))
    sums = blocks[indexes].sum(axis=1)
    return np.percentile(sums[:, 0] / sums[:, 1], [2.5, 97.5]).tolist()


def _json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(dumps(value, indent=2, allow_nan=False) + "\n")


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _fingerprint(rows: list[ResearchRow]) -> str:
    return sha256(
        dumps([asdict(row) for row in rows], default=str, sort_keys=True).encode()
    ).hexdigest()


def load_report(workspace: Path) -> dict:
    """Verify local research evidence without opening a model binary."""
    paths = workspace / "results"
    manifest = loads((paths / "manifest.json").read_bytes())
    content = (paths / "report.json").read_bytes()
    if manifest["report_sha256"] != sha256(content).hexdigest():
        raise ValueError("CLV research report integrity failed.")
    report = loads(content)
    if report["design"]["protocol"] != PROTOCOL or report["design"] != loads(
        (workspace / "design.json").read_bytes()
    ):
        raise ValueError("CLV research design mismatch.")
    return report


def run(workspace: Path) -> dict:
    """Run one experiment in a new workspace, with an exclusive reserve score."""
    workspace.mkdir(parents=True, exist_ok=False)
    development, inventory = load_reference_history()
    reserve, reserve_inventory = load_reference_history(
        master_seed=RESERVE_SEED, client_scope=RESERVE_NAMESPACE
    )
    dev_rows, dev_audit = assemble(development, complete_through=development.cutoff)
    held_rows, reserve_audit = assemble(reserve, complete_through=reserve.cutoff, reserve=True)
    if {r.episode.subscription_id for r in development.episodes} & {
        r.episode.subscription_id for r in reserve.episodes
    }:
        raise ValueError("Reserve and development share canonical episode identity.")
    if {r.target.customer_id for r in dev_rows["training"]} & {
        r.target.customer_id for r in dev_rows["validation"]
    }:
        raise ValueError("Training and validation accounts overlap.")
    all_rows = dev_rows | held_rows
    counts = {k: support(v) for k, v in all_rows.items()}
    failed = failed_partitions(counts)
    design = {
        "protocol": PROTOCOL,
        "development_seed": DEVELOPMENT_SEED,
        "reserve_seed": RESERVE_SEED,
        "reserve_namespace": RESERVE_NAMESPACE,
        "model_seed": MODEL_SEED,
        "windows": [
            d.isoformat()
            for d in (
                TRAIN_START,
                TRAIN_LAST,
                VALIDATION_START,
                VALIDATION_LAST,
                RESERVE_START,
                reserve.cutoff,
            )
        ],
        "support": counts,
        "partition_sha256": {name: _fingerprint(rows) for name, rows in all_rows.items()},
        "failed_partitions": failed,
        "account_floor": MINIMUM,
        "development_audit": dev_audit,
        "reserve_audit": reserve_audit,
        "source_inventory": [asdict(row) for row in inventory],
        "reserve_inventory": [asdict(row) for row in reserve_inventory],
        "features": [spec._asdict() for spec in FEATURES],
        "configurations": {name: estimator.get_params() for name, estimator in MENU.items()},
        "selection": "Validation MAE with one-penny tie tolerance in fixed menu order",
        "dependencies": {name: version(name) for name in ("numpy", "pandas", "scikit-learn")},
        "contractual_baseline": "Deferred: the source supplies no approved future retention rule.",
    }
    _json(workspace / "design.json", design)
    if failed:
        return {"design": design}
    training, validation = dev_rows["training"], dev_rows["validation"]
    train_x, val_x = model_inputs(training), model_inputs(validation)
    train_y, val_y = _target(training), _target(validation)
    val_scores, scores, pipelines = {}, {}, {}
    with TemporaryDirectory(dir=workspace) as temporary, threadpool_limits(1):
        output = Path(temporary) / "results"
        output.mkdir()
        for name, estimator in MENU.items():
            pipeline = _pipeline(estimator).fit(train_x, train_y)
            val_prediction = np.maximum(0, pipeline.predict(val_x))
            training_prediction = np.maximum(0, pipeline.predict(train_x))
            val_scores[name] = evaluate(val_y, val_prediction)
            scores[name] = {
                "training": evaluate(train_y, training_prediction),
                "validation": val_scores[name],
            }
            pipelines[name] = (pipeline, val_prediction)
        selected = select_candidate(val_scores)
        winner, validation_prediction = pipelines[selected]
        dump(winner, output / "selected.joblib")
        freeze = {
            "name": selected,
            "design_sha256": _hash(workspace / "design.json"),
            "model_sha256": _hash(output / "selected.joblib"),
            "metrics": list(val_scores[selected]),
        }
        _json(workspace / "frozen.json", freeze)
        held = held_rows["reserve"]
        held_y = _target(held)
        held_prediction = np.maximum(0, winner.predict(model_inputs(held)))
        report = {
            "design": design,
            "frozen": freeze,
            "scores": scores,
            "validation": _details(validation, validation_prediction),
            "feature_quality": {
                name: {
                    "training_missing": int(train_x[name].isna().sum()),
                    "validation_missing": int(val_x[name].isna().sum()),
                    "training_distinct": int(train_x[name].nunique()),
                }
                for name in train_x
            },
            "reserve": evaluate(held_y, held_prediction),
            "validation_mae_interval": _interval(validation, val_y, validation_prediction),
            "reserve_mae_interval": _interval(held, held_y, held_prediction),
        }
        _json(output / "report.json", report)
        _json(output / "manifest.json", {"report_sha256": _hash(output / "report.json")})
        output.rename(workspace / "results")
    return report


def main() -> None:
    """Explicitly generate the research evidence outside version control."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    args = parser.parse_args()
    report = run(args.workspace)
    print(dumps({key: report[key] for key in ("frozen", "scores", "reserve") if key in report}))
    print(report["design"]["support"], report["design"]["failed_partitions"])


if __name__ == "__main__":
    main()
