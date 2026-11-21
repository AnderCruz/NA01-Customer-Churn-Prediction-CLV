"""Development-only preprocessing, candidate fitting and frozen assignment."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import cut_tree, linkage
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    homogeneity_score,
    normalized_mutual_info_score,
    silhouette_samples,
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from .protocol import PROTOCOL, minimum_group_size
from .rfm import CADENCES


def valid_rows(frame: pd.DataFrame, blocks: dict) -> pd.Series:
    """Exclude missing essential measures and unknown explicit categories."""
    valid = pd.Series(True, index=frame.index)
    for fields in blocks.values():
        for name in fields:
            if name == "cadence":
                valid &= frame[name].isin(CADENCES)
            else:
                values = frame[name].astype(float)
                valid &= np.isfinite(values)
    if "behavioural" in blocks:
        valid &= frame.observed_usage_periods.eq(3)
    return valid


@dataclass(frozen=True, slots=True)
class Block:
    """One standardised continuous and unscaled one-hot feature block."""

    name: str
    numerical: tuple[str, ...]
    categories: tuple[str, ...]
    scaler: StandardScaler | None

    @property
    def dimensions(self) -> tuple[str, ...]:
        """Record the order of continuous coordinates and one-hot indicators."""
        return self.numerical + tuple(f"cadence={category}" for category in self.categories)

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        """Give the weighted block its mean squared coordinate difference."""
        parts = []
        if self.scaler is not None:
            parts.append(self.scaler.transform(frame[list(self.numerical)].astype(float)))
        if self.categories:
            parts.append(
                np.column_stack([frame.cadence.eq(category) for category in self.categories])
            )
        return np.column_stack(parts) / np.sqrt(len(self.dimensions))


@dataclass(frozen=True, slots=True)
class Preprocessing:
    """A frozen training representation and its essential input contract."""

    inputs: dict
    blocks: tuple[Block, ...]
    dropped: tuple[str, ...]

    @property
    def columns(self) -> tuple[str, ...]:
        """Name all transformed dimensions in their fixed order."""
        return tuple(name for block in self.blocks for name in block.dimensions)

    def eligible(self, frame: pd.DataFrame) -> pd.Series:
        """Reject unknown categories, including a category absent during fitting."""
        valid = valid_rows(frame, self.inputs)
        for block in self.blocks:
            if block.categories:
                valid &= frame.cadence.isin(block.categories)
        return valid

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        """Apply the frozen transformations to rows already admitted."""
        if not self.eligible(frame).all():
            raise ValueError("Unassignable evidence cannot enter the frozen representation.")
        if frame.empty:
            return np.empty((0, len(self.columns)))
        return np.column_stack([block.transform(frame) for block in self.blocks])

    def describe(self) -> dict:
        """Expose fitted parameters without serialising or executing a model."""
        return {
            "columns": self.columns,
            "dropped_constants": self.dropped,
            "blocks": [
                {
                    "name": block.name,
                    "coordinates": block.dimensions,
                    "one_hot_levels": block.categories,
                    "weight": 1 / np.sqrt(len(block.dimensions)),
                    "means": block.scaler.mean_.tolist() if block.scaler is not None else [],
                    "scales": block.scaler.scale_.tolist() if block.scaler is not None else [],
                }
                for block in self.blocks
            ],
        }


def fit_preprocessing(frame: pd.DataFrame, blocks: dict) -> Preprocessing:
    """Estimate scaling on this development population alone."""
    if frame.empty or not frame.index.is_unique or not valid_rows(frame, blocks).all():
        raise ValueError("Preprocessing requires unique and eligible development accounts.")
    fitted = []
    dropped = []
    for name, guess in blocks.items():
        for feature in guess:
            if frame[feature].nunique() <= 1:
                dropped.append(feature)
        numerical = tuple(field for field in guess if field not in dropped and field != "cadence")
        categories = (
            tuple(sorted(frame.cadence.unique()))
            if "cadence" in guess and "cadence" not in dropped
            else ()
        )
        scaler = StandardScaler().fit(frame[list(numerical)].astype(float)) if numerical else None
        if numerical or categories:
            fitted.append(Block(name, numerical, categories, scaler))
    if not fitted:
        raise ValueError("No variable development dimensions.")
    return Preprocessing(blocks, tuple(fitted), tuple(dropped))


@dataclass(frozen=True, slots=True)
class Fit:
    """One fitted candidate, including explicit convergence and native assignment status."""

    family: str
    groups: int
    converged: bool
    labels: np.ndarray
    model: KMeans | GaussianMixture | None
    hierarchy: np.ndarray | None = None

    def assign(self, coordinates: np.ndarray) -> np.ndarray:
        """Apply native frozen assignment for K-Means and the Gaussian mixture."""
        if self.model is None or not self.converged:
            raise ValueError("This candidate does not support frozen assignment.")
        if not len(coordinates):
            return np.empty(0, dtype=int)
        return self.model.predict(coordinates)

    def details(self, coordinates: np.ndarray) -> dict:
        """Capture diagnostics whose meaning is specific to each model family."""
        if isinstance(self.model, KMeans):
            return {
                "inertia": float(self.model.inertia_),
                "iterations": int(self.model.n_iter_),
                "centroid_distances": pdist(self.model.cluster_centers_).tolist(),
            }
        if isinstance(self.model, GaussianMixture):
            return {
                "aic": float(self.model.aic(coordinates)),
                "bic": float(self.model.bic(coordinates)),
                "weights": self.model.weights_.tolist(),
                "means": self.model.means_.tolist(),
                "covariances": self.model.covariances_.tolist(),
                "iterations": int(self.model.n_iter_),
                "membership_confidence": self.model.predict_proba(coordinates).max(axis=1).tolist(),
            }
        return {"merge_distances": self.hierarchy[:, 2].tolist()}


def fit_candidate(family: str, groups: int, coordinates: np.ndarray, seed: int) -> Fit:
    """Fit one fixed clustering configuration with no cross-population tuning."""
    if groups < 2 or groups >= len(coordinates):
        raise ValueError("Candidate group count exceeds the usable population.")
    if family == "Ward":
        hierarchy = linkage(
            coordinates, method=PROTOCOL["ward"]["linkage"], metric=PROTOCOL["ward"]["metric"]
        )
        return Fit(
            family, groups, True, cut_tree(hierarchy, n_clusters=[groups])[:, 0], None, hierarchy
        )
    if family == "K-Means":
        model = KMeans(n_clusters=groups, random_state=seed, **PROTOCOL["kmeans"]).fit(coordinates)
        return Fit(family, groups, model.n_iter_ < model.max_iter, model.labels_, model)
    if family == "GMM":
        configuration = dict(PROTOCOL["gmm"], covariance_type="diag")
        mixture = GaussianMixture(n_components=groups, random_state=seed, **configuration).fit(
            coordinates
        )
        return Fit(family, groups, bool(mixture.converged_), mixture.predict(coordinates), mixture)
    raise ValueError("Unknown clustering family.")


def evaluate(coordinates: np.ndarray, labels: np.ndarray, groups: int) -> dict:
    """Report comparable geometry and reconcile support before using internal metrics."""
    counts = np.bincount(labels, minlength=groups)
    result = {
        "counts": counts.tolist(),
        "smallest_share": float(counts.min() / len(labels)) if len(labels) else 0,
        "supported": bool(counts.min() >= minimum_group_size(len(labels))),
        "silhouette": None,
    }
    if not 1 < np.count_nonzero(counts) < len(labels):
        return result
    samples = silhouette_samples(coordinates, labels)
    means = {group: coordinates[labels == group].mean(axis=0) for group in np.unique(labels)}
    within = sum(
        float(np.square(coordinates[labels == group] - mean).sum()) for group, mean in means.items()
    )
    between = float(np.square(coordinates - coordinates.mean(axis=0)).sum() - within)
    return result | {
        "silhouette": float(samples.mean()),
        "davies_bouldin": float(davies_bouldin_score(coordinates, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(coordinates, labels)),
        "within_sse": within,
        "between_sse": between,
        "silhouette_by_group": {
            str(group): samples[labels == group].tolist() for group in np.unique(labels)
        },
    }


def generator_associations(frame: pd.DataFrame, labels: np.ndarray) -> dict:
    """Compare partitions with fixed, interpretable generator reference attributes."""
    sources = {
        "cadence": frame.cadence,
        "tenure_band": np.digitize(frame.tenure_days, [365, 730, 1095]),
        "reactivated": frame.reactivated_episodes,
        "active_episodes": frame.active_episodes,
        "catalogue_rate": frame.contractual_gbp_per_month.astype(str),
        "history_complete": frame.calendar_history_complete,
    }
    cadence = pd.crosstab(frame.cadence, labels)
    return {
        "nmi": {
            name: normalized_mutual_info_score(values, labels) if len(set(values)) > 1 else 0.0
            for name, values in sources.items()
        },
        "cadence_homogeneity": homogeneity_score(frame.cadence, labels),
        "cadence_counts": {
            name: dict(zip(map(str, counts.index), map(int, counts), strict=True))
            for name, counts in cadence.iterrows()
        },
    }
