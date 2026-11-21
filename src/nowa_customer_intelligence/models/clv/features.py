"""Customer CLV feature specification and point-in-time assembly."""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from typing import NamedTuple

from .history import ZERO_GBP, HistorySnapshot


class FeatureSpec(NamedTuple):
    name: str
    definition: str
    units: str
    source: str
    nullable: bool


FEATURES = (
    FeatureSpec(
        "tenure_days", "Elapsed time since known account creation", "days", "Customer", False
    ),
    FeatureSpec("episodes", "Known established episodes", "count", "Lifecycle", False),
    FeatureSpec("completed", "Known completed episodes", "count", "Lifecycle", False),
    FeatureSpec("reactivated", "Known reactivated episodes", "count", "Lifecycle", False),
    FeatureSpec("active", "Known active episodes", "count", "Lifecycle", False),
    FeatureSpec("invoice_count", "Visible invoice count", "count", "Invoice", True),
    FeatureSpec("issued_gbp", "Visible window-bounded issuance", "GBP", "Invoice", True),
    FeatureSpec("recent_gbp", "Visible issuance in the last 90 UTC dates", "GBP", "Invoice", True),
    FeatureSpec("mean_invoice_gbp", "Mean visible issue", "GBP", "Invoice", True),
    FeatureSpec("recency_days", "Elapsed time since last visible issue", "days", "Invoice", True),
    FeatureSpec("monthly", "Visible monthly issues", "count", "Invoice", True),
    FeatureSpec("annual", "Visible annual issues", "count", "Invoice", True),
    FeatureSpec("billing_evidence", "Invoice coverage state", "category", "Invoice", False),
    FeatureSpec("cadence", "Observed cadence mix", "category", "Invoice", False),
    FeatureSpec(
        "snapshot_gbp", "Total for fully observed active snapshots", "GBP/month", "Snapshot", True
    ),
    FeatureSpec(
        "snapshot_coverage", "Active episodes with usable amounts", "count", "Snapshot", False
    ),
    FeatureSpec("month", "UTC observation month", "category", "Calendar", False),
)


def customer_features(view: HistorySnapshot) -> dict[str, dict]:
    """Build a predictor-only mapping using one already validated historical view."""
    active_values = defaultdict(list)
    for row in view.episodes:
        if row.snapshot_recurring_gbp is not None:
            active_values[row.customer_id].append(row.snapshot_recurring_gbp)
    recent = defaultdict(lambda: ZERO_GBP)
    start = view.observed_at.date() - timedelta(days=89)
    for row in view.issues or ():
        if row.issued_on >= start:
            recent[row.customer_id] += row.issued_gbp
    output = {}
    for account in view.customers:
        key = account.customer_id
        billing = account.billing
        cadence = "unobserved"
        if billing.monthly_count and billing.annual_count:
            cadence = "mixed"
        elif billing.monthly_count:
            cadence = "monthly"
        elif billing.annual_count:
            cadence = "annual"
        amounts = active_values[key]
        snapshot: Decimal | None = (
            sum(amounts, ZERO_GBP) if len(amounts) == account.active_episodes else None
        )
        values = (
            account.tenure_days,
            account.established_episodes,
            account.completed_episodes,
            account.reactivated_episodes,
            account.active_episodes,
            billing.invoice_count,
            billing.issued_gbp,
            recent[key] if view.issues is not None else None,
            billing.mean_invoice_gbp,
            billing.latest_issue_age_days,
            billing.monthly_count,
            billing.annual_count,
            billing.billing_evidence,
            cadence,
            snapshot,
            len(amounts),
            view.observed_at.strftime("%m"),
        )
        output[key] = dict(zip((s.name for s in FEATURES), values, strict=True))
    return output
