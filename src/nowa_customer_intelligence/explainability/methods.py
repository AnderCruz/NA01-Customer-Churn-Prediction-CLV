"""Bounded, deterministic attribution and sensitivity calculations."""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from math import comb

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

Predict = Callable[[pd.DataFrame], np.ndarray]


@dataclass(frozen=True, slots=True)
class Attribution:
    """A row-wise signed decomposition on one explicitly named output scale."""

    columns: tuple[str, ...]
    values: np.ndarray
    base: np.ndarray
    predictions: np.ndarray

    def reconciliation(self, tolerance: float) -> dict:
        """Verify scalar shape, finiteness and residual tolerance."""
        rows = len(self.predictions)
        if (
            self.values.shape != (rows, len(self.columns))
            or self.base.shape != (rows,)
            or self.predictions.shape != (rows,)
            or len(set(self.columns)) != len(self.columns)
        ):
            raise ValueError("Attribution dimensions or column order are invalid.")
        residual = np.abs(self.base + self.values.sum(axis=1) - self.predictions)
        if not rows or tolerance <= 0 or not np.isfinite(residual).all():
            raise ValueError("Attribution residuals must be finite and non-empty.")
        return {
            "rows": rows,
            "tolerance": tolerance,
            "max_abs_error": float(residual.max()),
            "mean_abs_error": float(residual.mean()),
            "failures": int((residual > tolerance).sum()),
        }


def representative_rows(metadata: pd.DataFrame) -> pd.DataFrame:
    """Choose latest rows per account with stable episode tie-breaking."""
    keys = ["time"] + (["episode"] if "episode" in metadata else [])
    return (
        metadata.sort_values(keys, kind="stable")
        .drop_duplicates("account", keep="last")
        .sort_values("account", kind="stable")
    )


def stratified_sample(metadata: pd.DataFrame, size: int, seed: int) -> pd.Index:
    """Sample distinct account representatives with proportional cadence quotas."""
    representatives = representative_rows(metadata)
    if not len(representatives) or size < 1 or representatives.cadence.isna().any():
        raise ValueError("A non-empty account and cadence sampling frame is required.")
    groups = list(representatives.groupby("cadence", sort=True))
    size = min(size, len(representatives))
    targets = np.array([size * len(rows) / len(representatives) for _, rows in groups])
    quotas = targets.astype(int)
    order = np.argsort(-(targets - quotas), kind="stable")
    quotas[order[: size - quotas.sum()]] += 1
    rng = np.random.default_rng(seed)
    sampled = [
        idx
        for (_, group), quota in zip(groups, quotas, strict=True)
        for idx in rng.choice(group.index.to_numpy(), size=quota, replace=False)
    ]
    return pd.Index(sorted(sampled))


def account_permutation(metadata: pd.DataFrame, rng: np.random.Generator) -> tuple[np.ndarray, int]:
    """Exchange entire trajectories only between accounts with identical timestamp layouts."""
    signatures = defaultdict(list)
    for _, group in metadata.reset_index(drop=True).groupby("account", sort=True):
        keys = ["time"] + (["episode"] if "episode" in group else [])
        ordered = group.sort_values(keys, kind="stable")
        signatures[tuple(ordered.time)].append(ordered.index.to_numpy())
    donor = np.arange(len(metadata))
    eligible = 0
    for group in signatures.values():
        if len(group) < 2:
            continue
        eligible += len(group)
        for recipient, origin in zip(group, rng.permutation(len(group)), strict=True):
            donor[recipient] = group[origin]
    return donor, eligible


def permutation_mae(
    predict: Predict,
    frame: pd.DataFrame,
    metadata: pd.DataFrame,
    targets: np.ndarray,
    groups: dict[str, tuple[str, ...]],
    *,
    repeats: int,
    seed: int,
) -> dict:
    """Measure MAE change when supported account blocks are swapped jointly."""
    if not frame.index.equals(metadata.index) or targets.shape != (len(frame),) or repeats < 2:
        raise ValueError("Permutation requires aligned targets, features and account evidence.")
    base = np.abs(predict(frame) - targets)
    baseline = float(base.mean())
    baseline_balanced = float(
        pd.Series(base, index=frame.index).groupby(metadata.account).mean().mean()
    )
    rng = np.random.default_rng(seed)
    donors = [account_permutation(metadata, rng) for _ in range(repeats)]
    results = {}
    for name, columns in groups.items():
        errors = []
        account_errors = []
        changed_rows = []
        for order, _ in donors:
            incoming = frame.iloc[order][list(columns)].set_axis(frame.index)
            original = frame[list(columns)]
            equal = incoming.eq(original) | (incoming.isna() & original.isna())
            changed = int((~equal.all(axis=1)).sum())
            changed_rows.append(changed)
            shuffled = frame.copy()
            shuffled[list(columns)] = incoming
            loss = np.abs(predict(shuffled) - targets)
            errors.append(float(loss.mean() - baseline))
            balanced = pd.Series(loss, index=frame.index).groupby(metadata.account).mean().mean()
            account_errors.append(float(balanced - baseline_balanced))
        results[name] = {
            "features": list(columns),
            "delta_mae": errors,
            "mean": float(np.mean(errors)),
            "sd": float(np.std(errors, ddof=1)),
            "p05_p95": np.quantile(errors, [0.05, 0.95]).tolist(),
            "account_balanced_delta": account_errors,
            "movable_accounts": donors[0][1],
            "mean_changed_rows": float(np.mean(changed_rows)),
            "supported": any(changed_rows),
        }
    return {"row_mae": baseline, "account_balanced_mae": baseline_balanced, "groups": results}


def group_transformed(attribution: Attribution, originals: list[str]) -> Attribution:
    """Sum signed coordinates for each original feature in the same additive game."""
    if len(originals) != len(attribution.columns):
        raise ValueError("A positional original feature is required for every coordinate.")
    names = tuple(dict.fromkeys(originals))
    values = np.column_stack(
        [attribution.values[:, np.array(originals) == name].sum(axis=1) for name in names]
    )
    return Attribution(names, values, attribution.base, attribution.predictions)


def grouped_shapley(
    predict: Predict,
    examples: pd.DataFrame,
    background: pd.DataFrame,
    groups: dict[str, tuple[str, ...]],
) -> Attribution:
    """Enumerate an exact finite-background Shapley game over coherent raw blocks."""
    all_columns = [feature for part in groups.values() for feature in part]
    if (
        list(examples.columns) != list(background.columns)
        or not examples.columns.is_unique
        or len(set(all_columns)) != len(all_columns)
        or set(all_columns) != set(examples.columns)
        or not 1 <= len(groups) <= 6
        or not len(examples)
        or not len(background)
    ):
        raise ValueError("Shapley blocks must partition the aligned raw feature contract.")
    num_blocks = len(groups)
    repeat = len(background)
    template = pd.concat([background] * len(examples), ignore_index=True)
    replacements = {
        feature: np.repeat(examples[feature].to_numpy(), repeat) for feature in examples
    }
    coalitions = np.empty((2**num_blocks, len(examples)))
    coalitions[0] = np.mean(predict(background))
    for mask in range(1, len(coalitions) - 1):
        matrix = template.copy()
        for index, features in enumerate(groups.values()):
            if mask & (1 << index):
                for column in features:
                    matrix[column] = replacements[column]
        coalitions[mask] = predict(matrix).reshape(len(examples), repeat).mean(axis=1)
    coalitions[-1] = predict(examples)
    values = np.zeros((len(examples), num_blocks))
    for index in range(num_blocks):
        bit = 1 << index
        for mask in range(len(coalitions)):
            if not mask & bit:
                weight = 1 / (num_blocks * comb(num_blocks - 1, mask.bit_count()))
                values[:, index] += weight * (coalitions[mask | bit] - coalitions[mask])
    return Attribution(tuple(groups), values, coalitions[0], coalitions[-1])


def tree_attribution(
    pipeline,
    examples: pd.DataFrame,
    background: pd.DataFrame,
    output: str,
    predictions: np.ndarray,
    *,
    path_dependent: bool = False,
) -> Attribution:
    """Use an explicit TreeSHAP mode and normalise the binary output shape."""
    from shap import TreeExplainer, maskers

    estimator = pipeline[-1]
    features = tuple(pipeline[:-1].get_feature_names_out())
    masker = (
        None
        if path_dependent
        else maskers.Independent(pipeline[:-1].transform(background), max_samples=len(background))
    )
    explainer = TreeExplainer(
        estimator,
        masker,
        model_output=output,
        feature_perturbation="tree_path_dependent" if path_dependent else "interventional",
        feature_names=list(features),
    )
    explained = explainer(pipeline[:-1].transform(examples), check_additivity=False)
    values, bases = np.asarray(explained.values), np.asarray(explained.base_values)
    if values.ndim == 3:
        classes = list(estimator.classes_)
        if len(classes) != 2 or values.shape[2] != 2 or bases.shape != (len(examples), 2):
            raise ValueError("Unexpected class axis in TreeSHAP outputs.")
        values, bases = values[:, :, classes.index(1)], bases[:, classes.index(1)]
    return Attribution(features, values, bases, predictions)


def rank_agreement(first: np.ndarray, second: np.ndarray, *, top: int = 5) -> dict:
    """Report deterministic top-set overlap and tied-rank correlation."""
    if first.ndim != 1 or first.shape != second.shape or not len(first):
        raise ValueError("Ranking vectors must be aligned.")
    limit = min(top, max(1, len(first) // 2))
    a = set(np.argsort(-first, kind="stable")[:limit])
    b = set(np.argsort(-second, kind="stable")[:limit])
    rank = spearmanr(first, second).statistic if np.ptp(first) and np.ptp(second) else None
    return {
        "spearman": float(rank) if rank is not None else None,
        "top_jaccard": len(a & b) / len(a | b),
    }


def sampling_stability(values: np.ndarray, *, seed: int, repeats: int) -> list[dict]:
    """Resample one explained row per account with replacement and compare ranks."""
    rng = np.random.default_rng(seed)
    baseline = np.abs(values).mean(axis=0)
    return [
        rank_agreement(
            baseline, np.abs(values[rng.integers(len(values), size=len(values))]).mean(axis=0)
        )
        for _ in range(repeats)
    ]


def supported_predictions(
    predict: Predict,
    training: pd.DataFrame,
    points: pd.DataFrame,
    interventions: dict[str, float | str],
    *,
    cadence: str,
    coordinates: tuple[str, ...],
    radius: float,
) -> np.ndarray:
    """Return predictions near actual training points in the declared context."""
    modified = points.assign(**interventions)
    result = np.full(len(points), np.nan)
    for category, subset in modified.groupby(cadence, sort=True):
        evidence = training.loc[training[cadence].eq(category), list(coordinates)].dropna()
        if evidence.empty:
            continue
        query = subset[list(coordinates)].to_numpy(dtype=float)
        reference = evidence.to_numpy(dtype=float)
        iqr = np.quantile(reference, 0.75, axis=0) - np.quantile(reference, 0.25, axis=0)
        scale = np.where(iqr > 0, iqr, np.maximum(np.ptp(reference, axis=0), 1e-9))
        distance = np.abs((query[:, None, :] - reference[None, :, :]) / scale).max(axis=-1)
        supported = np.flatnonzero(np.any(distance <= radius, axis=1))
        if len(supported):
            result[points.index.get_indexer(subset.index[supported])] = predict(
                subset.iloc[supported]
            )
    return result
