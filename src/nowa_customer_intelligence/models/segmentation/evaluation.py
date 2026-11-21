"""Controlled account-level refits, profile reconciliation and transfer evidence."""

from dataclasses import dataclass
from decimal import Decimal
from math import ceil

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from .clustering import Fit, Preprocessing, evaluate, fit_candidate, fit_preprocessing
from .protocol import PROTOCOL


def _trial(reference: np.ndarray, fit: Fit) -> dict:
    usable = fit.converged and len(np.unique(fit.labels)) == fit.groups
    return {
        "ari": adjusted_rand_score(reference, fit.labels) if usable else None,
        "converged": fit.converged,
        "sizes": np.bincount(fit.labels, minlength=fit.groups).tolist(),
    }


def stability(frame: pd.DataFrame, pipeline: Preprocessing, candidate: Fit) -> dict:
    """Refit on fixed subsets, comparing each partition to the base on identical rows."""
    coordinates = pipeline.transform(frame)
    settings = PROTOCOL
    initialisations = []
    if candidate.family != "Ward":
        for seed in settings["repeat_seeds"]:
            comparison = fit_candidate(candidate.family, candidate.groups, coordinates, seed)
            initialisations.append({"seed": seed} | _trial(candidate.labels, comparison))
    choices = np.random.default_rng(settings["resample_seed"])
    repetitions = []
    for _ in range(settings["resample_repetitions"]):
        indices = np.sort(
            choices.choice(
                len(frame), ceil(len(frame) * settings["resample_fraction"]), replace=False
            )
        )
        sample = frame.iloc[indices]
        modes = {}
        for name, rebuild in (("conditional", False), ("complete_workflow", True)):
            try:
                values = (
                    fit_preprocessing(sample, pipeline.inputs).transform(sample)
                    if rebuild
                    else coordinates[indices]
                )
                comparison = fit_candidate(
                    candidate.family, candidate.groups, values, settings["fit_seed"]
                )
                modes[name] = _trial(candidate.labels[indices], comparison)
            except ValueError as error:
                modes[name] = {"ari": None, "error": str(error)}
        repetitions.append({"shared_accounts": len(indices)} | modes)
    return {"initialisations": initialisations, "resamples": repetitions}


def stability_passes(result: dict) -> bool:
    """Require all controlled comparisons and the predeclared ARI floors."""
    initial = [trial["ari"] for trial in result["initialisations"]]
    if any(value is None or value < PROTOCOL["minimum_initialisation_ari"] for value in initial):
        return False
    for name in ("conditional", "complete_workflow"):
        ari = [trial[name]["ari"] for trial in result["resamples"]]
        if any(value is None for value in ari) or (
            np.median(ari) < PROTOCOL["minimum_median_ari"]
            or np.quantile(ari, 0.10) < PROTOCOL["minimum_p10_ari"]
        ):
            return False
    return True


PROFILE_MEASURES = (
    "tenure_days",
    "recency_days",
    "frequency",
    "monetary_gbp",
    "contractual_gbp_per_month",
    "established_episodes",
    "completed_episodes",
    "active_episodes",
    "reactivated_episodes",
    "observed_usage_periods",
    "usage_coverage",
    "mean_active_users",
    "mean_sessions",
    "mean_events",
    "change_active_users",
    "change_sessions",
    "change_events",
)


def profiles(
    frame: pd.DataFrame, labelled: pd.Series, transformed: np.ndarray | None = None
) -> dict:
    """Summarise original units and reconcile exact issued amounts on the profiled roster."""
    if not labelled.index.is_unique or not labelled.index.isin(frame.index).all():
        raise ValueError("Profile labels must identify unique, visible accounts.")
    frame = frame.loc[labelled.index]
    total = sum(frame.monetary_gbp, Decimal(0))
    output = {}
    for label, members in labelled.groupby(labelled):
        subset = frame.loc[members.index]
        numerical = subset[[name for name in PROFILE_MEASURES if name in subset]].astype(float)
        description = numerical.describe(percentiles=[0.25, 0.5, 0.75])
        output[str(label)] = {
            "accounts": len(members),
            "share": len(members) / len(frame),
            "issued_gbp": str(sum(subset.monetary_gbp, Decimal(0))),
            "cadence": subset.cadence.value_counts().to_dict(),
            "statistics": description.astype(object).where(description.notna(), None).to_dict(),
            "transformed_mean": transformed[labelled.eq(label).to_numpy()].mean(axis=0).tolist()
            if transformed is not None
            else None,
        }
    if (
        sum(group["accounts"] for group in output.values()) != len(frame)
        or sum((Decimal(group["issued_gbp"]) for group in output.values()), Decimal(0)) != total
    ):
        raise RuntimeError("Profile reconciliation failed.")
    return {"accounts": len(frame), "issued_gbp": str(total), "groups": output}


def migration(
    first: pd.Series, second: pd.Series, before: pd.DataFrame, after: pd.DataFrame
) -> dict:
    """Compare frozen labels for common members, reporting roster changes separately."""
    shared = first.index.intersection(second.index)
    previous, current = first.loc[shared], second.loc[shared]
    transition = pd.crosstab(previous.rename("from"), current.rename("to"))
    return {
        "shared_assigned": len(shared),
        "stable": int(previous.eq(current).sum()),
        "changed": int(previous.ne(current).sum()),
        "ari": adjusted_rand_score(previous, current) if len(shared) > 1 else None,
        "transition": {
            str(origin): dict(zip(map(str, values.index), map(int, values), strict=True))
            for origin, values in transition.iterrows()
        },
        "first_assigned": len(first),
        "later_assigned": len(second),
        "newly_visible": len(after.index.difference(before.index)),
        "newly_assignable_existing": len(
            second.index.intersection(before.index).difference(first.index)
        ),
        "formerly_assigned_now_unassignable": len(
            first.index.intersection(after.index).difference(second.index)
        ),
        "ceased_to_be_visible": len(first.index.difference(after.index)),
    }


@dataclass(frozen=True, slots=True)
class FrozenAssignment:
    """Apply a single development model and fixed preprocessing without refitting."""

    preprocessing: Preprocessing
    candidate: Fit

    def apply(self, frame: pd.DataFrame) -> tuple[pd.Series, np.ndarray, dict]:
        """Return explicitly assignable account labels, coordinates and transfer metrics."""
        eligible = frame.loc[frame.disposition.eq("eligible") & self.preprocessing.eligible(frame)]
        points = self.preprocessing.transform(eligible)
        labels = self.candidate.assign(points)
        return (
            pd.Series(labels, index=eligible.index),
            points,
            evaluate(points, labels, self.candidate.groups),
        )
