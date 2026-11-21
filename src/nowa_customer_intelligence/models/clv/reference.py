"""Read the accepted seed-42 scenario into temporary CLV analytical inputs."""

from calendar import monthrange
from datetime import UTC, date, datetime, time

from ...data.eda_inputs import REFERENCE_CUTOFF, fieldwise_reference
from ...data.synthetic.provenance import DatasetInventory
from .history import HistoryLedger


def load_reference_history(
    *, master_seed: int = 42, client_scope: str = "fieldwise-fictional"
) -> tuple[HistoryLedger, tuple[DatasetInventory, ...]]:
    """Reconstruct verified Fieldwise evidence using a temporary Registry."""
    with fieldwise_reference(master_seed=master_seed, client_scope=client_scope) as (run, _):
        population = run.population
        start = date.fromisoformat(run.provenance.parameters.history[0])
        ledger = HistoryLedger(
            population.customers,
            population.episodes,
            population.charges,
            population.snapshots,
            start,
            REFERENCE_CUTOFF,
        )
        return ledger, run.provenance.inventory


def month_ends(ledger: HistoryLedger) -> tuple[datetime, ...]:
    """Return observed calendar month-end timestamps within the ledger window."""
    current = ledger.history_start.replace(day=1)
    ends = []
    while current <= ledger.cutoff.date():
        last = current.replace(day=monthrange(current.year, current.month)[1])
        boundary = datetime.combine(last, time.max, UTC)
        if boundary <= ledger.cutoff:
            ends.append(boundary)
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else current.replace(month=current.month + 1)
        )
    return tuple(ends)
