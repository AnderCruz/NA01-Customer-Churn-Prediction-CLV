"""Read-only Phase 09 interfaces bound to accepted developments and models."""

from dataclasses import asdict, dataclass
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import load
from scipy.special import expit
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline

from ..data.synthetic.feature_matrix import FEATURE_SPEC_VERSION
from ..models.churn import dataset, estimators
from ..models.churn import research as churn
from ..models.clv import design, reference
from ..models.clv import research as clv
from ..models.clv.features import FEATURES

MODEL_HASHES = {
    "churn": "16d7a588ec36dc4b22beb20b56f98903af68d4453563921985ba063a024a8cd1",
    "clv": "250f4d860a662f69f95e2577cd890dc4f86d75c33771bc8dc0ed04aa4398afc7",
}
SCALES = {
    "churn": {"raw": "class-1 log odds", "final": "class-1 probability"},
    "clv": {"raw": "pre-clip signed gross issued GBP", "final": "clipped gross issued GBP"},
}


def digest(path: Path) -> str:
    """Return the SHA-256 of an explicitly selected local file."""
    return sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class Cohort:
    """Predictors and independent audit fields in the frozen development row order."""

    features: pd.DataFrame
    metadata: pd.DataFrame
    target: np.ndarray

    def __post_init__(self) -> None:
        if (
            len(self.features) != len(self.metadata)
            or len(self.features) != len(self.target)
            or not self.features.columns.is_unique
            or not self.features.index.equals(self.metadata.index)
            or not self.features.index.is_unique
        ):
            raise ValueError("Cohort rows or feature order are ambiguous.")


@dataclass(frozen=True, slots=True)
class FrozenModel:
    """An audited frozen pipeline with its allowed development cohorts."""

    name: str
    pipeline: Pipeline
    registry: str
    model_path: Path
    freeze: dict
    training: Cohort
    validation: Cohort
    input_hashes: dict
    specification: list[dict]
    accepted_metrics: dict
    saved_predictions: np.ndarray | None

    def predict(self, frame: pd.DataFrame, *, output: str) -> np.ndarray:
        """Apply the accepted full pipeline and the specified output contract."""
        columns = tuple(self.pipeline.feature_names_in_)
        if tuple(frame.columns) != columns or output not in SCALES[self.name]:
            raise ValueError("Unexpected feature order or explanation output.")
        if self.name == "churn":
            values = (
                estimators.churn_scores(self.pipeline, frame)
                if output == "final"
                else self.pipeline.decision_function(frame)
            )
        else:
            values = self.pipeline.predict(frame)
            if output == "final":
                values = np.maximum(values, 0)
        if values.shape != (len(frame),) or not np.isfinite(values).all():
            raise ValueError("The frozen predictor did not return finite scalar outputs.")
        return values


def _frozen_pipeline(name: str, directory: Path, report: dict) -> tuple[Pipeline, Path, dict]:
    frozen = loads((directory / "frozen.json").read_bytes())
    path = directory / "results/selected.joblib"
    content = path.read_bytes()
    expected_estimator = (
        HistGradientBoostingClassifier if name == "churn" else HistGradientBoostingRegressor
    )
    if (
        frozen != report["frozen"]
        or frozen["design_sha256"] != digest(directory / "design.json")
        or loads((directory / "design.json").read_bytes()) != report["design"]
        or frozen["model_sha256"] != MODEL_HASHES[name]
        or sha256(content).hexdigest() != MODEL_HASHES[name]
    ):
        raise ValueError("Frozen audit fingerprints differ from the accepted evidence.")
    model = load(BytesIO(content))
    if type(model) is not Pipeline or type(model[-1]) is not expected_estimator:
        raise ValueError("Unexpected frozen estimator.")
    return model, path, frozen


def _churn_cohort(rows: tuple[dataset.ResolvedObservation, ...]) -> Cohort:
    frame = dataset.model_inputs(rows)
    metadata = pd.DataFrame(
        {
            "account": [row.customer for row in rows],
            "time": [row.key.observed_at for row in rows],
            "episode": [row.key.subscription_id for row in rows],
            "cadence": frame["billing_frequency"],
        }
    )
    return Cohort(frame, metadata, np.array([row.target for row in rows], dtype=int))


def _clv_cohort(rows: list[design.ResearchRow]) -> Cohort:
    frame = clv.model_inputs(rows)
    metadata = pd.DataFrame(
        {
            "account": [row.target.customer_id for row in rows],
            "time": [row.target.observed_at for row in rows],
            "cadence": frame["cadence"],
        }
    )
    return Cohort(frame, metadata, np.array([float(r.target.future_6m_issued_gbp) for r in rows]))


def load_development(name: str, processed: Path) -> FrozenModel:
    """Load only explicit seed-42 development paths and verify their provenance."""
    if name == "churn":
        directory = processed / "phase06-research"
        _, report = churn.load_reports(directory / "results")
        pipeline, path, frozen = _frozen_pipeline(name, directory, report)
        bundle = dataset.load_bundle(processed / "phase05-fieldwise-final", seed=42)
        original = report["design"]
        if (
            bundle.manifest_hash != original["reference_manifest_sha256"]
            or bundle.evidence_hash != original["reference_evidence_sha256"]
            or tuple(pipeline.feature_names_in_) != dataset.COLUMNS
            or tuple(pipeline.classes_) != (0, 1)
            or pipeline[-1].get_params() != frozen["parameters"]
            or frozen["threshold"] != 0.003965284793899528
            or report["holdout"] is not None
        ):
            raise ValueError("Churn development contract or class orientation changed.")
        partitions, _ = dataset.partition(bundle, fresh=False)
        if any(
            dataset.support(rows) != original["support"][key] for key, rows in partitions.items()
        ):
            raise ValueError("Churn development allocation changed.")
        accepted = next(
            row["validation"] for row in report["candidates"] if row["name"] == frozen["candidate"]
        )
        return FrozenModel(
            name,
            pipeline,
            FEATURE_SPEC_VERSION,
            path,
            frozen,
            _churn_cohort(partitions["training"]),
            _churn_cohort(partitions["validation"]),
            {"bundle_manifest": bundle.manifest_hash, "internal_evidence": bundle.evidence_hash},
            original["features"],
            accepted,
            None,
        )
    if name != "clv":
        raise ValueError("Only accepted churn and CLV development evidence is allowed.")
    directory = processed / "phase07-clv-research"
    report = clv.load_report(directory)
    pipeline, path, frozen = _frozen_pipeline(name, directory, report)
    original = report["design"]
    if (
        tuple(pipeline.feature_names_in_) != tuple(field.name for field in FEATURES)
        or pipeline[-1].get_params() != original["configurations"][frozen["name"]]
    ):
        raise ValueError("CLV fitted feature or estimator contract changed.")
    ledger, _ = reference.load_reference_history(master_seed=42)
    partitions, _ = design.assemble(ledger, complete_through=ledger.cutoff, reserve=False)
    hashes = {}
    for key, rows in partitions.items():
        content = dumps([asdict(row) for row in rows], default=str, sort_keys=True).encode()
        hashes[key] = sha256(content).hexdigest()
        if (
            hashes[key] != original["partition_sha256"][key]
            or design.support(rows) != original["support"][key]
        ):
            raise ValueError("CLV development ordering or evidence changed.")
    return FrozenModel(
        name,
        pipeline,
        design.PROTOCOL,
        path,
        frozen,
        _clv_cohort(partitions["training"]),
        _clv_cohort(partitions["validation"]),
        hashes,
        original["features"],
        report["scores"][frozen["name"]]["validation"]
        | {
            "training_median_MAE": report["scores"]["Training median"]["validation"]["MAE"],
        },
        np.array([row["Predicted GBP"] for row in report["validation"]]),
    )


def feature_lineage(pipeline: Pipeline) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Map fitted numerical, indicator and categorical positions through selection."""
    prep = pipeline[0]
    origins = []
    for group, transformer, inputs in prep.transformers_:
        if group == "remainder":
            if transformer != "drop":
                raise ValueError("Unexpected passthrough coordinates.")
            continue
        if group == "numeric":
            imputer = transformer[0]
            columns = [(name, "numerical") for name in inputs]
            if imputer.indicator_ is not None:
                columns.extend(
                    (inputs[index], "missing indicator") for index in imputer.indicator_.features_
                )
        elif group == "missing":
            columns = [(inputs[index], "missing indicator") for index in transformer.features_]
        elif group == "category":
            if transformer.drop_idx_ is not None or transformer.min_frequency is not None:
                raise ValueError("Unsupported one-hot category regrouping.")
            columns = [
                (name, f"category {level}")
                for name, levels in zip(inputs, transformer.categories_, strict=True)
                for level in levels
            ]
        else:
            raise ValueError("Unknown frozen transformation block.")
        span = prep.output_indices_[group]
        if span.start != len(origins) or span.stop - span.start != len(columns):
            raise ValueError("Fitted output positions do not match the original feature mapping.")
        origins.extend(columns)
    before = pd.DataFrame(origins, columns=["original", "component"])
    before.insert(0, "transformed", prep.get_feature_names_out())
    before["retained"] = pipeline[1].get_support() if len(pipeline) == 3 else True
    after = before.loc[before.retained].reset_index(drop=True)
    if (
        list(after.transformed) != list(pipeline[:-1].get_feature_names_out())
        or len(after) != pipeline[-1].n_features_in_
    ):
        raise ValueError("Transformed feature lineage does not match the fitted estimator.")
    return before, after


def audit_predictions(frozen: FrozenModel) -> dict:
    """Reconcile every allowed validation output without fitting."""
    frame = frozen.validation.features
    raw = frozen.predict(frame, output="raw")
    final = frozen.predict(frame, output="final")
    coords = frozen.pipeline[:-1].transform(frame)
    before, after = feature_lineage(frozen.pipeline)
    widths = (len(frame.columns), len(before), len(after))
    expected = (25, 40, 30) if frozen.name == "churn" else (17, 29, 29)
    if widths != expected or coords.shape != (len(frame), widths[-1]):
        raise ValueError("Unexpected model input width.")
    if frozen.name == "churn":
        internal = frozen.pipeline[-1].decision_function(coords)
        linked = expit(raw)
        scores = estimators.metrics(frozen.validation.target, final, frozen.freeze["threshold"])
        for key, value in frozen.accepted_metrics.items():
            np.testing.assert_allclose(scores[key], value, rtol=0, atol=1e-12)
        np.testing.assert_allclose(linked, final, rtol=0, atol=1e-12)
        reference_error = float(np.max(np.abs(linked - final)))
    else:
        internal = frozen.pipeline[-1].predict(coords)
        np.testing.assert_allclose(final, frozen.saved_predictions, rtol=0, atol=1e-9)
        np.testing.assert_allclose(final, np.maximum(raw, 0), rtol=0, atol=1e-12)
        reference_error = float(np.max(np.abs(final - frozen.saved_predictions)))
    np.testing.assert_allclose(raw, internal, rtol=0, atol=1e-12)
    return {
        "widths": widths,
        "validation_rows": len(frame),
        "raw_pipeline_max_error": float(np.max(np.abs(raw - internal))),
        "linked_or_retained_max_error": reference_error,
        "validation_raw_negative": int(np.count_nonzero(raw < 0)) if frozen.name == "clv" else None,
    }
