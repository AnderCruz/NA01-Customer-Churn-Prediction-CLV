"""Descriptive account profiles from established point-in-time financial evidence."""

from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, time
from decimal import Decimal

from ..clv.history import ZERO_GBP, HistoryLedger, KnownIssue, historical_value


@dataclass(frozen=True, slots=True)
class AccountProfile:
    """One visible account at an observation, before any segmentation eligibility rule."""

    customer_id: str
    observed_at: datetime
    tenure_days: int
    established_episodes: int
    completed_episodes: int
    active_episodes: int
    reactivated_episodes: int
    all_observed_gbp: Decimal | None
    mean_issue_gbp: Decimal | None
    cadence: str
    contractual_gbp_per_month: Decimal | None
    usable_active_snapshots: int
    calendar_history_complete: bool
    invoice_feed_available: bool
    recency_days: int | None
    frequency: int | None
    monetary_gbp: Decimal | None


def window_start(observation: datetime) -> datetime:
    """Return the proposed twelve-calendar-month lower boundary in UTC."""
    if observation.utcoffset() is None:
        raise ValueError("Expected a timezone-aware observation.")
    observed = observation.astimezone(UTC)
    year = observed.year - 1
    last_day = monthrange(year, observed.month)[1]
    return observed.replace(year=year, day=min(observed.day, last_day))


def profile_accounts(ledger: HistoryLedger, observation: datetime) -> tuple[AccountProfile, ...]:
    """Summarise historical evidence without applying a fitting or scoring policy."""
    start = window_start(observation)
    view = historical_value(ledger, observation)
    recent: dict[str, list[KnownIssue]] = defaultdict(list)
    for issue in view.issues or ():
        if start < datetime.combine(issue.issued_on, time.min, UTC):
            recent[issue.customer_id].append(issue)
    snapshot_values: dict[str, list[Decimal]] = defaultdict(list)
    for episode in view.episodes:
        if episode.snapshot_recurring_gbp is not None:
            snapshot_values[episode.customer_id].append(episode.snapshot_recurring_gbp)
    profiles = []
    for row in view.customers:
        summary = row.billing
        available = view.issues is not None
        issues = recent[row.customer_id]
        rates = snapshot_values[row.customer_id]
        if summary.monthly_count and summary.annual_count:
            cadence = "mixed"
        elif summary.monthly_count:
            cadence = "monthly"
        elif summary.annual_count:
            cadence = "annual"
        else:
            cadence = "unobserved"
        profiles.append(
            AccountProfile(
                customer_id=row.customer_id,
                observed_at=view.observed_at,
                tenure_days=row.tenure_days,
                established_episodes=row.established_episodes,
                completed_episodes=row.completed_episodes,
                active_episodes=row.active_episodes,
                reactivated_episodes=row.reactivated_episodes,
                all_observed_gbp=summary.issued_gbp,
                mean_issue_gbp=summary.mean_invoice_gbp,
                cadence=cadence,
                contractual_gbp_per_month=(
                    sum(rates, ZERO_GBP) if len(rates) == row.active_episodes else None
                ),
                usable_active_snapshots=len(rates),
                calendar_history_complete=(
                    datetime.combine(max(view.history_start, row.created_on), time.min, UTC)
                    <= start
                ),
                invoice_feed_available=available,
                recency_days=summary.latest_issue_age_days,
                frequency=len(issues) if available else None,
                monetary_gbp=sum((issue.issued_gbp for issue in issues), ZERO_GBP)
                if available
                else None,
            )
        )
    return tuple(profiles)
