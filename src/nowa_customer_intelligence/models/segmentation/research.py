"""Run the frozen Phase 08 protocol once in an isolated local workspace."""

import argparse
import os
import shutil
from dataclasses import asdict
from decimal import Decimal
from hashlib import sha256
from itertools import combinations
from json import dumps, loads
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

from ...data.eda_inputs import fieldwise_reference
from .clustering import (
    evaluate,
    fit_candidate,
    fit_preprocessing,
    generator_associations,
    valid_rows,
)
from .diagnostics import FEATURES
from .evaluation import FrozenAssignment, migration, profiles, stability, stability_passes
from .population import SourceEvidence, behaviour_gate, development_populations, observe
from .protocol import PROTOCOL, RESERVE_SCOPE, RESERVE_SEED
from .rfm import FIELDS, ReferenceScores, fit_references

DEFAULT_WORKSPACE = Path("data/processed/phase08-segmentation-research")
FAMILIES = ("K-Means", "Ward", "GMM")


def _encode(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Unsupported research artefact type {type(value).__name__}")


def digest(path: Path) -> str:
    """Fingerprint a local research artefact."""
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, contents: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        dumps(contents, indent=2, sort_keys=True, default=_encode, allow_nan=False) + "\n"
    )
    temporary.replace(path)


def load_report(workspace: Path | None = None) -> dict:
    """Read only checksum-verified JSON. Notebook replay performs no research fit."""
    workspace = workspace or Path(
        os.environ.get("NCI_SEGMENTATION_WORKSPACE", str(DEFAULT_WORKSPACE))
    )
    manifest = loads((workspace / "manifest.json").read_bytes())
    for name in ("protocol.json", "design.json", "report.json"):
        if digest(workspace / name) != manifest[name]:
            raise ValueError(f"Integrity check failed for {name}.")
    return loads((workspace / "report.json").read_bytes())


def feature_dictionary() -> list[dict]:
    """Expose the considered financial, contractual and behavioural fields and exclusions."""
    reasons = {
        "all_observed_gbp": "Cumulative exposure duplicates tenure and trailing issuance.",
        "mean_issue_gbp": "Invoice size strongly depends on pricing cadence.",
        "contractual_gbp_per_month": "Two catalogue rates among active reference accounts.",
        "established_episodes": "Duplicates the synthetic reactivation indicator.",
        "completed_episodes": "Duplicates the synthetic reactivation indicator.",
        "active_episodes": "Constant within the reference observation populations.",
    }
    spaces = PROTOCOL["feature_spaces"]
    entries = []
    for item in FEATURES:
        members = [
            name
            for name, blocks in spaces.items()
            if any(item.name in fields for fields in blocks.values())
        ]
        entries.append(
            item._asdict()
            | {
                "spaces": members,
                "admission": reasons.get(
                    item.name, "Primary input or prespecified contractual comparison."
                ),
            }
        )
    for measure in ("active_users", "sessions", "events"):
        for statistic, calculation in (
            ("latest", "Latest available comparable whole month"),
            ("mean", "Arithmetic mean of available comparable whole months"),
            ("change", "Last minus first expected month when both are available"),
        ):
            name = f"{statistic}_{measure}"
            entries.append(
                {
                    "name": name,
                    "calculation": calculation,
                    "meaning": f"Historical account {measure.replace('_', ' ')}",
                    "source": "Usage facts with validated episode and lifecycle",
                    "units": "count/month",
                    "dtype": "float" if statistic == "mean" else "integer",
                    "availability": "Full UTC period and dated row known at observation",
                    "missing": "Null when required evidence is unavailable or ambiguous",
                    "limitation": "Synthetic activity and one-day reporting delay",
                    "spaces": ["FS-03"] if statistic == "mean" else [],
                    "admission": "Conditional on three observed months and FS-03 support."
                    if statistic == "mean"
                    else "Descriptive usage diagnostic only.",
                }
            )
    return entries


def _label(score):
    return "-".join(map(str, score)) if score is not None else None


def reference_assignments(population, references: ReferenceScores, *, aware: bool) -> pd.Series:
    """Assign a frozen reference only to primary eligible accounts."""
    return pd.Series(
        {
            row.customer_id: _label(references.assign(row, cadence_aware=aware))
            for row in population.eligible
        },
        dtype=object,
    ).dropna()


def reference_report(populations, references: ReferenceScores) -> list[dict]:
    """Compare two reference methods on comparable accounts and frozen bands."""
    output = []
    previous = None
    for population in populations:
        frame = population.frame()
        assignments = {
            name: reference_assignments(population, references, aware=name == "cadence_aware")
            for name in ("traditional", "cadence_aware")
        }
        traditional, cadence = assignments.values()
        shared = traditional.index.intersection(cadence.index)
        values = pd.crosstab(traditional.loc[shared], cadence.loc[shared])
        comparisons = {}
        for name, labels in assignments.items():
            comparisons[name] = profiles(frame, labels) | {
                "unassignable": len(frame) - len(labels),
                "unassignable_by_cadence": frame.loc[~frame.index.isin(labels.index), "cadence"]
                .value_counts()
                .to_dict(),
                "per_dimension": [
                    labels.str.split("-").str[index].value_counts().to_dict()
                    for index in range(len(FIELDS))
                ],
            }
        output.append(
            {
                "date": population.observation.date().isoformat(),
                "methods": comparisons,
                "agreement": int(traditional.loc[shared].eq(cadence.loc[shared]).sum()),
                "compared": len(shared),
                "contingency": values.to_dict(),
                "frozen_reference_migration": {
                    name: migration(
                        previous[0][name], labels, previous[1], population.frame(eligible=False)
                    )
                    for name, labels in assignments.items()
                }
                if previous
                else None,
            }
        )
        previous = assignments, population.frame(eligible=False)
    return output


def _candidate(space, frame, val, full_populations, pipeline, coordinates, common, family, groups):
    key = f"{space} / {family} / {groups}"
    base = {
        "id": key,
        "space": space,
        "family": family,
        "groups": groups,
        "fitting_accounts": len(frame),
    }
    try:
        candidate = fit_candidate(family, groups, coordinates, PROTOCOL["fit_seed"])
    except (ValueError, np.linalg.LinAlgError) as error:
        return base | {"gates": ["fitting_failed"], "error": str(error)}, None
    labels = pd.Series(candidate.labels, index=frame.index)
    metrics = evaluate(coordinates, candidate.labels, groups)
    common_metrics = evaluate(common.transform(frame), candidate.labels, groups)
    associations = generator_associations(frame, candidate.labels)
    evidence = base | {
        "development": metrics,
        "common_silhouette": common_metrics["silhouette"],
        "model_details": candidate.details(coordinates),
        "converged": candidate.converged,
        "associations": associations,
        "profiles": profiles(frame, labels, coordinates),
    }
    gates = []
    if not candidate.converged:
        gates.append("non_convergence")
    if not metrics["supported"]:
        gates.append("development_cluster_support")
    if any(size == 0 for size in metrics["counts"]):
        gates.append("degenerate_labels")
    if len(frame) < PROTOCOL["minimum_assignment_share"] * full_populations[0]:
        gates.append("development_assignment_coverage")
    if (
        common_metrics["silhouette"] is None
        or common_metrics["silhouette"] < PROTOCOL["minimum_silhouette_common_space"]
    ):
        gates.append("development_separation")
    working = (
        FrozenAssignment(pipeline, candidate)
        if candidate.model is not None and candidate.converged
        else None
    )
    if candidate.family == "Ward":
        gates.append("no_native_assignment")
    if working is not None:
        later_labels, _, temporal = working.apply(val)
        temporal["assigned"] = len(later_labels)
        temporal["common_silhouette"] = evaluate(
            common.transform(val.loc[later_labels.index]), later_labels.to_numpy(), groups
        )["silhouette"]
        evidence["validation"] = temporal
        shared = labels.index.intersection(later_labels.index)
        evidence["validation_shared"] = len(shared)
        evidence["validation_ari"] = (
            adjusted_rand_score(labels.loc[shared], later_labels.loc[shared])
            if len(shared) > 1
            else None
        )
        if not temporal["supported"]:
            gates.append("validation_cluster_support")
        if len(later_labels) < PROTOCOL["minimum_assignment_share"] * full_populations[1]:
            gates.append("validation_assignment_coverage")
        if (
            temporal["common_silhouette"] is None
            or temporal["common_silhouette"] < PROTOCOL["minimum_silhouette_common_space"]
        ):
            gates.append("validation_separation")
    if candidate.converged and metrics["supported"]:
        repeats = stability(frame, pipeline, candidate)
        evidence["stability"] = repeats
        if not stability_passes(repeats):
            gates.append("stability")
    if (
        max(associations["nmi"].values()) > PROTOCOL["maximum_generator_nmi"]
        or associations["cadence_homogeneity"] > PROTOCOL["maximum_cadence_homogeneity"]
    ):
        gates.append("generator_dominance")
    return evidence | {"gates": gates}, (candidate, labels)


def _selection(candidates: list[dict]) -> dict | None:
    viable = [candidate for candidate in candidates if not candidate["gates"]]
    if not viable:
        return None
    strongest = max(candidate["common_silhouette"] for candidate in viable)
    close = [
        row for row in viable if row["common_silhouette"] >= strongest - PROTOCOL["silhouette_tie"]
    ]
    return min(
        close,
        key=lambda row: (
            -(row["validation_ari"] if row["validation_ari"] is not None else -1.0),
            row["groups"],
            FAMILIES.index(row["family"]),
            row["space"],
        ),
    )


def _fit_all(fit: pd.DataFrame, validation: pd.DataFrame, spaces: dict):
    common = fit_preprocessing(fit, spaces["FS-01"])
    settings = {}
    candidates = []
    fitted = {}
    for space, blocks in spaces.items():
        frame = fit.loc[valid_rows(fit, blocks)]
        pipeline = fit_preprocessing(frame, blocks)
        coordinates = pipeline.transform(frame)
        pca = PCA(svd_solver="full").fit(coordinates)
        settings[space] = pipeline.describe() | {
            "raw_quality": frame[list(name for names in blocks.values() for name in names)]
            .nunique()
            .to_dict(),
            "transformed_standard_deviation": coordinates.std(axis=0).tolist(),
            "pca": {
                "ratios": pca.explained_variance_ratio_.tolist(),
                "loadings": pca.components_.tolist(),
                "eigenvalues": pca.explained_variance_.tolist(),
            },
        }
        for family in FAMILIES:
            for groups in PROTOCOL["groups"]:
                result, fitted_candidate = _candidate(
                    space,
                    frame,
                    validation,
                    (len(fit), len(validation)),
                    pipeline,
                    coordinates,
                    common,
                    family,
                    groups,
                )
                candidates.append(result)
                if fitted_candidate is not None:
                    candidate, labels = fitted_candidate
                    fitted[result["id"]] = (pipeline, candidate, labels, pca)

        representative = {}
        for family in FAMILIES:
            comparable = [
                row
                for row in candidates
                if row["space"] == space
                and row["family"] == family
                and row.get("development", {}).get("silhouette") is not None
            ]
            if not comparable:
                continue
            selected = max(
                comparable,
                key=lambda row: (
                    row["development"]["supported"],
                    row["converged"],
                    row["development"]["silhouette"],
                    -row["groups"],
                ),
            )
            _, example, _, _ = fitted[selected["id"]]
            representative[family] = {
                "id": selected["id"],
                "projected": pca.transform(coordinates)[:, :2].tolist(),
                "labels": example.labels.tolist(),
                "hierarchy": example.hierarchy.tolist() if example.hierarchy is not None else None,
            }
        settings[space]["representative"] = representative

    sensitivity = []
    for left, right in combinations(spaces, 2):
        for family in FAMILIES:
            for groups in PROTOCOL["groups"]:
                left_key, right_key = (
                    f"{left} / {family} / {groups}",
                    f"{right} / {family} / {groups}",
                )
                if left_key in fitted and right_key in fitted:
                    a, b = fitted[left_key][2], fitted[right_key][2]
                    shared = a.index.intersection(b.index)
                    sensitivity.append(
                        {
                            "left": left_key,
                            "right": right_key,
                            "shared": len(shared),
                            "ari": adjusted_rand_score(a.loc[shared], b.loc[shared]),
                        }
                    )
    return settings, candidates, fitted, sensitivity


def _evaluate_frozen(frozen, pca, population):
    frame = population.frame()
    labels, points, metrics = frozen.apply(frame)
    return labels, {
        "date": population.observation.date().isoformat(),
        "primary_eligible": len(frame),
        "assigned": len(labels),
        "unassignable": len(frame) - len(labels),
        "metrics": metrics,
        "profiles": profiles(frame, labels, points),
        "associations": generator_associations(frame.loc[labels.index], labels.to_numpy())
        if len(labels)
        else None,
        "projected": pca.transform(points)[:, :2].tolist() if len(points) else [],
        "labels": labels.tolist(),
        "membership_confidence": frozen.candidate.model.predict_proba(points).max(axis=1).tolist()
        if len(points) and frozen.candidate.family == "GMM"
        else None,
    }


def run(workspace: Path) -> None:
    """Freeze all pre-fit artefacts before fitting and gate the one reserve evaluation."""
    workspace.mkdir(parents=True, exist_ok=False)
    reserve_home = workspace / "reserve"
    reserve_home.mkdir()
    _write(workspace / "protocol.json", PROTOCOL)
    with fieldwise_reference(registry_path=workspace / "development-registry.sqlite") as (run, _):
        source = SourceEvidence.from_verified_reference(run)
    populations, audits = development_populations(source)
    fit, validation, assessment = populations
    usage_gate = behaviour_gate(fit, validation)
    spaces = {
        name: blocks
        for name, blocks in PROTOCOL["feature_spaces"].items()
        if name != "FS-03" or usage_gate["passed"]
    }
    references = fit_references(fit.eligible)
    _write(workspace / "rfm_boundaries.json", asdict(references))
    joblib.dump(references, workspace / "rfm-boundaries.joblib")
    with fieldwise_reference(
        registry_path=reserve_home / "registry.sqlite",
        master_seed=RESERVE_SEED,
        client_scope=RESERVE_SCOPE,
    ) as (run, export):
        reserve_source = SourceEvidence.from_verified_reference(run)
        shutil.copytree(export, reserve_home / "source")
    if assessment.observation.date().isoformat() != PROTOCOL["reserve_observation"]:
        raise RuntimeError("Fixed reserve date is inconsistent with the protocol.")
    reserve_feasibility = observe(
        reserve_source, reserve_source.ledger.cutoff, include_usage=False
    ).audit()
    for key in (
        "usage_period_counts",
        "eligible_with_any_usage",
        "eligible_with_full_usage",
        "cadence_eligible",
    ):
        reserve_feasibility.pop(key)
    _write(
        reserve_home / "manifest.json",
        {
            "seed": RESERVE_SEED,
            "scope": RESERVE_SCOPE,
            "source": reserve_source.provenance,
            "registry_sha256": digest(reserve_home / "registry.sqlite"),
            "feasibility": reserve_feasibility,
        },
    )
    design = {
        "protocol": PROTOCOL,
        "protocol_sha256": digest(workspace / "protocol.json"),
        "development": source.provenance,
        "development_registry_sha256": digest(workspace / "development-registry.sqlite"),
        "reserve_manifest_sha256": digest(reserve_home / "manifest.json"),
        "feasibility": audits,
        "chosen_dates": [row.observation.date().isoformat() for row in populations],
        "behaviour_gate": usage_gate,
        "usage_reporting_lag_days": source.usage_lag_days,
        "active_spaces": spaces,
        "feature_dictionary": feature_dictionary(),
        "rfm_boundaries": asdict(references),
        "rfm_boundaries_sha256": digest(workspace / "rfm-boundaries.joblib"),
    }
    _write(workspace / "design.json", design)
    _write(workspace / "run-started.json", {"design_sha256": digest(workspace / "design.json")})
    print("Phase 08 design frozen. Fitting development candidates.", flush=True)

    with threadpool_limits(limits=1):
        transforms, candidates, fitted, sensitivity = _fit_all(
            fit.frame(), validation.frame(), spaces
        )
        selected = _selection(candidates)
        temporal = None
        independent = {"status": "unscored_no_nominee", "feasibility": reserve_feasibility}
        if selected is not None:
            pipeline, candidate, _, pca = fitted[selected["id"]]
            frozen = FrozenAssignment(pipeline, candidate)
            joblib.dump((frozen, pca), workspace / "nominated.joblib")
            _write(
                workspace / "frozen.json",
                {
                    "nominee": selected["id"],
                    "design_sha256": digest(workspace / "design.json"),
                    "model_sha256": digest(workspace / "nominated.joblib"),
                },
            )
            transfers = [_evaluate_frozen(frozen, pca, population) for population in populations]
            temporal = {
                "snapshots": [evidence for _, evidence in transfers],
                "migration": [
                    migration(
                        transfers[i][0],
                        transfers[i + 1][0],
                        populations[i].frame(eligible=False),
                        populations[i + 1].frame(eligible=False),
                    )
                    for i in range(len(populations) - 1)
                ],
            }
            _write(
                reserve_home / "evaluation-started.json",
                {
                    "frozen_sha256": digest(workspace / "frozen.json"),
                },
            )
            reserved = observe(
                reserve_source,
                reserve_source.ledger.cutoff,
                include_usage="behavioural" in pipeline.inputs,
            )
            _, reserve_results = _evaluate_frozen(frozen, pca, reserved)
            _write(reserve_home / "evaluation.json", reserve_results)
            independent = {
                "status": "evaluated_frozen_nominee_only",
                "feasibility": reserve_feasibility,
                "results": reserve_results,
            }
        report = {
            "design": design,
            "rfm": reference_report(populations, references),
            "transformations": transforms,
            "candidates": candidates,
            "sensitivity": sensitivity,
            "nominee": selected["id"] if selected is not None else None,
            "temporal": temporal,
            "reserve": independent,
        }
        _write(workspace / "report.json", report)
    files = ("protocol.json", "design.json", "report.json")
    _write(workspace / "manifest.json", {name: digest(workspace / name) for name in files})
    print(f"Phase 08 research completed. Nominee: {report['nominee']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    run(parser.parse_args().workspace)
