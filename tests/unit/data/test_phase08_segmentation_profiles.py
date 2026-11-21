"""Exercise the descriptive segmentation evidence contract."""

from dataclasses import asdict, replace
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import pandas as pd
import pytest

from nowa_customer_intelligence.data.synthetic.billing import (
    BillingFrequency,
    InvoiceFact,
    InvoiceStatus,
    PaymentEvent,
    ScheduledCharge,
)
from nowa_customer_intelligence.data.synthetic.customers import CustomerRecord
from nowa_customer_intelligence.data.synthetic.episodes import EpisodeStatus, SubscriptionEpisode
from nowa_customer_intelligence.data.synthetic.identity_registry import EpisodeIdentity
from nowa_customer_intelligence.data.synthetic.lifecycle import (
    GeneratedEpisode,
    LifecycleFact,
    LifecycleKind,
)
from nowa_customer_intelligence.models.clv.history import HistoryLedger
from nowa_customer_intelligence.models.segmentation.diagnostics import numeric_quality
from nowa_customer_intelligence.models.segmentation.profiles import profile_accounts, window_start


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def episode(number: int, start: datetime, close: datetime | None = None, prior=None):
    key = str(UUID(int=number, version=4))
    stamps = [(kind, start) for kind in (LifecycleKind.ESTABLISHED, LifecycleKind.ACTIVATED)]
    if prior:
        stamps.append((LifecycleKind.REACTIVATED, start))
    if close:
        stamps.append((LifecycleKind.TERMINATED, close))
    return GeneratedEpisode(
        EpisodeIdentity("fiction", "fixture", str(number), str(number)),
        SubscriptionEpisode(
            key,
            "owner",
            start.date(),
            EpisodeStatus.EXPIRED if close else EpisodeStatus.ACTIVE,
            end_date=close.date() if close else None,
        ),
        start.date(),
        tuple(LifecycleFact(key, kind, stamp, stamp, stamp) for kind, stamp in stamps),
        prior,
    )


def charge(episode, name, day, amount, *, lag=0, cadence=BillingFrequency.MONTHLY):
    issued = instant(day)
    status = InvoiceStatus.FAILED
    return ScheduledCharge(
        InvoiceFact(name, episode.episode.subscription_id, issued.date(), Decimal(amount), status),
        issued.date() + timedelta(days=30),
        "launch",
        cadence,
        Decimal("79"),
        PaymentEvent(name, status, issued, issued, issued + timedelta(days=lag)),
    )


@pytest.fixture
def ledger() -> HistoryLedger:
    predecessor = episode(1, instant("2023-01-01"), instant("2024-01-01"))
    successor = episode(2, instant("2024-01-02"), prior=predecessor.episode.subscription_id)
    concurrent = episode(3, instant("2024-01-03"))
    return HistoryLedger(
        (
            CustomerRecord("owner", date(2023, 1, 1), "GB"),
            CustomerRecord("quiet", date(2023, 1, 1), "GB"),
            CustomerRecord("new", date(2024, 1, 4), "GB"),
            CustomerRecord("future", date(2024, 2, 5), "GB"),
        ),
        (predecessor, successor, concurrent),
        (
            charge(predecessor, "boundary", "2023-01-31", "12.50", cadence=BillingFrequency.ANNUAL),
            charge(predecessor, "first", "2023-02-01", "0.10"),
            charge(successor, "at-observation", "2024-01-31", "0.20"),
            charge(concurrent, "other-episode", "2024-01-31", "1.00"),
            charge(successor, "late", "2024-01-30", "90", lag=2),
        ),
        (),
        date(2023, 1, 1),
        instant("2024-02-29"),
    )


def test_rfm_observation_window_distinct_episodes_and_late_issue(ledger: HistoryLedger) -> None:
    by_id = {row.customer_id: row for row in profile_accounts(ledger, instant("2024-01-31"))}
    owner = by_id["owner"]
    assert set(by_id) == {"owner", "quiet", "new"}
    assert owner.calendar_history_complete
    assert not by_id["new"].calendar_history_complete
    assert owner.established_episodes == 3 and owner.active_episodes == 2
    assert owner.completed_episodes == owner.reactivated_episodes == 1
    assert owner.cadence == "mixed"
    assert (owner.frequency, owner.recency_days) == (3, 0)
    assert owner.monetary_gbp == Decimal("1.30")
    assert owner.all_observed_gbp == Decimal("13.80")
    assert owner.contractual_gbp_per_month is None
    by_id = {row.customer_id: row for row in profile_accounts(ledger, instant("2024-02-01"))}
    assert by_id["owner"].monetary_gbp == Decimal("91.20")


def test_zero_issuance_unknown_feed_and_history_exposure(ledger: HistoryLedger) -> None:
    observed = instant("2024-01-31")
    by_id = {row.customer_id: row for row in profile_accounts(ledger, observed)}
    quiet = by_id["quiet"]
    assert quiet.invoice_feed_available and quiet.calendar_history_complete
    assert (quiet.recency_days, quiet.frequency, quiet.monetary_gbp) == (None, 0, Decimal(0))
    assert quiet.contractual_gbp_per_month == Decimal(0)
    unknown = profile_accounts(replace(ledger, charges=None), observed)
    assert all(
        not row.invoice_feed_available
        and row.frequency is row.recency_days is row.monetary_gbp is None
        for row in unknown
    )
    short_source = replace(ledger, history_start=date(2023, 2, 1))
    assert all(
        not row.calendar_history_complete for row in profile_accounts(short_source, observed)
    )


def test_recency_uses_visible_history_beyond_trailing_window(ledger: HistoryLedger) -> None:
    single = replace(ledger, charges=ledger.charges[:1])
    by_id = {row.customer_id: row for row in profile_accounts(single, instant("2024-01-31"))}
    owner = by_id["owner"]
    assert (owner.recency_days, owner.frequency, owner.monetary_gbp) == (365, 0, Decimal(0))


def test_window_utc_and_leap_boundary() -> None:
    observation = datetime(2024, 3, 1, 1, tzinfo=timezone(timedelta(hours=2)))
    assert window_start(observation) == instant("2023-02-28T23:00:00")
    with pytest.raises(ValueError, match="timezone-aware"):
        window_start(datetime(2024, 2, 29))


def test_quality_preserves_concentrated_atoms_and_missingness(ledger: HistoryLedger) -> None:
    rows = profile_accounts(ledger, instant("2024-01-31"))
    frame = pd.DataFrame.from_records(asdict(row) for row in rows)
    quality = numeric_quality(frame)
    assert quality.loc["recency_days", "Missing"] == 2
    assert quality.loc["frequency", "Distinct"] == 2
    assert quality.loc["frequency", "Largest atom share"] == pytest.approx(2 / 3)
    repeated = numeric_quality(pd.concat([frame.iloc[[0]]] * 4))
    assert repeated.loc["frequency", "IQR"] == 0
    assert pd.isna(repeated.loc["frequency", "Outside Tukey fences"])


def test_calendar_history_requires_verified_source_and_known_financials(ledger) -> None:
    from nowa_customer_intelligence.models.segmentation.population import disposition

    rows = {row.customer_id: row for row in profile_accounts(ledger, instant("2024-01-31"))}
    assert disposition(rows["owner"], True) == "eligible"
    assert disposition(rows["owner"], False) == "insufficient_source_evidence"
    assert disposition(rows["new"], True) == "short_history"
    assert disposition(rows["quiet"], True) == "unavailable_essential_financial_feature"
    assert (
        disposition(replace(rows["owner"], invoice_feed_available=False), True)
        == "insufficient_source_evidence"
    )


def test_rfm_freeze_direction_support_and_decimal_replay(ledger) -> None:
    from json import dumps, loads

    from nowa_customer_intelligence.models.segmentation.rfm import ReferenceScores, fit_references

    owner = next(
        row for row in profile_accounts(ledger, instant("2024-01-31")) if row.customer_id == "owner"
    )
    rows = tuple(
        replace(
            owner,
            customer_id=str(index),
            cadence="monthly",
            recency_days=index,
            frequency=index // 15,
            monetary_gbp=Decimal(index) / Decimal(100),
        )
        for index in range(30)
    )
    fitted = fit_references(rows)
    record = loads(dumps(asdict(fitted), default=str))
    replay = ReferenceScores.from_record(record)
    assert replay == fitted
    assert replay.traditional[2].thresholds == (Decimal("0.09"), Decimal("0.19"))
    assert replay.assign(rows[0], cadence_aware=True) == (3, 1, 1)
    assert replay.assign(rows[-1]) == (1, 3, 3)
    assert replay.assign(replace(rows[0], cadence="mixed"), cadence_aware=True) is None
    assert replay.assign(replace(rows[0], calendar_history_complete=False)) is None
    assert replay.assign(replace(rows[0], recency_days=None)) is None
    outside = replace(rows[0], monetary_gbp=Decimal("999999"), frequency=999)
    assert replay.assign(outside) == (3, 3, 3)
    assert replay.assign(rows[0]) == (3, 1, 1)
    with pytest.raises(ValueError, match="unique"):
        fit_references(rows + (rows[0],))


def usage_row(subscription_id, start, end, available, counts):
    from nowa_customer_intelligence.data.synthetic.observations import UsageRecord

    return UsageRecord(
        subscription_id,
        date.fromisoformat(start),
        date.fromisoformat(start),
        date.fromisoformat(end),
        active_users=counts[0],
        sessions_count=counts[1],
        events_count=counts[2],
        available_at=instant(available),
    )


def test_usage_keeps_zero_late_and_concurrent_evidence_separate(ledger) -> None:
    from nowa_customer_intelligence.models.segmentation.usage import UsageState, account_usage

    predecessor = ledger.episodes[0].episode.subscription_id
    rows = (
        usage_row(predecessor, "2023-11-01", "2023-11-30", "2023-12-01", (0, 0, 0)),
        usage_row(predecessor, "2023-12-01", "2023-12-31", "2024-02-05", (9, 8, 7)),
    )
    observed = instant("2024-01-31T23:59:59.999999")
    data = account_usage(ledger, rows, observed, reporting_lag_days=1)
    assert [period.state for period in data["owner"].periods] == [
        UsageState.OBSERVED,
        UsageState.MISSING,
        UsageState.AMBIGUOUS,
    ]
    assert [period.state for period in data["quiet"].periods] == [UsageState.STRUCTURAL] * 3
    assert data["owner"].features()["observed_usage_periods"] == 1
    assert data["owner"].features()["latest_active_users"] == 0
    assert data["owner"].features()["mean_events"] == 0
    assert data["owner"].features()["change_sessions"] is None


def test_usage_fixed_month_boundary_pending_and_comparable_changes(ledger) -> None:
    from nowa_customer_intelligence.models.segmentation.usage import (
        UsageState,
        account_usage,
        usage_months,
    )

    predecessor = episode(1, instant("2023-01-01"))
    ledger = replace(ledger, episodes=(predecessor,), charges=())
    key = predecessor.episode.subscription_id
    rows = (
        usage_row(key, "2023-11-01", "2023-11-30", "2023-12-01", (3, 4, 5)),
        usage_row(key, "2023-12-01", "2023-12-31", "2024-01-01", (4, 5, 6)),
        usage_row(key, "2024-01-01", "2024-01-31", "2024-02-01", (5, 6, 7)),
    )
    midnight = instant("2024-02-01")
    cutoff = midnight - timedelta(microseconds=1)
    assert usage_months(cutoff) == usage_months(midnight)
    before = account_usage(ledger, rows, cutoff, reporting_lag_days=1)["owner"]
    after = account_usage(ledger, rows, midnight, reporting_lag_days=1)["owner"]
    assert before.periods[-1].state is UsageState.PENDING
    assert before.features()["change_events"] is None
    assert after.features()["change_events"] == 2
    assert after.features()["mean_active_users"] == 4
    with pytest.raises(ValueError, match="Duplicate visible"):
        account_usage(ledger, rows + (rows[0],), midnight, reporting_lag_days=1)


def test_usage_reconciles_every_account_month_without_changing_financial_profiles(ledger) -> None:
    from collections import Counter

    from nowa_customer_intelligence.models.segmentation.population import SourceEvidence, observe
    from nowa_customer_intelligence.models.segmentation.usage import UsageState

    active = episode(4, instant("2023-01-01"))
    active = replace(active, episode=replace(active.episode, customer_id="quiet"))
    ledger = replace(ledger, episodes=(*ledger.episodes, active))
    predecessor = ledger.episodes[0].episode.subscription_id
    rows = (
        usage_row(predecessor, "2023-11-01", "2023-11-30", "2023-12-01", (0, 0, 0)),
        usage_row(predecessor, "2023-12-01", "2023-12-31", "2024-02-05", (9, 8, 7)),
        usage_row(
            active.episode.subscription_id, "2023-12-01", "2023-12-30", "2023-12-31", (4, 5, 6)
        ),
    )
    cutoff = instant("2024-01-31T23:59:59.999999")
    source = SourceEvidence(ledger, rows, 1, {})
    financial = observe(source, cutoff, include_usage=False)
    population = observe(source, cutoff)
    accounts = population.usage
    months = [date(2023, 11, 1), date(2023, 12, 1), date(2024, 1, 1)]
    assert set(accounts) == {"owner", "quiet", "new"}
    assert all(
        [period.month for period in result.periods] == months for result in accounts.values()
    )

    statuses = Counter(period.state for result in accounts.values() for period in result.periods)
    assert statuses == {
        UsageState.OBSERVED: 1,
        UsageState.MISSING: 2,
        UsageState.AMBIGUOUS: 1,
        UsageState.PARTIAL: 1,
        UsageState.PENDING: 1,
        UsageState.STRUCTURAL: 3,
    }
    assert sum(statuses.values()) == len(accounts) * len(months)
    assert accounts["owner"].periods[0].counts == (0, 0, 0)
    for result in accounts.values():
        assert all(
            period.counts is None
            for period in result.periods
            if period.state is not UsageState.OBSERVED
        )
    assert population.profiles == financial.profiles
    assert population.statuses == financial.statuses
