"""Run the approved bounded Phase 09 research using frozen development evidence."""

import argparse
from functools import partial
from hashlib import sha256
from importlib.metadata import version
from json import dumps, loads
from pathlib import Path
from platform import python_version
from time import perf_counter

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from . import methods
from .frozen import (
    MODEL_HASHES,
    SCALES,
    FrozenModel,
    audit_predictions,
    digest,
    feature_lineage,
    load_development,
)

WORKSPACE = Path("data/processed/phase09-explainability-research")
SCHEMA = "phase09-explainability-v1"
GROUPS = {
    "churn": {
        "Episode history": ("episode_age_days", "prior_completed_episodes"),
        "Billing and contract": (
            "plan_id",
            "billing_frequency",
            "monthly_recurring_gbp",
            "issued_invoice_count",
            "issued_amount_gbp",
            "mean_invoice_gbp",
            "days_since_last_invoice",
        ),
        "Product usage and coverage": (
            "expected_usage_months",
            "observed_usage_months",
            "unobserved_usage_months",
            "usage_coverage_ratio",
            "active_user_months",
            "zero_active_user_months",
            "latest_active_users",
            "mean_active_users",
            "max_active_users",
            "latest_sessions",
            "mean_sessions",
            "latest_events",
            "mean_events",
            "active_users_change",
            "sessions_change",
            "events_change",
        ),
    },
    "clv": {
        "Account lifecycle": ("tenure_days", "episodes", "completed", "reactivated", "active"),
        "Invoice history and cadence": (
            "invoice_count",
            "issued_gbp",
            "recent_gbp",
            "mean_invoice_gbp",
            "recency_days",
            "monthly",
            "annual",
            "billing_evidence",
            "cadence",
        ),
        "Contract snapshots": ("snapshot_gbp", "snapshot_coverage"),
        "Calendar": ("month",),
    },
}
PROTOCOL = {
    "schema": SCHEMA,
    "model_sha256": MODEL_HASHES,
    "development_seed": 42,
    "populations": ["frozen development training", "previously evaluated development validation"],
    "groups": GROUPS,
    "outputs": SCALES,
    "backgrounds": [[64, 909], [64, 910], [64, 911], [32, 909], [128, 909]],
    "background_balance": "One latest row per account, proportionate cadence, stable episode tie",
    "validation_sample": [96, 914],
    "local_cases": {
        "clv": [
            "monthly median prediction",
            "annual median prediction",
            "low absolute error",
            "largest absolute error",
            "mature zero with high forecast",
            "high historical issuance",
            "clipping observed",
        ],
        "churn": [
            "confirmed positive near positive median",
            "high score false positive",
            "low score true negative",
            "near the research threshold",
        ],
    },
    "cohort_matching": "Distinct accounts with identical ordered validation timestamps",
    "permutation": {
        "seed": 912,
        "repeats": 30,
        "clv_singletons": ["recency_days", "issued_gbp", "invoice_count", "tenure_days"],
    },
    "tolerances": {"probability": 1e-8, "log_odds": 1e-7, "GBP": 1e-6},
    "stability": {"seed": 913, "repeats": 100, "spearman": 0.80, "top_jaccard": 0.60},
    "sensitivity": {
        "minimum_accounts": 5,
        "radius_in_training_iqrs": 0.30,
        "quantiles": [0.1, 0.25, 0.5, 0.75, 0.9],
        "interaction_quantiles": [0.1, 0.5, 0.9],
        "churn": {
            "cadence": "billing_frequency",
            "features": ["days_since_last_invoice", "episode_age_days", "billing_frequency"],
            "pairs": [
                ["days_since_last_invoice", "billing_frequency"],
                ["episode_age_days", "monthly_recurring_gbp"],
            ],
            "context": [
                "episode_age_days",
                "monthly_recurring_gbp",
                "issued_invoice_count",
                "issued_amount_gbp",
                "days_since_last_invoice",
            ],
        },
        "clv": {
            "cadence": "cadence",
            "features": ["recent_gbp", "recency_days", "tenure_days", "cadence"],
            "pairs": [["issued_gbp", "invoice_count"], ["recency_days", "cadence"]],
            "context": [
                "issued_gbp",
                "recent_gbp",
                "invoice_count",
                "recency_days",
                "snapshot_gbp",
                "tenure_days",
            ],
        },
    },
    "failure": "Unreconciled modes are excluded; validated final-output block method is fallback.",
    "scope": "Internal model behaviour; no operational decisions, causality or reserve scoring.",
}


def _write(path: Path, content: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(dumps(content, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def load_report(workspace: Path, name: str) -> dict:
    """Load a Phase 09 report only after checking the protocol and evidence hashes."""
    if name not in MODEL_HASHES:
        raise ValueError("Unknown explanation report.")
    manifest = loads((workspace / "manifest.json").read_bytes())
    filename = f"{name}.json"
    inputs = {item: (workspace / item).read_bytes() for item in ("protocol.json", filename)}
    for item, content in inputs.items():
        if sha256(content).hexdigest() != manifest[item]:
            raise ValueError(f"Phase 09 report integrity failed for {item}.")
    report = loads(inputs[filename])
    if (
        loads(inputs["protocol.json"]) != loads(dumps(PROTOCOL))
        or report["schema"] != SCHEMA
        or report["model"]["sha256"] != MODEL_HASHES[name]
        or report["protocol_sha256"] != manifest["protocol.json"]
        or report["model"]["name"] != name
    ):
        raise ValueError("Phase 09 explanation provenance is incompatible.")
    return report


def _summary(metadata: pd.DataFrame) -> dict:
    return {
        "rows": len(metadata),
        "accounts": int(metadata.account.nunique()),
        "cadence": metadata.cadence.value_counts().to_dict(),
        "month": metadata.time.dt.strftime("%Y-%m").value_counts().sort_index().to_dict(),
    }


def _records(frame: pd.DataFrame) -> list[dict]:
    return loads(frame.to_json(orient="records", double_precision=15))


def _background(model: FrozenModel, size: int, seed: int) -> tuple[pd.DataFrame, dict]:
    cohort = model.training
    order = methods.stratified_sample(cohort.metadata, size, seed)
    selected = cohort.features.loc[order]
    fingerprint = sha256(
        cohort.metadata.loc[order].to_json(date_format="iso").encode()
        + selected.to_json(double_precision=15).encode()
    ).hexdigest()
    return selected, _summary(cohort.metadata.loc[order]) | {"seed": seed, "sha256": fingerprint}


def _tolerance(name: str, output: str) -> float:
    key = "GBP" if name == "clv" else "log_odds" if output == "raw" else "probability"
    return PROTOCOL["tolerances"][key]


def _check_tree(model, cases, background, output, *, path_dependent=False):
    start = perf_counter()
    mode = "probability" if output == "final" else "raw"
    try:
        values = methods.tree_attribution(
            model.pipeline,
            cases,
            background,
            mode,
            model.predict(cases, output=output),
            path_dependent=path_dependent,
        )
        check = values.reconciliation(_tolerance(model.name, output))
        check["coefficient_shape"] = list(values.values.shape)
        check["base_shape"] = list(values.base.shape)
        if not path_dependent:
            expected = model.predict(background, output=output).mean()
            check["reference_base_max_error"] = float(np.max(np.abs(values.base - expected)))
        supported = check["failures"] == 0 and (
            check.get("reference_base_max_error", 0) <= check["tolerance"]
        )
    except (
        ImportError,
        ValueError,
        RuntimeError,
        TypeError,
        AttributeError,
        NotImplementedError,
        AssertionError,
    ) as exc:
        values, check, supported = None, {"reason": str(exc)}, False
    return (values if supported else None), check | {
        "supported": supported,
        "seconds": perf_counter() - start,
        "explained_output": SCALES[model.name][output],
        "perturbation": "tree_path_dependent" if path_dependent else "interventional",
    }


def _gates(model):
    interface = audit_predictions(model)
    background, support = _background(model, 32, 909)
    frame = model.validation.features
    cases = frame.iloc[np.linspace(0, len(frame) - 1, 12, dtype=int)]
    probes = {}
    for scale in ("raw", "final") if model.name == "churn" else ("raw",):
        _, probes[scale] = _check_tree(model, cases, background, scale)
    if model.name == "clv":
        _, probes["path_raw"] = _check_tree(model, cases, background, "raw", path_dependent=True)
    fallback = methods.grouped_shapley(
        lambda values: model.predict(values, output="final"), cases, background, GROUPS[model.name]
    ).reconciliation(_tolerance(model.name, "final"))
    if fallback["failures"]:
        raise ValueError("Final-output model-agnostic compatibility gate failed.")
    return {
        "prediction_contract": interface,
        "probe_background": support,
        "tree": probes,
        "grouped_callable": fallback,
    }


def _local_cases(model: FrozenModel, prediction: np.ndarray) -> dict[str, int]:
    cohort = model.validation
    frame, metadata = cohort.features, cohort.metadata
    errors = np.abs(prediction - cohort.target)
    raw = model.predict(frame, output="raw")
    table = metadata.assign(prediction=prediction, target=cohort.target, absolute_error=errors)
    if model.name == "clv":

        def middle(cadence):
            values = table.loc[table.cadence.eq(cadence), "prediction"]
            return (values - values.median()).abs().sort_values(kind="stable").index

        proposals = [
            middle("monthly"),
            middle("annual"),
            (table.absolute_error - table.absolute_error.quantile(0.25))
            .abs()
            .sort_values(kind="stable")
            .index,
            table.sort_values("absolute_error", ascending=False, kind="stable").index,
            table.loc[table.target.eq(0)]
            .sort_values("prediction", ascending=False, kind="stable")
            .index,
            frame.issued_gbp.sort_values(ascending=False, kind="stable").index,
            table.loc[raw < 0].index,
        ]
    else:
        threshold = model.freeze["threshold"]
        positives = table.loc[table.target.eq(1), "prediction"]
        proposals = [
            (positives - positives.median()).abs().sort_values(kind="stable").index,
            table.loc[table.target.eq(0) & table.prediction.ge(threshold)]
            .sort_values("prediction", ascending=False, kind="stable")
            .index,
            table.loc[table.target.eq(0) & table.prediction.lt(threshold)]
            .sort_values("prediction", kind="stable")
            .index,
            (table.prediction - threshold).abs().sort_values(kind="stable").index,
        ]
    cases = {}
    used = set()
    for label, indexes in zip(PROTOCOL["local_cases"][model.name], proposals, strict=True):
        for idx in indexes:
            account = table.loc[idx, "account"]
            if account not in used:
                cases[label] = int(idx)
                used.add(account)
                break
    return cases


def _grid(training: pd.DataFrame, name: str, quantiles: list[float]) -> list:
    column = training[name].dropna()
    if pd.api.types.is_numeric_dtype(column):
        return np.unique(np.quantile(column, quantiles, method="nearest")).tolist()
    return sorted(column.unique().tolist())


def _sensitivity(model, examples, local_ids, sample_size):
    settings = PROTOCOL["sensitivity"]
    spec = settings[model.name]
    training = model.training.features
    predict = partial(model.predict, output="final")
    curves, interactions = {}, []
    for term in spec["features"]:
        grid = _grid(training, term, settings["quantiles"])
        lines = np.array(
            [
                methods.supported_predictions(
                    predict,
                    training,
                    examples,
                    {term: value},
                    cadence=spec["cadence"],
                    coordinates=tuple(spec["context"]),
                    radius=settings["radius_in_training_iqrs"],
                )
                for value in grid
            ]
        )
        global_lines = lines[:, :sample_size]
        counts = np.isfinite(global_lines).sum(axis=1)
        curves[term] = {
            "grid": grid,
            "support": counts.tolist(),
            "candidate_accounts": sample_size,
            "pdp": [
                float(np.nanmean(row)) if size >= settings["minimum_accounts"] else None
                for row, size in zip(global_lines, counts, strict=True)
            ],
            "ice": {
                label: [float(value) if np.isfinite(value) else None for value in lines[:, pos]]
                for label, pos in local_ids.items()
            },
        }
    for first, second in spec["pairs"]:
        grid1 = _grid(training, first, settings["interaction_quantiles"])
        grid2 = _grid(training, second, settings["interaction_quantiles"])
        surface = np.array(
            [
                [
                    methods.supported_predictions(
                        predict,
                        training,
                        examples.iloc[:sample_size],
                        {first: x, second: y},
                        cadence=spec["cadence"],
                        coordinates=tuple(spec["context"]),
                        radius=settings["radius_in_training_iqrs"],
                    )
                    for x in grid1
                ]
                for y in grid2
            ]
        )
        counts = np.isfinite(surface).sum(axis=-1)
        values = [
            [
                float(np.nanmean(row)) if size >= settings["minimum_accounts"] else None
                for row, size in zip(layer, support, strict=True)
            ]
            for layer, support in zip(surface, counts, strict=True)
        ]
        contrasts = []
        for j in range(len(grid2) - 1):
            for i in range(len(grid1) - 1):
                difference = (
                    surface[j + 1, i + 1] - surface[j + 1, i] - surface[j, i + 1] + surface[j, i]
                )
                matched = int(np.isfinite(difference).sum())
                contrasts.append(
                    {
                        "x": grid1[i : i + 2],
                        "y": grid2[j : j + 2],
                        "matched": matched,
                        "effect": float(np.nanmean(difference))
                        if matched >= settings["minimum_accounts"]
                        else None,
                    }
                )
        interactions.append(
            {
                "features": [first, second],
                "x": grid1,
                "y": grid2,
                "surface": values,
                "support": counts.tolist(),
                "matched_contrasts": contrasts,
            }
        )
    return {"curves": curves, "interactions": interactions}


def _pack(attribution, *, method, scale, tolerance) -> dict:
    return {
        "method": method,
        "scale": scale,
        "columns": list(attribution.columns),
        "values": attribution.values.tolist(),
        "base": attribution.base.tolist(),
        "predictions": attribution.predictions.tolist(),
        "reconciliation": attribution.reconciliation(tolerance),
    }


def _distributions(model, prediction):
    cohort = model.validation
    predicted = cohort.metadata.assign(
        prediction=prediction,
        target=cohort.target,
        error=prediction - cohort.target,
        raw=model.predict(cohort.features, output="raw"),
    )
    sections = predicted.groupby("cadence", sort=True)
    return (
        {
            column: predicted[column].tolist()
            for column in ("cadence", "prediction", "target", "error", "raw")
        },
        {
            str(name): {
                "rows": len(frame),
                "accounts": int(frame.account.nunique()),
                "mean_prediction": float(frame.prediction.mean()),
                "mae": float(frame.error.abs().mean()),
            }
            for name, frame in sections
        },
    )


def _summarise_attribution(attribution, metadata, end):
    values = attribution.values[:end]
    ranks = dict(zip(attribution.columns, np.abs(values).mean(axis=0).tolist(), strict=True))
    cohorts = {}
    for cadence in sorted(metadata.cadence.unique()):
        mask = metadata.cadence.eq(cadence).to_numpy()
        cohorts[cadence] = {
            "accounts": int(mask.sum()),
            "mean_absolute": dict(
                zip(attribution.columns, np.abs(values[mask]).mean(axis=0).tolist(), strict=True)
            ),
            "mean_signed": dict(
                zip(attribution.columns, values[mask].mean(axis=0).tolist(), strict=True)
            ),
        }
    return {"mean_absolute": ranks, "cadences": cohorts}


def _stability(model, cases, background, primary, repeats, count, local_map, *, tree: bool):
    tolerance = _tolerance(model.name, "final")
    label = (
        "interventional TreeSHAP grouped to original features"
        if tree
        else "finite-background block Shapley"
    )
    cohorts = []
    local_values = {name: [primary.values[ix].tolist()] for name, ix in local_map.items()}
    prediction = primary.predictions
    baseline = np.abs(primary.values[:count]).mean(axis=0)

    def explain(reference):
        if tree:
            transformed, check = _check_tree(model, cases, reference, "final")
            if transformed is None:
                return None, check
            _, retained = feature_lineage(model.pipeline)
            original = methods.group_transformed(transformed, retained.original.tolist())
            return original, original.reconciliation(tolerance)
        result = methods.grouped_shapley(
            lambda frame: model.predict(frame, output="final"), cases, reference, GROUPS[model.name]
        )
        return result, result.reconciliation(tolerance)

    replay, replay_check = explain(background)
    if (
        replay is None
        or replay_check["failures"]
        or not np.array_equal(replay.predictions, prediction)
        or not np.allclose(replay.values, primary.values, atol=tolerance, rtol=0)
        or not np.allclose(replay.base, primary.base, atol=tolerance, rtol=0)
    ):
        raise ValueError("Primary explanation did not reproduce on the identical background.")
    for size, seed in repeats:
        alternate, support = _background(model, size, seed)
        values, check = explain(alternate)
        if values is None or check["failures"]:
            cohorts.append({"background": support, "validation": check, "available": False})
            continue
        cohorts.append(
            {
                "background": support,
                "available": True,
                "validation": check,
                "global": methods.rank_agreement(
                    baseline, np.abs(values.values[:count]).mean(axis=0)
                ),
                "maximum_local_abs_change": float(np.max(np.abs(values.values - primary.values))),
                "base_shift": float(values.base.mean() - primary.base.mean()),
            }
        )
        for name, ix in local_map.items():
            local_values[name].append(values.values[ix].tolist())
    settings = PROTOCOL["stability"]
    sampled = methods.sampling_stability(
        primary.values[:count], seed=settings["seed"], repeats=settings["repeats"]
    )
    summaries = {}
    for name, records in (
        ("account_bootstrap", sampled),
        ("background", [item["global"] for item in cohorts if item["available"]]),
    ):
        medians = {
            key: float(np.median(values))
            if (values := [item[key] for item in records if item[key] is not None])
            else None
            for key in ("spearman", "top_jaccard")
        }
        summaries[name] = medians | {
            "compared": len(records),
            "diagnostic_floors_met": all(
                value is not None and value >= settings[key] for key, value in medians.items()
            ),
        }
    return {
        "method": label,
        "background_comparisons": cohorts,
        "local_values": local_values,
        "sampling": sampled,
        "summary": summaries,
        "replay_max_abs_delta": float(np.max(np.abs(replay.values - primary.values))),
        "replay_max_base_delta": float(np.max(np.abs(replay.base - primary.base))),
    }


def _result(model, preflight, protocol_hash):
    start = perf_counter()
    data = model.validation
    prediction = model.predict(data.features, output="final")
    sample = methods.stratified_sample(data.metadata, *PROTOCOL["validation_sample"])
    local = _local_cases(model, prediction)
    extra = [idx for idx in local.values() if idx not in sample]
    rows = list(sample) + extra
    cases = data.features.loc[rows]
    local_map = {label: rows.index(idx) for label, idx in local.items()}
    num_global = len(sample)
    background, composition = _background(model, *PROTOCOL["backgrounds"][0])
    tolerance = _tolerance(model.name, "final")
    before, after = feature_lineage(model.pipeline)
    game = methods.grouped_shapley(
        lambda frame: model.predict(frame, output="final"), cases, background, GROUPS[model.name]
    )
    scale = SCALES[model.name]["final"]
    game_record = _pack(
        game,
        method="finite-background model-agnostic block Shapley",
        scale=scale,
        tolerance=tolerance,
    )
    if game_record["reconciliation"]["failures"]:
        raise ValueError("The complete final-output game failed reconciliation.")
    tree_evidence = {}
    use_tree = False
    primary = game
    if model.name == "churn":
        for output in ("raw", "final"):
            if not preflight["tree"][output]["supported"]:
                continue
            attribution, check = _check_tree(model, cases, background, output)
            tree_evidence[output] = {"check": check}
            if attribution is None:
                continue
            grouped = methods.group_transformed(attribution, after.original.tolist())
            registered = grouped.reconciliation(_tolerance(model.name, output))
            np.testing.assert_allclose(
                attribution.values.sum(axis=1), grouped.values.sum(axis=1), rtol=0, atol=1e-12
            )
            if registered["failures"]:
                raise ValueError("Grouped transformed attribution loses additive consistency.")
            tree_evidence[output]["original"] = _pack(
                grouped,
                method="interventional TreeSHAP grouped to original features",
                scale=SCALES[model.name][output],
                tolerance=_tolerance(model.name, output),
            )
            if output == "final":
                primary, use_tree = grouped, True
    details = tree_evidence["final"]["original"] if use_tree else game_record
    rankings = _summarise_attribution(primary, data.metadata.loc[sample], num_global)
    block_rankings = _summarise_attribution(game, data.metadata.loc[sample], num_global)
    stability = _stability(
        model,
        cases,
        background,
        primary,
        PROTOCOL["backgrounds"][1:],
        num_global,
        local_map,
        tree=use_tree,
    )
    raw = model.predict(cases, output="raw")
    cases_evidence = []
    for label, idx in local.items():
        pos = local_map[label]
        row = data.metadata.loc[idx]
        cases_evidence.append(
            {
                "label": label,
                "anonymous": f"Case {len(cases_evidence) + 1:02}",
                "position": pos,
                "cadence": row.cadence,
                "month": row.time.strftime("%Y-%m"),
                "actual": float(data.target[idx]),
                "final": float(prediction[idx]),
                "raw": float(raw[pos]),
                "signed_error": float(prediction[idx] - data.target[idx]),
            }
        )
    permutation = None
    if model.name == "clv":
        config = PROTOCOL["permutation"]
        groups = GROUPS[model.name] | {key: (key,) for key in config["clv_singletons"]}
        permutation = methods.permutation_mae(
            lambda frame: model.predict(frame, output="final"),
            data.features,
            data.metadata,
            data.target,
            groups,
            repeats=config["repeats"],
            seed=config["seed"],
        )
    distribution, cohorts = _distributions(model, prediction)
    numeric = data.features.select_dtypes(include=[np.number])
    correlations = loads(numeric.corr(method="spearman").to_json(double_precision=10))
    identity = {
        "name": model.name,
        "sha256": MODEL_HASHES[model.name],
        "identifier": model.freeze.get("candidate", model.freeze.get("name")),
        "registry": model.registry,
        "class": type(model.pipeline[-1]).__name__,
        "steps": [type(step).__name__ for _, step in model.pipeline.steps],
        "input_hashes": model.input_hashes,
        "threshold": model.freeze.get("threshold"),
    }
    if digest(model.model_path) != MODEL_HASHES[model.name]:
        raise ValueError("Retained frozen model digest changed.")
    return {
        "schema": SCHEMA,
        "protocol_sha256": protocol_hash,
        "model": identity,
        "compatibility": preflight,
        "accepted_metrics": model.accepted_metrics,
        "reference_populations": {
            "training": _summary(model.training.metadata),
            "validation": _summary(data.metadata),
            "explained_global": _summary(data.metadata.loc[sample]),
        },
        "background": composition,
        "feature_dictionary": model.specification,
        "lineage": _records(before),
        "retained_lineage": _records(after),
        "feature_values": _records(cases),
        "explained_outcomes": _records(
            data.metadata.loc[rows, ["cadence"]].assign(
                actual=data.target[rows], prediction=prediction[rows]
            )
        ),
        "cases": cases_evidence,
        "global_rows": num_global,
        "primary": details,
        "grouped_game": game_record,
        "tree_explanations": tree_evidence,
        "global": rankings,
        "grouped_global": block_rankings,
        "stability": stability,
        "permutation": permutation,
        "distribution": distribution,
        "validation_cadence": cohorts,
        "rank_correlations": correlations,
        "sensitivity": _sensitivity(model, cases, local_map, num_global),
        "elapsed_seconds": perf_counter() - start,
    }


def run(workspace: Path, processed: Path) -> None:
    """Complete model and compatibility gates before publishing bounded results."""
    workspace.mkdir(parents=True, exist_ok=False)
    _write(workspace / "protocol.json", PROTOCOL)
    protocol_hash = digest(workspace / "protocol.json")
    with threadpool_limits(limits=1):
        models = {name: load_development(name, processed) for name in ("churn", "clv")}
        preflight = {name: _gates(model) for name, model in models.items()}
        environment = {
            "python": python_version(),
            "packages": {
                name: version(name)
                for name in ("numpy", "scikit-learn", "shap", "numba", "joblib", "scipy", "pandas")
            },
        }
        _write(workspace / "compatibility.json", environment | {"models": preflight})
        print("Frozen prediction and compatibility gates complete.", flush=True)
        for name, model in models.items():
            report = _result(model, preflight[name], protocol_hash)
            report["environment"] = environment
            _write(workspace / f"{name}.json", report)
            print(
                f"{name}: {report['primary']['method']}, {report['elapsed_seconds']:.1f}s",
                flush=True,
            )
    items = ("protocol.json", "compatibility.json", "churn.json", "clv.json")
    _write(workspace / "manifest.json", {name: digest(workspace / name) for name in items})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    run(args.workspace, args.processed)
