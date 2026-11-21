"""Point-in-time analysis of fictional GBP invoice issuance and contractual evidence."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Literal

from ...data.synthetic.billing import (
    BillingFrequency,
    PaymentEvent,
    ScheduledCharge,
    validate_invoice_relationships,
)
from ...data.synthetic.churn_experiment import utc_instant
from ...data.synthetic.customers import CustomerRecord
from ...data.synthetic.episodes import EpisodeStatus
from ...data.synthetic.lifecycle import GeneratedEpisode, LifecycleFact, LifecycleKind
from ...data.synthetic.observations import SnapshotRecord

ZERO_GBP = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class HistoryLedger:
    """Source-window-bounded inputs with explicit billing-feed availability."""

    customers: tuple[CustomerRecord, ...]
    episodes: tuple[GeneratedEpisode, ...]
    charges: tuple[ScheduledCharge, ...] | None
    snapshots: tuple[SnapshotRecord, ...]
    history_start: date
    cutoff: datetime

    def __post_init__(self) -> None:
        if self.history_start > utc_instant(self.cutoff).date():
            raise ValueError("The history start exceeds the ledger cutoff.")
        owners = {row.customer_id: row for row in self.customers}
        if len(owners) != len(self.customers):
            raise ValueError("Duplicate customer identity.")
        episodes = {row.episode.subscription_id: row for row in self.episodes}
        if len({key.lower() for key in episodes}) != len(self.episodes):
            raise ValueError("Duplicate episode identity.")
        for key, row in episodes.items():
            owner = owners.get(row.episode.customer_id)
            if owner is None or owner.created_at > row.episode.start_date:
                raise ValueError("Missing or inconsistent episode owner.")
            if any(fact.subscription_id != key for fact in row.facts):
                raise ValueError("Lifecycle evidence belongs to a different episode.")
            starts = [f for f in row.facts if f.kind is LifecycleKind.ESTABLISHED]
            if (
                len(starts) != 1
                or utc_instant(starts[0].effective_at).date() != row.episode.start_date
            ):
                raise ValueError("Expected a single matching establishment fact.")
            prior = episodes.get(row.prior_subscription_id)
            if row.prior_subscription_id is not None and (
                prior is None
                or prior.episode.customer_id != row.episode.customer_id
                or prior.episode.end_date is None
                or prior.episode.end_date > row.episode.start_date
                or prior.episode.start_date >= row.episode.start_date
            ):
                raise ValueError("Inconsistent reactivation lineage.")
        validate_invoice_relationships(
            (row.episode for row in self.episodes),
            (row.invoice for row in self.charges or ()),
        )
        for charge in self.charges or ():
            invoice = charge.invoice
            episode = episodes[invoice.subscription_id].episode
            if (
                charge.payment_event.invoice_id != invoice.invoice_id
                or utc_instant(charge.payment_event.occurred_at) < _midnight(invoice.invoice_date)
                or invoice.invoice_date < episode.start_date
                or episode.end_date is not None
                and invoice.invoice_date >= episode.end_date
                or type(charge.frequency) is not BillingFrequency
                or invoice.currency != "GBP"
                or invoice.amount != invoice.amount.quantize(Decimal("0.01"))
            ):
                raise ValueError("Invalid invoice attribution, availability or GBP precision.")
        keys = set()
        for row in self.snapshots:
            key = (row.subscription_id, utc_instant(row.observed_at))
            if key in keys or row.subscription_id not in episodes:
                raise ValueError("Duplicate or unattributed snapshot.")
            keys.add(key)


@dataclass(frozen=True, slots=True)
class KnownIssue:
    """One invoice visible at an observation, at its original issue date."""

    invoice_id: str
    subscription_id: str
    customer_id: str
    issued_on: date
    available_at: datetime
    cadence: BillingFrequency
    issued_gbp: Decimal


@dataclass(frozen=True, slots=True)
class IssuedSummary:
    """Visible invoice measures within the available source window."""

    issued_gbp: Decimal | None
    invoice_count: int | None
    latest_issue_age_days: int | None
    monthly_count: int | None
    annual_count: int | None
    billing_evidence: Literal["unavailable", "no_observed_issue", "issued_evidence"]

    @property
    def mean_invoice_gbp(self) -> Decimal | None:
        """Return an arithmetic mean only when an issue exists."""
        if self.issued_gbp is not None and self.invoice_count:
            return self.issued_gbp / self.invoice_count
        return None


@dataclass(frozen=True, slots=True)
class EpisodeHistory:
    """Historical episode state, separate from customer aggregation."""

    subscription_id: str
    customer_id: str
    established_on: date
    completed: bool
    active: bool
    reactivated: bool
    snapshot_observed_on: date | None
    snapshot_recurring_gbp: Decimal | None
    billing: IssuedSummary


@dataclass(frozen=True, slots=True)
class CustomerHistory:
    """Observed account tenure and history across its known episodes."""

    customer_id: str
    created_on: date
    tenure_days: int
    established_episodes: int
    completed_episodes: int
    reactivated_episodes: int
    active_episodes: int
    billing: IssuedSummary


@dataclass(frozen=True, slots=True)
class HistorySnapshot:
    """One as-of roll-up. None indicates the invoice feed was unavailable."""

    observed_at: datetime
    history_start: date
    customers: tuple[CustomerHistory, ...]
    episodes: tuple[EpisodeHistory, ...]
    issues: tuple[KnownIssue, ...] | None


def _midnight(day: date) -> datetime:
    return datetime.combine(day, time.min, UTC)


def _as_known(evidence: LifecycleFact | PaymentEvent | SnapshotRecord) -> datetime:
    return max(
        utc_instant(evidence.occurred_at),
        utc_instant(evidence.effective_at),
        utc_instant(evidence.available_at),
    )


def _summarise(issues: list[KnownIssue], observed: date, available: bool) -> IssuedSummary:
    if not available:
        return IssuedSummary(None, None, None, None, None, "unavailable")
    issue_dates = [row.issued_on for row in issues]
    recency = (observed - max(issue_dates)).days if issue_dates else None
    cadence = Counter(row.cadence for row in issues)
    return IssuedSummary(
        sum((row.issued_gbp for row in issues), ZERO_GBP),
        len(issues),
        recency,
        cadence[BillingFrequency.MONTHLY],
        cadence[BillingFrequency.ANNUAL],
        "issued_evidence" if issues else "no_observed_issue",
    )


def historical_value(ledger: HistoryLedger, observed_at: datetime) -> HistorySnapshot:
    """Roll up GBP issuance available at the observation, without future episode evidence."""
    observed = utc_instant(observed_at)
    day = observed.date()
    if day < ledger.history_start or observed > utc_instant(ledger.cutoff):
        raise ValueError("Observation is outside the history window.")
    accounts = {row.customer_id: row for row in ledger.customers if row.created_at <= day}
    latest = {}
    for row in ledger.snapshots:
        stamp = utc_instant(row.observed_at)
        prior = latest.get(row.subscription_id)
        if (
            stamp <= observed
            and _as_known(row) <= observed
            and (prior is None or stamp > utc_instant(prior.observed_at))
        ):
            latest[row.subscription_id] = row

    visible = {}
    for row in ledger.episodes:
        episode = row.episode
        known = {fact.kind: fact for fact in row.facts if _as_known(fact) <= observed}
        if episode.customer_id in accounts and LifecycleKind.ESTABLISHED in known:
            visible[episode.subscription_id] = (episode.customer_id, known)
    issues = []
    episode_issues = defaultdict(list)
    customer_issues = defaultdict(list)
    for charge in ledger.charges or ():
        row = charge.invoice
        attested = _as_known(charge.payment_event)
        if (
            row.subscription_id not in visible
            or not ledger.history_start <= row.invoice_date <= day
            or attested > observed
        ):
            continue
        owner, _ = visible[row.subscription_id]
        issue = KnownIssue(
            row.invoice_id,
            row.subscription_id,
            owner,
            row.invoice_date,
            attested,
            charge.frequency,
            row.amount,
        )
        issues.append(issue)
        episode_issues[row.subscription_id].append(issue)
        customer_issues[owner].append(issue)

    available = ledger.charges is not None
    episodes = []
    account_episodes = defaultdict(list)
    for key, (owner, known) in sorted(visible.items()):
        completed = LifecycleKind.TERMINATED in known
        active = LifecycleKind.ACTIVATED in known and not completed
        snapshot = latest.get(key)
        item = EpisodeHistory(
            key,
            owner,
            utc_instant(known[LifecycleKind.ESTABLISHED].effective_at).date(),
            completed,
            active,
            LifecycleKind.REACTIVATED in known,
            snapshot.snapshot_date if snapshot else None,
            snapshot.recurring_revenue
            if snapshot and active and snapshot.subscription_status is EpisodeStatus.ACTIVE
            else None,
            _summarise(episode_issues[key], day, available),
        )
        episodes.append(item)
        account_episodes[owner].append(item)
    customers = []
    for key, owner in sorted(accounts.items()):
        history = account_episodes[key]
        customers.append(
            CustomerHistory(
                key,
                owner.created_at,
                (day - owner.created_at).days,
                len(history),
                sum(row.completed for row in history),
                sum(row.reactivated for row in history),
                sum(row.active for row in history),
                _summarise(customer_issues[key], day, available),
            )
        )
    return HistorySnapshot(
        observed,
        ledger.history_start,
        tuple(customers),
        tuple(episodes),
        tuple(sorted(issues, key=lambda row: (row.issued_on, row.invoice_id)))
        if available
        else None,
    )


def issued_concentration(snapshot: HistorySnapshot) -> tuple[tuple[int, Decimal], ...]:
    """Return the cumulative issued GBP for accounts ordered by observed value."""
    amounts = sorted(
        (
            row.billing.issued_gbp
            for row in snapshot.customers
            if row.billing.issued_gbp is not None
        ),
        reverse=True,
    )
    total = ZERO_GBP
    points = [(0, total)]
    for rank, amount in enumerate(amounts, 1):
        total += amount
        points.append((rank, total))
    return tuple(points)
