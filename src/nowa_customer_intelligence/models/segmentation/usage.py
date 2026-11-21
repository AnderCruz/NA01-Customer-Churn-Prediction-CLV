"""Conservative three-calendar-month usage evidence at canonical account grain."""

from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum

from ...data.synthetic.churn_experiment import utc_instant
from ...data.synthetic.lifecycle import LifecycleKind
from ...data.synthetic.observations import UsageRecord
from ..clv.history import HistoryLedger

MEASURES = ("active_users", "sessions", "events")


class UsageState(StrEnum):
    """Reason a completed calendar period is usable or unavailable."""

    OBSERVED = "observed"
    STRUCTURAL = "no_known_active_episode"
    AMBIGUOUS = "multiple_episodes"
    PARTIAL = "partial_episode_or_record"
    PENDING = "awaiting_reporting"
    MISSING = "missing_or_unavailable"


@dataclass(frozen=True, slots=True)
class UsagePeriod:
    """Retain the expected calendar period and the visible count vector, if usable."""

    month: date
    state: UsageState
    counts: tuple[int, int, int] | None = None


@dataclass(frozen=True, slots=True)
class AccountUsage:
    """Three expected months, preserving period gaps and observed zeroes."""

    periods: tuple[UsagePeriod, ...]

    def features(self) -> dict[str, int | float | None]:
        """Use known values for descriptive means and comparable endpoints for changes."""
        observed = [period.counts for period in self.periods if period.counts is not None]
        result: dict[str, int | float | None] = {
            "expected_usage_periods": len(self.periods),
            "observed_usage_periods": len(observed),
            "usage_coverage": len(observed) / len(self.periods),
        }
        first, last = self.periods[0].counts, self.periods[-1].counts
        for index, name in enumerate(MEASURES):
            result[f"latest_{name}"] = observed[-1][index] if observed else None
            result[f"mean_{name}"] = (
                sum(counts[index] for counts in observed) / len(observed) if observed else None
            )
            result[f"change_{name}"] = (
                last[index] - first[index] if first is not None and last is not None else None
            )
        return result


def usage_months(observation: datetime) -> tuple[tuple[date, date], ...]:
    """Take the last three complete UTC calendar months, including a closed current month."""
    stamp = utc_instant(observation)
    start = stamp.date().replace(day=1)
    last = start.replace(day=monthrange(start.year, start.month)[1])
    if stamp < datetime.combine(last, time.max, UTC):
        last = start - timedelta(days=1)
    periods = []
    for _ in range(3):
        start = last.replace(day=1)
        periods.append((start, last))
        last = start - timedelta(days=1)
    return tuple(reversed(periods))


def _period(
    month: date,
    end: date,
    intervals: list[tuple[str, date, date]],
    known_rows: dict[tuple[str, date], UsageRecord],
    observed: datetime,
    reporting_lag_days: int,
) -> UsagePeriod:
    overlaps = [
        (key, left, right) for key, left, right in intervals if left <= end and month < right
    ]
    if not overlaps:
        return UsagePeriod(month, UsageState.STRUCTURAL)
    if len(overlaps) > 1:
        return UsagePeriod(month, UsageState.AMBIGUOUS)
    key, left, right = overlaps[0]
    row = known_rows.get((key, month))
    if left > month or right <= end or row and (row.period_start, row.period_end) != (month, end):
        return UsagePeriod(month, UsageState.PARTIAL)
    if row is not None and (
        row.active_users is not None
        and row.sessions_count is not None
        and row.events_count is not None
    ):
        return UsagePeriod(
            month, UsageState.OBSERVED, (row.active_users, row.sessions_count, row.events_count)
        )
    if observed.date() < end + timedelta(days=reporting_lag_days):
        return UsagePeriod(month, UsageState.PENDING)
    return UsagePeriod(month, UsageState.MISSING)


def account_usage(
    ledger: HistoryLedger,
    rows: tuple[UsageRecord, ...],
    observation: datetime,
    *,
    reporting_lag_days: int,
) -> dict[str, AccountUsage]:
    """Require one known, whole-month episode and one available full-period usage row."""
    observed = utc_instant(observation)
    periods = usage_months(observed)
    intervals: dict[str, list[tuple[str, date, date]]] = defaultdict(list)
    episode_ids = {episode.episode.subscription_id for episode in ledger.episodes}
    known_rows = {}
    for row in rows:
        if row.subscription_id not in episode_ids:
            raise ValueError("Usage has no canonical episode.")
        if row.available_at is None or utc_instant(row.available_at) > observed:
            continue
        identity = row.subscription_id, row.usage_month.replace(day=1)
        if identity in known_rows:
            raise ValueError("Duplicate visible episode usage month.")
        known_rows[identity] = row
    for episode in ledger.episodes:
        known = {
            fact.kind: utc_instant(fact.effective_at).date()
            for fact in episode.facts
            if max(fact.effective_at, fact.occurred_at, fact.available_at) <= observed
        }
        if LifecycleKind.ESTABLISHED in known and LifecycleKind.ACTIVATED in known:
            intervals[episode.episode.customer_id].append(
                (
                    episode.episode.subscription_id,
                    known[LifecycleKind.ACTIVATED],
                    known.get(LifecycleKind.TERMINATED, date.max),
                )
            )
    return {
        owner.customer_id: AccountUsage(
            tuple(
                _period(
                    month,
                    end,
                    intervals[owner.customer_id],
                    known_rows,
                    observed,
                    reporting_lag_days,
                )
                if end >= ledger.history_start
                else UsagePeriod(month, UsageState.MISSING)
                for month, end in periods
            )
        )
        for owner in ledger.customers
        if owner.created_at <= observed.date()
    }
