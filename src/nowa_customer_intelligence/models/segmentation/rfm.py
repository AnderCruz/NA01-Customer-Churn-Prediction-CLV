"""Frozen traditional and cadence-aware financial reference scores."""

from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal
from math import ceil

from .profiles import AccountProfile

FIELDS = ("recency_days", "frequency", "monetary_gbp")
CADENCES = ("monthly", "annual", "mixed")
MIN_CADENCE = 30
Number = Decimal | int
Score = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ScoreRule:
    """Finite, tie-preserving empirical quantile breaks and monotone levels."""

    thresholds: tuple[Number, ...]
    levels: tuple[int, ...]

    def apply(self, value: Number) -> int:
        """Keep threshold equality in the lower raw band and clip exterior values."""
        return self.levels[bisect_left(self.thresholds, value)]


def fit_score_rule(values: list[Number], *, reverse: bool = False) -> ScoreRule:
    """Use nearest-rank thirds, pooling small bands without splitting tied values."""
    if not values:
        raise ValueError("Scoring boundaries require observed development evidence.")
    ordered = sorted(values)
    count = len(ordered)
    minimum = max(5, ceil(count * 0.05))
    candidates = sorted({ordered[ceil(count / 3) - 1], ordered[ceil(2 * count / 3) - 1]})
    retained = []
    previous = 0
    for value in candidates:
        position = sum(item <= value for item in ordered)
        if position - previous >= minimum and count - position >= minimum:
            retained.append(value)
            previous = position
    levels = {0: (2,), 1: (1, 3), 2: (1, 2, 3)}[len(retained)]
    return ScoreRule(tuple(retained), levels[::-1] if reverse else levels)


def _values(profile: AccountProfile) -> tuple[int, int, Decimal] | None:
    if (
        not profile.calendar_history_complete
        or not profile.invoice_feed_available
        or profile.recency_days is None
        or profile.frequency is None
        or profile.monetary_gbp is None
    ):
        return None
    return profile.recency_days, profile.frequency, profile.monetary_gbp


@dataclass(frozen=True, slots=True)
class ReferenceScores:
    """Fit once on eligible accounts and apply without re-estimating boundaries."""

    traditional: tuple[ScoreRule, ScoreRule, ScoreRule]
    cadence: dict[str, tuple[ScoreRule, ScoreRule, ScoreRule]]

    @classmethod
    def from_record(cls, record: dict) -> "ReferenceScores":
        """Reconstruct frozen rules from the verified JSON boundary record."""

        def read(rows):
            return tuple(
                ScoreRule(
                    tuple(
                        (Decimal if field == "monetary_gbp" else int)(value)
                        for value in row["thresholds"]
                    ),
                    tuple(row["levels"]),
                )
                for field, row in zip(FIELDS, rows, strict=True)
            )

        return cls(
            read(record["traditional"]),
            {cadence: read(rows) for cadence, rows in record["cadence"].items()},
        )

    def assign(self, profile: AccountProfile, *, cadence_aware: bool = False) -> Score | None:
        """Return neutral R, F, M levels or an explicit unassignable result."""
        values = _values(profile)
        rules = self.cadence.get(profile.cadence) if cadence_aware else self.traditional
        if values is None or rules is None:
            return None
        return tuple(rule.apply(value) for rule, value in zip(rules, values, strict=True))


def fit_references(profiles: tuple[AccountProfile, ...]) -> ReferenceScores:
    """Fit shared thirds and supported cadence-specific thirds on scored accounts."""
    values = [(profile.cadence, _values(profile)) for profile in profiles]
    if (
        not profiles
        or len({row.customer_id for row in profiles}) != len(profiles)
        or any(row is None for _, row in values)
    ):
        raise ValueError("RFM fitting requires unique accounts with complete essential evidence.")

    def rules(rows):
        return tuple(
            fit_score_rule(list(dimension), reverse=index == 0)
            for index, dimension in enumerate(zip(*rows, strict=True))
        )

    grouped = {}
    for cadence in CADENCES:
        rows = [row for group, row in values if group == cadence]
        if len(rows) >= MIN_CADENCE:
            grouped[cadence] = rules(rows)
    return ReferenceScores(rules([row for _, row in values]), grouped)
