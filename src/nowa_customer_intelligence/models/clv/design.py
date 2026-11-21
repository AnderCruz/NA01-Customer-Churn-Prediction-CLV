"""Fixed temporal protocol and label-only feasibility for CLV research."""

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from .features import customer_features
from .history import HistoryLedger, historical_value
from .reference import month_ends
from .target import BilledTarget, TargetBuilder

PROTOCOL = "fieldwise-clv-v1"
DEVELOPMENT_SEED = 42
RESERVE_SEED = 731
RESERVE_NAMESPACE = "fieldwise-fictional-clv-reserve"
TRAIN_START = datetime(2021, 6, 1, tzinfo=UTC)
TRAIN_LAST = datetime(2022, 7, 1, tzinfo=UTC)
VALIDATION_START = datetime(2023, 1, 1, tzinfo=UTC)
VALIDATION_LAST = datetime(2023, 3, 1, tzinfo=UTC)
RESERVE_START = datetime(2023, 9, 30, tzinfo=UTC)
MINIMUM = {"training": 150, "validation": 100, "reserve": 100}


@dataclass(frozen=True, slots=True)
class ResearchRow:
    """Separately assembled features and outcome for one customer observation."""

    target: BilledTarget
    predictors: dict


def training_account(customer_id: str) -> bool:
    """Assign accounts using a fixed salted hash independent of labels."""
    digest = sha256(f"{PROTOCOL}:{customer_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % 100 < 70


def assemble(
    ledger: HistoryLedger, *, complete_through: datetime | None, reserve: bool = False
) -> tuple[dict[str, list[ResearchRow]], dict]:
    """Audit eligibility and maturity before assembling fixed research cohorts."""
    # Only verified exhaustive fictional source runs may call this reference protocol.
    builder = TargetBuilder(ledger, complete_through=complete_through)
    partitions = {"reserve": []} if reserve else {"training": [], "validation": []}
    roster = Counter()
    exclusions = Counter()
    for observed in month_ends(ledger):
        view = historical_value(ledger, observed)
        candidate_features = None
        for account in view.customers:
            key = account.customer_id
            outcome = builder.at(key, observed, ascertained_at=ledger.cutoff)
            roster[outcome.state.value] += 1
            if reserve:
                name = (
                    "reserve"
                    if RESERVE_START <= observed < RESERVE_START + timedelta(days=1)
                    else None
                )
                boundary = ledger.cutoff + timedelta(microseconds=1)
            elif training_account(key) and TRAIN_START <= observed < TRAIN_LAST:
                name, boundary = "training", VALIDATION_START
            elif not training_account(key) and VALIDATION_START <= observed < VALIDATION_LAST:
                name, boundary = "validation", RESERVE_START
            else:
                name, boundary = None, ledger.cutoff
            if name is None:
                exclusions["outside_fixed_group_or_calendar"] += 1
                continue
            cutoff_outcome = builder.at(
                key, observed, ascertained_at=boundary - timedelta(microseconds=1)
            )
            if cutoff_outcome.future_6m_issued_gbp is None:
                exclusions[cutoff_outcome.state.value] += 1
                continue
            if candidate_features is None:
                candidate_features = customer_features(view)
            partitions[name].append(ResearchRow(cutoff_outcome, candidate_features[key]))
    return partitions, {"states": dict(roster), "selection_exclusions": dict(exclusions)}


def support(rows: list[ResearchRow]) -> dict:
    """Report observation and distinct-account support for evaluation."""
    zero = [r for r in rows if r.target.future_6m_issued_gbp == 0]
    positive = [r for r in rows if r.target.future_6m_issued_gbp > 0]
    return {
        "observations": len(rows),
        "accounts": len({r.target.customer_id for r in rows}),
        "zero_rows": len(zero),
        "positive_rows": len(positive),
        "zero_accounts": len({r.target.customer_id for r in zero}),
        "positive_accounts": len({r.target.customer_id for r in positive}),
        "monthly_accounts": len({r.target.customer_id for r in rows if r.predictors["monthly"]}),
        "annual_accounts": len({r.target.customer_id for r in rows if r.predictors["annual"]}),
        "first_observation": min((r.target.observed_at.isoformat() for r in rows), default=None),
        "last_observation": max((r.target.observed_at.isoformat() for r in rows), default=None),
    }


def failed_partitions(supports: dict[str, dict]) -> list[str]:
    """Apply fixed support floors before any model fitting."""
    return [
        name
        for name, counts in supports.items()
        if counts["accounts"] < MINIMUM[name]
        or counts["positive_accounts"] < 30
        or min(counts["zero_accounts"], counts["monthly_accounts"], counts["annual_accounts"]) < 15
    ]
