"""Workload distribution tests on the oversubscribed fixtures.

Wall-clock benchmarks tell us how *fast* ``LoadBalancingAssignmentAlgorithm``
runs. These tests pin down how *well* it spreads work — the entire reason
the algorithm exists. They exercise the oversubscribed fixtures where every
worker who isn't rank-locked-out has to absorb multiple allocations, and
assert that load-balancing achieves its stated goals:

* Every allocation gets filled.
* Every eligible worker gets at least one allocation (no one idle).
* The Gini coefficient stays low — near-perfect equality.
* No single worker carries more than ~3x the mean load.

The thresholds below are deliberately loose against measured behavior
(~Gini=0.13, max=12 on oversub_10x) so the tests catch genuine
regressions rather than minor drift.
"""

import statistics
import sys
from collections import Counter
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

from mcdonalds.allocations.allocation_request import McDonaldsAllocationRequest  # noqa: E402
from mcdonalds.entities.mcdonalds_employee import McWorker  # noqa: E402
from mcdonalds.rules.mc_rank_rule import McRankRule  # noqa: E402

from beekeeper import AssignmentState, BeeKeeper, MixedInputAdapter, OutputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_allocation_input_adapter import JsonAllocationInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_entity_input_adapter import JsonEntityInputAdapter  # noqa: E402
from beekeeper.algorithm.implementations.load_balancing import LoadBalancingAssignmentAlgorithm  # noqa: E402
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule  # noqa: E402

FIXTURES_DIR = EXAMPLES_DIR / "mcdonalds"

# Generous thresholds against measured behavior. Real numbers on oversub_10x
# are Gini ~0.13, max ~12; these limits catch regressions of 2-3x or more.
GINI_CEILING = 0.30
MAX_LOAD_MULTIPLIER = 3.0  # busiest worker may carry up to 3x the mean


class _CapturingOutput(OutputAdapter[McWorker, McDonaldsAllocationRequest]):
    def __init__(self) -> None:
        self.captured: AssignmentState[McWorker, McDonaldsAllocationRequest] | None = None

    def handle_output(self, output_state: AssignmentState[McWorker, McDonaldsAllocationRequest]) -> None:
        self.captured = output_state


def _load_workers(suffix: str) -> list[McWorker]:
    adapter: JsonEntityInputAdapter[McWorker] = JsonEntityInputAdapter(
        file=FIXTURES_DIR / f"workers_{suffix}.json",
        entity_type=McWorker,
    )
    return list(adapter.get_entities())


def _run_load_balancing(suffix: str) -> AssignmentState[McWorker, McDonaldsAllocationRequest]:
    sink = _CapturingOutput()
    BeeKeeper[McWorker, McDonaldsAllocationRequest](
        input_adapter=MixedInputAdapter(
            entity_adapter=JsonEntityInputAdapter(
                file=FIXTURES_DIR / f"workers_{suffix}.json",
                entity_type=McWorker,
            ),
            allocation_adapter=JsonAllocationInputAdapter(
                file=FIXTURES_DIR / f"allocations_{suffix}.json",
                allocation_type=McDonaldsAllocationRequest,
            ),
        ),
        algorithm=LoadBalancingAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest](),
        preliminary_rules=[
            McRankRule(),
            AvailabilityRule[McWorker, McDonaldsAllocationRequest](),
            RequestedEntityRule[McWorker, McDonaldsAllocationRequest](),
        ],
        output_adapters=[sink],
    ).execute()
    assert sink.captured is not None
    return sink.captured


def _per_worker_counts(
    state: AssignmentState[McWorker, McDonaldsAllocationRequest], all_workers: list[McWorker]
) -> list[int]:
    """Allocations per worker, including zeros for workers who weren't picked."""
    counts: Counter[str] = Counter({w.name: 0 for w in all_workers})
    for planned in state.planned_allocations:
        for entity in planned.assigned_entities:
            counts[entity.name] += 1
    return list(counts.values())


def _gini(values: list[int]) -> float:
    """Gini coefficient. 0 = perfect equality, 1 = one element has everything."""
    sorted_values = sorted(values)
    n = len(sorted_values)
    total = sum(sorted_values)
    if n == 0 or total == 0:
        return 0.0
    cumulative = sum((i + 1) * v for i, v in enumerate(sorted_values))
    return (2 * cumulative) / (n * total) - (n + 1) / n


@pytest.fixture(scope="module")
def oversub_states() -> dict[str, AssignmentState[McWorker, McDonaldsAllocationRequest]]:
    """Run load-balancing once per fixture; share results across tests."""
    return {suffix: _run_load_balancing(suffix) for suffix in ("oversub_3x", "oversub_6x", "oversub_10x")}


@pytest.mark.parametrize(
    ("suffix", "expected_total"),
    [("oversub_3x", 150), ("oversub_6x", 300), ("oversub_10x", 500)],
)
def test_every_allocation_filled(
    oversub_states: dict[str, AssignmentState[McWorker, McDonaldsAllocationRequest]],
    suffix: str,
    expected_total: int,
) -> None:
    """With sparse unavailabilities and rank-eligible candidates everywhere, no
    allocation should go unfilled."""
    assert len(oversub_states[suffix].planned_allocations) == expected_total


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_no_eligible_worker_idle(
    oversub_states: dict[str, AssignmentState[McWorker, McDonaldsAllocationRequest]],
    suffix: str,
) -> None:
    """Under heavy oversubscription, load-balancing should never leave a worker
    idle. (Every worker in these fixtures has at least one rank-eligible
    allocation, so 'unused' indicates a distribution failure rather than a
    feasibility one.)"""
    workers = _load_workers(suffix)
    counts = _per_worker_counts(oversub_states[suffix], workers)
    idle = sum(1 for c in counts if c == 0)
    assert idle == 0, f"On {suffix}, {idle} workers got zero allocations under load-balancing."


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_gini_coefficient_below_ceiling(
    oversub_states: dict[str, AssignmentState[McWorker, McDonaldsAllocationRequest]],
    suffix: str,
) -> None:
    """Gini coefficient is the canonical inequality metric. Near 0 means perfectly
    even; near 1 means one worker has everything. Load-balancing typically hits
    ~0.13 on these fixtures; the 0.30 ceiling catches 2x+ degradation."""
    workers = _load_workers(suffix)
    counts = _per_worker_counts(oversub_states[suffix], workers)
    gini = _gini(counts)
    assert gini < GINI_CEILING, f"On {suffix}, Gini={gini:.3f} exceeded ceiling {GINI_CEILING}."


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_busiest_worker_within_multiplier_of_mean(
    oversub_states: dict[str, AssignmentState[McWorker, McDonaldsAllocationRequest]],
    suffix: str,
) -> None:
    """The busiest worker shouldn't be wildly more loaded than the average."""
    workers = _load_workers(suffix)
    counts = _per_worker_counts(oversub_states[suffix], workers)
    mean = statistics.mean(counts)
    busiest = max(counts)
    assert busiest <= MAX_LOAD_MULTIPLIER * mean, (
        f"On {suffix}, busiest worker has {busiest} allocations against mean {mean:.1f} "
        f"(ratio {busiest / mean:.2f}, ceiling {MAX_LOAD_MULTIPLIER})."
    )
