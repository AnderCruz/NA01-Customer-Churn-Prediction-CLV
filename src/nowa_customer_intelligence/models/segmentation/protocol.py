"""Predeclared Phase 08 development and confirmation design."""

from math import ceil

FINANCIAL = ("recency_days", "frequency", "monetary_gbp")
CONTRACTUAL = ("tenure_days", "reactivated_episodes")
BEHAVIOURAL = ("mean_active_users", "mean_sessions", "mean_events")
ASSESSMENT = "2024-03-31"
RESERVE_SEED = 83108
RESERVE_SCOPE = "fieldwise-segmentation-reserve-83108"

PROTOCOL = {
    "name": "fieldwise-segmentation-v0",
    "development_seed": 42,
    "preferred_observations": ("2023-03-31", "2023-12-31", ASSESSMENT),
    "minimum_temporal_gap_months": 3,
    "reserve_seed": RESERVE_SEED,
    "reserve_scope": RESERVE_SCOPE,
    "reserve_observation": ASSESSMENT,
    "minimum_accounts": 200,
    "minimum_cadence_count": 30,
    "minimum_cluster_count": 30,
    "minimum_cluster_share": 0.05,
    "minimum_assignment_share": 0.95,
    "minimum_complete_usage_share": 0.80,
    "minimum_distinct_behavioural_values": 5,
    "feature_spaces": {
        "FS-01": {"financial": FINANCIAL},
        "FS-02": {"financial": FINANCIAL, "contractual": CONTRACTUAL + ("cadence",)},
        "FS-02 without cadence": {"financial": FINANCIAL, "contractual": CONTRACTUAL},
        "FS-03": {
            "financial": FINANCIAL,
            "contractual": CONTRACTUAL + ("cadence",),
            "behavioural": BEHAVIOURAL,
        },
    },
    "scaling": "StandardScaler and equal dimension-adjusted distance blocks",
    "groups": (2, 3, 4, 5, 6),
    "fit_seed": 42,
    "repeat_seeds": (11, 29, 73),
    "resample_seed": 602,
    "resample_repetitions": 20,
    "resample_fraction": 0.80,
    "minimum_median_ari": 0.75,
    "minimum_p10_ari": 0.60,
    "minimum_initialisation_ari": 0.75,
    "minimum_silhouette_common_space": 0.20,
    "maximum_generator_nmi": 0.65,
    "maximum_cadence_homogeneity": 0.75,
    "silhouette_tie": 0.02,
    "kmeans": {"init": "k-means++", "n_init": 20, "max_iter": 300, "tol": 1e-4},
    "ward": {"linkage": "ward", "metric": "euclidean"},
    "gmm": {
        "covariance_type": "diagonal",
        "n_init": 10,
        "max_iter": 200,
        "tol": 1e-3,
        "reg_covar": 1e-6,
    },
}


def minimum_group_size(rows: int) -> int:
    """Require the absolute floor and the minimum population proportion."""
    return max(PROTOCOL["minimum_cluster_count"], ceil(rows * PROTOCOL["minimum_cluster_share"]))
