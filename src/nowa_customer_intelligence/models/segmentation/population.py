"""Verified fictional evidence, population dispositions and temporal feasibility."""

from calendar import monthrange
from dataclasses import asdict, dataclass, fields
from datetime import datetime, time

import pandas as pd

from ...data.eda_inputs import fieldwise_reference
from ...data.synthetic.churn_experiment import utc_instant
from ...data.synthetic.observations import UsageRecord
from ...data.synthetic.provenance import ProvenancedDevelopment
from ..clv.history import HistoryLedger
from ..clv.reference import month_ends
from .profiles import AccountProfile, profile_accounts, window_start
from .protocol import ASSESSMENT, BEHAVIOURAL, FINANCIAL, PROTOCOL
from .usage import AccountUsage, account_usage


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    """The verified contract export and bounded generator window used as attestation."""

    ledger: HistoryLedger
    usage: tuple[UsageRecord, ...]
    usage_lag_days: int
    provenance: dict

    @classmethod
    def from_verified_reference(cls, run: ProvenancedDevelopment):
        """Retain the accepted reference window and its five file fingerprints."""
        proof = run.provenance
        if (
            proof.integrity is None
            or not proof.integrity.passed
            or set(proof.expected_inventory)
            != {"customers", "subscriptions", "subscription_snapshots", "usage_monthly", "invoices"}
        ):
            raise ValueError("The verified reference requires all five intact source datasets.")
        result = run.population
        clients = {row.identity.client for row in result.episodes}
        if len(clients) != 1:
            raise ValueError("A Phase 08 source must identify one fictional client.")
        ledger = HistoryLedger(
            result.customers,
            result.episodes,
            result.charges,
            result.snapshots,
            datetime.fromisoformat(proof.parameters.history[0]).date(),
            proof.parameters.observation_cutoff,
        )
        return cls(
            ledger,
            result.usage,
            proof.parameters.scenario.usage.reporting_lag_days,
            {
                "run_id": proof.run_id,
                "source_scope": proof.scope,
                "client_scope": next(iter(clients)),
                "history": proof.parameters.history,
                "cutoff": ledger.cutoff.isoformat(),
                "seed_reference": proof.parameters.seed_reference,
                "scenario": proof.parameters.scenario_id,
                "stream_algorithm": proof.stream_algorithm,
                "policy_references": proof.policy_references,
                "dependencies": dict(proof.dependencies),
                "registry_episode_count": proof.registry_episode_count,
                "files": [asdict(item) for item in proof.integrity.files],
                "coverage": "accepted export of the exhaustive fictional generation window",
            },
        )


def disposition(profile: AccountProfile, covered: bool) -> str:
    """Explain the first failed primary eligibility check for a visible account."""
    if not profile.calendar_history_complete:
        return "short_history"
    if not covered or not profile.invoice_feed_available:
        return "insufficient_source_evidence"
    if any(getattr(profile, field) is None for field in FINANCIAL):
        return "unavailable_essential_financial_feature"
    return "eligible"


@dataclass(frozen=True, slots=True)
class Population:
    """One reconciled set of profiles for a single UTC month end."""

    observation: datetime
    profiles: tuple[AccountProfile, ...]
    statuses: dict[str, str]
    usage: dict[str, AccountUsage]
    total_source_accounts: int

    @property
    def eligible(self) -> tuple[AccountProfile, ...]:
        """Return only the primary modelling population, in canonical account order."""
        return tuple(row for row in self.profiles if self.statuses[row.customer_id] == "eligible")

    def frame(self, *, eligible: bool = True) -> pd.DataFrame:
        """Keep exact financial values and separate usage coverage fields."""
        rows = self.eligible if eligible else self.profiles
        frame = pd.DataFrame.from_records(
            (asdict(row) for row in rows), columns=[field.name for field in fields(AccountProfile)]
        ).set_index("customer_id", verify_integrity=True)
        frame["disposition"] = pd.Series(self.statuses, dtype=object).reindex(frame.index)
        if self.usage:
            usage = pd.DataFrame.from_dict(
                {row.customer_id: self.usage[row.customer_id].features() for row in rows},
                orient="index",
            )
            frame = frame.join(usage)
        return frame

    def audit(self) -> dict:
        """Report reconciled visibility, modelling exclusions and usage support."""
        counts = pd.Series(self.statuses, dtype=str).value_counts().to_dict()
        eligible = self.eligible
        usage = [self.usage[row.customer_id].features() for row in eligible] if self.usage else []
        return {
            "date": self.observation.date().isoformat(),
            "visible": len(self.profiles),
            "not_yet_visible": self.total_source_accounts - len(self.profiles),
            "complete_calendar": sum(row.calendar_history_complete for row in self.profiles),
            "eligible": len(eligible),
            "visible_excluded_unassignable": len(self.profiles) - len(eligible),
            "dispositions": counts,
            "cadence_eligible": pd.Series([row.cadence for row in eligible], dtype=str)
            .value_counts()
            .to_dict(),
            "usage_period_counts": pd.Series(
                [period.state.value for record in self.usage.values() for period in record.periods],
                dtype=str,
            )
            .value_counts()
            .to_dict(),
            "eligible_with_any_usage": sum(row["observed_usage_periods"] > 0 for row in usage),
            "eligible_with_full_usage": sum(row["observed_usage_periods"] == 3 for row in usage),
        }


def observe(source: SourceEvidence, instant: datetime, *, include_usage: bool = True) -> Population:
    """Build point-in-time profiles from the bounded, verified source."""
    instant = utc_instant(instant)
    if instant.time() != time.max or instant.day != monthrange(instant.year, instant.month)[1]:
        raise ValueError("Segmentation observations must be at UTC month end.")
    profiles = profile_accounts(source.ledger, instant)
    covered = source.ledger.history_start <= window_start(instant).date()
    usage = (
        account_usage(
            source.ledger, source.usage, instant, reporting_lag_days=source.usage_lag_days
        )
        if include_usage
        else {}
    )
    return Population(
        instant,
        profiles,
        {row.customer_id: disposition(row, covered) for row in profiles},
        usage,
        len(source.ledger.customers),
    )


def choose_dates(counts: dict[str, dict]) -> tuple[str, str, str]:
    """Use the preferred dates if supported, with a chronological coverage-only fallback."""

    def viable(day):
        return (
            counts[day]["eligible"] >= PROTOCOL["minimum_accounts"]
            and sum(
                value >= PROTOCOL["minimum_cadence_count"]
                for value in counts[day]["cadence_eligible"].values()
            )
            >= 2
        )

    def elapsed(first, last):
        a, b = datetime.fromisoformat(first), datetime.fromisoformat(last)
        return (b.year - a.year) * 12 + b.month - a.month

    preferred = PROTOCOL["preferred_observations"]
    if all(day in counts and viable(day) for day in preferred):
        return preferred
    if ASSESSMENT in counts and viable(ASSESSMENT):
        earlier = sorted(day for day in counts if day < ASSESSMENT and viable(day))
        minimum_gap = PROTOCOL["minimum_temporal_gap_months"]
        for fit in earlier:
            for validation in earlier:
                if (
                    elapsed(fit, validation) >= minimum_gap
                    and elapsed(validation, ASSESSMENT) >= minimum_gap
                ):
                    return fit, validation, ASSESSMENT
    raise ValueError("No chronologically supported selection using the predeclared coverage rule.")


def development_populations(source: SourceEvidence) -> tuple[tuple[Population, ...], list[dict]]:
    """Audit the preferred dates first, expanding only if the coverage rule fails."""
    observations = {instant.date().isoformat(): instant for instant in month_ends(source.ledger)}
    populations = {
        day: observe(source, observations[day]) for day in PROTOCOL["preferred_observations"]
    }
    try:
        dates = choose_dates({key: value.audit() for key, value in populations.items()})
    except ValueError:
        for day, instant in observations.items():
            if (
                day not in populations
                and source.ledger.history_start <= window_start(instant).date()
            ):
                populations[day] = observe(source, instant)
        dates = choose_dates({key: value.audit() for key, value in populations.items()})
    return tuple(populations[day] for day in dates), [
        populations[day].audit() for day in sorted(populations)
    ]


def behaviour_gate(fit: Population, validation: Population) -> dict:
    """Require reliable comparable exposure and enough distinct development measurements."""
    frames = [population.frame() for population in (fit, validation)]
    complete = [
        frame.loc[frame.observed_usage_periods.eq(3), list(BEHAVIOURAL)] for frame in frames
    ]
    shares = [len(rows) / len(frame) for rows, frame in zip(complete, frames, strict=True)]
    distinct = complete[0].nunique().to_dict()
    return {
        "complete_shares": shares,
        "development_distinct": distinct,
        "minimum_share": PROTOCOL["minimum_complete_usage_share"],
        "minimum_distinct": PROTOCOL["minimum_distinct_behavioural_values"],
        "passed": min(shares) >= PROTOCOL["minimum_complete_usage_share"]
        and min(distinct.values()) >= PROTOCOL["minimum_distinct_behavioural_values"],
    }


def reference_evidence(*, seed: int = 42, scope: str = "fieldwise-fictional") -> SourceEvidence:
    """Provide read-only notebook analysis with a temporary, verified source."""
    with fieldwise_reference(master_seed=seed, client_scope=scope) as (run, _):
        return SourceEvidence.from_verified_reference(run)
