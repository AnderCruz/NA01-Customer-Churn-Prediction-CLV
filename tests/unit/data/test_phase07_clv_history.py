"""Verify CLV historical attribution and point-in-time billing evidence."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

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
from nowa_customer_intelligence.data.synthetic.observations import SnapshotRecord
from nowa_customer_intelligence.models.clv.features import customer_features
from nowa_customer_intelligence.models.clv.history import (
    HistoryLedger,
    historical_value,
    issued_concentration,
)
from nowa_customer_intelligence.models.clv.target import TargetBuilder, TargetState, six_month_end


def at(day: int) -> datetime:
    return datetime(2024, 1, day, tzinfo=UTC)


def episode(number: int, opens: int, closes: int | None = None, prior: str | None = None):
    key = str(UUID(int=number, version=4))
    facts = [
        LifecycleFact(key, kind, at(opens), at(opens), at(opens))
        for kind in (
            LifecycleKind.ESTABLISHED,
            LifecycleKind.ACTIVATED,
            *((LifecycleKind.REACTIVATED,) if prior else ()),
        )
    ]
    if closes:
        facts.append(
            LifecycleFact(key, LifecycleKind.TERMINATED, at(closes), at(closes), at(closes))
        )
    return GeneratedEpisode(
        EpisodeIdentity("fiction", "fixture", str(number), str(number)),
        SubscriptionEpisode(
            key,
            "owner",
            at(opens).date(),
            EpisodeStatus.EXPIRED if closes else EpisodeStatus.ACTIVE,
            end_date=at(closes).date() if closes else None,
        ),
        at(opens).date(),
        tuple(facts),
        prior,
    )


def issue(
    row: GeneratedEpisode, key: str, day: int, available: int, amount: str
) -> ScheduledCharge:
    invoice = InvoiceFact(
        key, row.episode.subscription_id, at(day).date(), Decimal(amount), InvoiceStatus.FAILED
    )
    evidence = PaymentEvent(key, InvoiceStatus.FAILED, at(day), at(day), at(available))
    return ScheduledCharge(
        invoice,
        at(day).date() + timedelta(days=30),
        "launch",
        BillingFrequency.MONTHLY,
        Decimal("79"),
        evidence,
    )


@pytest.fixture
def ledger() -> HistoryLedger:
    predecessor = episode(1, 1, closes=10)
    successor = episode(2, 15, prior=predecessor.episode.subscription_id)
    charge_late = issue(predecessor, "late", 1, 4, "10.10")
    charge_later = issue(successor, "later", 15, 15, "0.20")
    charge_zero = issue(successor, "zero", 17, 17, "0.00")
    snapshot = SnapshotRecord(
        successor.episode.subscription_id,
        at(20).date(),
        EpisodeStatus.ACTIVE,
        at(20),
        at(20),
        at(20),
        at(20),
        "launch",
        BillingFrequency.MONTHLY,
        Decimal("79.00"),
        "GBP",
    )
    return HistoryLedger(
        (CustomerRecord("owner", at(1).date(), "GB"), CustomerRecord("other", at(5).date(), "GB")),
        (predecessor, successor),
        (charge_late, charge_later, charge_zero),
        (snapshot,),
        at(1).date(),
        at(31),
    )


def test_retains_canonical_episodes_and_exact_account_rollup(ledger: HistoryLedger) -> None:
    h = historical_value(ledger, at(21))
    account = next(row for row in h.customers if row.customer_id == "owner")
    assert account.billing.issued_gbp == Decimal("10.30")
    assert account.billing.invoice_count == account.billing.monthly_count == 3
    assert account.established_episodes == 2
    assert (
        account.completed_episodes == account.active_episodes == account.reactivated_episodes == 1
    )
    assert account.tenure_days == 20
    assert account.billing.latest_issue_age_days == 4
    assert {row.subscription_id for row in h.episodes} == {
        row.episode.subscription_id for row in ledger.episodes
    }
    assert sum(row.billing.issued_gbp for row in h.episodes) == account.billing.issued_gbp
    assert issued_concentration(h) == (
        (0, Decimal(0)),
        (1, Decimal("10.30")),
        (2, Decimal("10.30")),
    )
    assert h.episodes[1].snapshot_recurring_gbp == Decimal("79.00")


def test_as_of_rejects_late_invoices_future_accounts_episodes_and_snapshots(ledger) -> None:
    observed = historical_value(ledger, at(3))
    assert [row.customer_id for row in observed.customers] == ["owner"]
    assert len(observed.episodes) == 1 and observed.episodes[0].active
    assert not observed.issues
    assert historical_value(ledger, at(4)).issues[0].issued_gbp == Decimal("10.10")
    after_reactivation = historical_value(ledger, at(15))
    assert after_reactivation.episodes[1].snapshot_observed_on is None
    assert after_reactivation.episodes[1].billing.issued_gbp == Decimal("0.20")
    assert (
        historical_value(replace(ledger, history_start=date(2024, 1, 2)), at(21))
        .issues[0]
        .invoice_id
        == "later"
    )
    with pytest.raises(ValueError, match="outside"):
        historical_value(ledger, at(31) + timedelta(seconds=1))


def test_missing_feed_and_observed_zero_issue_have_different_states(ledger) -> None:
    missing = historical_value(replace(ledger, charges=None), at(21))
    assert missing.issues is None and missing.customers[0].billing.issued_gbp is None
    present = historical_value(replace(ledger, charges=(ledger.charges[2],)), at(21))
    empty, owner = present.customers
    assert empty.billing.issued_gbp == owner.billing.issued_gbp == Decimal("0.00")
    assert empty.billing.billing_evidence == "no_observed_issue"
    assert owner.billing.billing_evidence == "issued_evidence"
    assert owner.billing.mean_invoice_gbp == Decimal("0.00")
    assert empty.billing.mean_invoice_gbp is None


@pytest.mark.parametrize("case", ["duplicate", "orphan", "misattributed"])
def test_invalid_invoice_identity_is_rejected(ledger, case: str) -> None:
    charge = ledger.charges[0]
    charges = {
        "duplicate": (charge, charge),
        "orphan": (
            replace(
                charge, invoice=replace(charge.invoice, subscription_id=str(UUID(int=9, version=4)))
            ),
        ),
        "misattributed": (
            replace(charge, payment_event=replace(charge.payment_event, invoice_id="bad")),
        ),
    }
    with pytest.raises(ValueError):
        replace(ledger, charges=charges[case])


def test_concurrent_episode_invoices_are_counted_once_each(ledger) -> None:
    concurrent = episode(3, 6)
    extra = issue(concurrent, "extra", 6, 6, "2.35")
    view = historical_value(
        replace(ledger, episodes=(*ledger.episodes, concurrent), charges=(*ledger.charges, extra)),
        at(7),
    )
    owner = next(row for row in view.customers if row.customer_id == "owner")
    assert owner.active_episodes == 2
    assert owner.billing.issued_gbp == Decimal("12.45")


def test_six_calendar_month_horizon_preserves_utc_and_clamps_leap_day() -> None:
    assert six_month_end(datetime(2023, 8, 31, 12, tzinfo=UTC)) == datetime(
        2024, 2, 29, 12, tzinfo=UTC
    )
    assert six_month_end(datetime(2024, 8, 31, tzinfo=UTC)).date() == date(2025, 2, 28)


def test_future_target_counts_successor_but_never_changes_earlier_features(ledger) -> None:
    cutoff = datetime(2024, 7, 31, tzinfo=UTC)
    ledger = replace(ledger, cutoff=cutoff)
    builder = TargetBuilder(ledger, complete_through=cutoff)
    outcome = builder.at("owner", at(1), ascertained_at=cutoff)
    assert outcome.state is TargetState.POSITIVE
    # The predecessor issued exactly at observation. Only the successor counts here.
    assert outcome.future_6m_issued_gbp == Decimal("0.20")
    historical = customer_features(historical_value(ledger, at(1)))["owner"]
    assert historical["episodes"] == 1 and historical["reactivated"] == 0
    assert historical["issued_gbp"] == 0
    assert "future_6m_issued_gbp" not in historical


def test_exact_end_boundary_and_late_evidence(ledger) -> None:
    cutoff = datetime(2024, 8, 1, tzinfo=UTC)
    end = datetime(2024, 7, 31, tzinfo=UTC)
    observed = at(31)
    prototype = ledger.charges[1]
    bill = replace(
        prototype,
        invoice=replace(prototype.invoice, invoice_date=end.date()),
        payment_event=replace(
            prototype.payment_event, occurred_at=end, effective_at=end, available_at=cutoff
        ),
    )
    ledger = replace(ledger, cutoff=cutoff, charges=(bill,))
    builder = TargetBuilder(ledger, complete_through=cutoff)
    assert builder.at("owner", observed, ascertained_at=end).state is TargetState.INCOMPLETE
    assert builder.at("owner", observed, ascertained_at=cutoff).future_6m_issued_gbp == Decimal(
        "0.20"
    )
    assert (
        builder.at("owner", observed, ascertained_at=cutoff, unresolved_adjustments=True).state
        is TargetState.UNRESOLVED
    )


def test_true_zero_distinct_from_unknown_and_inactive_is_eligible(ledger) -> None:
    cutoff = datetime(2024, 8, 1, tzinfo=UTC)
    ledger = replace(ledger, cutoff=cutoff)
    present = TargetBuilder(ledger, complete_through=cutoff)
    assert present.at("other", at(5), ascertained_at=cutoff).state is TargetState.ZERO
    assert present.at("other", at(3), ascertained_at=cutoff).state is TargetState.INELIGIBLE
    assert present.at("other", at(5), ascertained_at=at(31)).state is TargetState.IMMATURE
    for candidate in (
        TargetBuilder(ledger, complete_through=None),
        TargetBuilder(replace(ledger, charges=None), complete_through=cutoff),
    ):
        unknown = candidate.at("other", at(5), ascertained_at=cutoff)
        assert unknown.state is TargetState.INCOMPLETE
        assert unknown.future_6m_issued_gbp is None


def test_target_aggregates_distinct_concurrent_issues(ledger) -> None:
    cutoff = datetime(2024, 8, 1, tzinfo=UTC)
    concurrent = episode(3, 6)
    added = issue(concurrent, "extra", 6, 6, "2.35")
    ledger = replace(
        ledger,
        cutoff=cutoff,
        episodes=(*ledger.episodes, concurrent),
        charges=(*ledger.charges, added),
    )
    amount = TargetBuilder(ledger, complete_through=cutoff).at(
        "owner", at(1), ascertained_at=cutoff
    )
    assert amount.future_6m_issued_gbp == Decimal("2.55")
