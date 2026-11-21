"""Build approved six-calendar-month billed-value outcomes independently of features."""

from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, time
from decimal import Decimal
from enum import StrEnum

from ...data.synthetic.churn_experiment import utc_instant
from .history import ZERO_GBP, HistoryLedger


class TargetState(StrEnum):
    POSITIVE = "mature_positive"
    ZERO = "mature_zero"
    IMMATURE = "immature"
    INCOMPLETE = "incomplete_financial_evidence"
    UNRESOLVED = "unresolved_adjustments"
    INELIGIBLE = "ineligible"


@dataclass(frozen=True, slots=True)
class BilledTarget:
    """Keep an unknown outcome distinct from a mature confirmed zero."""

    customer_id: str
    observed_at: datetime
    horizon_end: datetime
    state: TargetState
    future_6m_issued_gbp: Decimal | None


def six_month_end(observed_at: datetime) -> datetime:
    """Shift six UTC calendar months, clamping only an invalid target day."""
    observed = utc_instant(observed_at)
    year, month = divmod(observed.year * 12 + observed.month - 1 + 6, 12)
    return observed.replace(
        year=year, month=month + 1, day=min(observed.day, monthrange(year, month + 1)[1])
    )


class TargetBuilder:
    """Index canonical ownership and explicit evidence once for repeated observations."""

    def __init__(self, ledger: HistoryLedger, *, complete_through: datetime | None) -> None:
        self.ledger = ledger
        self.complete_through = utc_instant(complete_through) if complete_through else None
        if self.complete_through and self.complete_through > utc_instant(ledger.cutoff):
            raise ValueError("Completeness cannot extend beyond the source ledger.")
        self.customers = {row.customer_id: row.created_at for row in ledger.customers}
        owners = {row.episode.subscription_id: row.episode.customer_id for row in ledger.episodes}
        self.issues = defaultdict(list)
        for row in ledger.charges or ():
            invoice, evidence = row.invoice, row.payment_event
            issue = datetime.combine(invoice.invoice_date, time.min, UTC)
            available = max(
                map(
                    utc_instant,
                    (
                        evidence.occurred_at,
                        evidence.effective_at,
                        evidence.available_at,
                    ),
                )
            )
            self.issues[owners[invoice.subscription_id]].append((issue, available, invoice.amount))

    def at(
        self,
        customer_id: str,
        observation: datetime,
        *,
        ascertained_at: datetime,
        unresolved_adjustments: bool = False,
    ) -> BilledTarget:
        """Use issues in (observation, horizon] and evidence known by ascertainment."""
        observed, ascertained = map(utc_instant, (observation, ascertained_at))
        horizon = six_month_end(observed)
        created = self.customers.get(customer_id)
        amount = None
        if (
            created is None
            or not self.ledger.history_start <= observed.date()
            or not created <= observed.date()
            or observed > utc_instant(self.ledger.cutoff)
        ):
            state = TargetState.INELIGIBLE
        elif horizon > min(ascertained, utc_instant(self.ledger.cutoff)):
            state = TargetState.IMMATURE
        elif unresolved_adjustments:
            state = TargetState.UNRESOLVED
        elif (
            self.ledger.charges is None
            or self.complete_through is None
            or horizon > self.complete_through
        ):
            state = TargetState.INCOMPLETE
        else:
            qualifying = [row for row in self.issues[customer_id] if observed < row[0] <= horizon]
            if any(available > ascertained for _, available, _ in qualifying):
                state = TargetState.INCOMPLETE
            else:
                amount = sum((value for _, _, value in qualifying), ZERO_GBP)
                state = TargetState.POSITIVE if amount > 0 else TargetState.ZERO
        return BilledTarget(customer_id, observed, horizon, state, amount)
