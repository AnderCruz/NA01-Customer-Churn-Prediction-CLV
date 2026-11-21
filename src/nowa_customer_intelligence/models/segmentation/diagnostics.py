"""Candidate registry and descriptive feature-space checks before segmentation approval."""

from typing import NamedTuple

import pandas as pd


class Feature(NamedTuple):
    """A proposed profile field with its measurement and evidence contract."""

    name: str
    calculation: str
    meaning: str
    source: str
    units: str
    dtype: str
    availability: str
    missing: str
    limitation: str


FEATURES = (
    Feature(
        "tenure_days",
        "Observation date minus account creation date",
        "Observed account age",
        "Account",
        "days",
        "integer",
        "Creation known at observation",
        "Required",
        "Age is not continuous service or source completeness.",
    ),
    Feature(
        "established_episodes",
        "Count known establishments",
        "Contractual history",
        "Lifecycle ledger",
        "count",
        "integer",
        "Lifecycle fact available by observation",
        "Required",
        "Many accounts have only one established episode.",
    ),
    Feature(
        "completed_episodes",
        "Count known terminations",
        "Completed contractual episodes",
        "Lifecycle ledger",
        "count",
        "integer",
        "Lifecycle fact available by observation",
        "Required",
        "Completion is distinct from account inactivity.",
    ),
    Feature(
        "active_episodes",
        "Count known active episodes",
        "Current contractual footprint",
        "Lifecycle ledger",
        "count",
        "integer",
        "Activation and any known termination by observation",
        "Required",
        "The reference has no concurrent active episodes.",
    ),
    Feature(
        "reactivated_episodes",
        "Count known successor reactivations",
        "Historical reactivation",
        "Lifecycle ledger",
        "count",
        "integer",
        "Reactivation known by observation",
        "Required",
        "Fictional reactivation follows a structured mechanism.",
    ),
    Feature(
        "all_observed_gbp",
        "Sum all visible source-window issues",
        "Historical billed value",
        "Invoices",
        "GBP",
        "Decimal",
        "Issue and billing evidence available by observation",
        "Null if feed unavailable",
        "Cumulative value is exposure-dependent.",
    ),
    Feature(
        "mean_issue_gbp",
        "All visible issued GBP divided by visible issue count",
        "Typical issue size by arithmetic mean",
        "Invoices",
        "GBP",
        "Decimal",
        "Issue and billing evidence available by observation",
        "Null with no visible issues",
        "Annual prepayment can dominate the average.",
    ),
    Feature(
        "cadence",
        "Classify visible issue cadence as monthly, annual, mixed or unobserved",
        "Historical billing structure",
        "Invoices",
        "category",
        "string",
        "Issue and billing evidence available by observation",
        "Unobserved without visible issues",
        "Not a prediction-time engagement label.",
    ),
    Feature(
        "contractual_gbp_per_month",
        "Sum usable active snapshot monthly-normalised amounts",
        "Observed contractual rate",
        "Snapshots and lifecycle",
        "GBP/month",
        "Decimal",
        "Known active state and usable snapshots at observation",
        "Null if active rates incomplete",
        "Zero for no known active episodes; not observed issued revenue.",
    ),
    Feature(
        "recency_days",
        "Observation date minus latest visible invoice issue date",
        "Time since last visible issue",
        "Invoices",
        "days",
        "integer",
        "Issue and billing evidence available by observation",
        "Null without a visible issue",
        "Uses available source history, rather than a fabricated age for missing issues.",
    ),
    Feature(
        "frequency",
        "Count unique visible issues inside the proposed trailing window",
        "Observed billing frequency",
        "Invoices",
        "count",
        "integer",
        "Issue inside the window and billing evidence available by observation",
        "Null if feed unavailable",
        "A short account history lowers observed exposure.",
    ),
    Feature(
        "monetary_gbp",
        "Sum visible issued GBP inside the proposed trailing window",
        "Observed billed value",
        "Invoices",
        "GBP",
        "Decimal",
        "Issue inside the window and billing evidence available by observation",
        "Null if feed unavailable",
        "Zero issuance does not imply zero lifetime value.",
    ),
)


def numeric_quality(frame: pd.DataFrame) -> pd.DataFrame:
    """Measure missingness, concentration and tails without fitting a transformer."""
    rows = []
    for feature in FEATURES:
        series = frame[feature.name]
        known = series.dropna()
        is_numeric = feature.dtype != "string"
        values = known.astype(float) if is_numeric else None
        quantile = values.quantile([0.25, 0.75]) if is_numeric and len(known) else None
        iqr = quantile.iloc[1] - quantile.iloc[0] if quantile is not None else None
        tails = (
            int(
                (
                    (values < quantile.iloc[0] - 1.5 * iqr)
                    | (values > quantile.iloc[1] + 1.5 * iqr)
                ).sum()
            )
            if iqr is not None and iqr > 0
            else None
        )
        rows.append(
            {
                "Feature": feature.name,
                "Known": len(known),
                "Missing": len(series) - len(known),
                "Distinct": known.nunique(),
                "Largest atom share": known.value_counts(normalize=True).max()
                if len(known)
                else None,
                "Skew": values.skew()
                if len(known) > 2 and is_numeric and known.nunique() > 1
                else None,
                "IQR": iqr,
                "Outside Tukey fences": tails,
            }
        )
    return pd.DataFrame(rows).set_index("Feature")
