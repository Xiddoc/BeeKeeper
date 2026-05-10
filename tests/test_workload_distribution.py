"""Workload distribution tests on the oversubscribed fixtures.

Wall-clock benchmarks tell us how *fast* each algorithm runs. They don't
tell us how *well* each algorithm spreads work — and "spreads work" is the
entire reason ``LoadBalancingAssignmentAlgorithm`` exists. These tests
exercise the oversubscribed fixtures (where every worker who isn't
rank-locked-out absorbs multiple allocations) and pin down the contract:

* ``GreedyAssignmentAlgorithm`` concentrates work on top-scored workers.
  With score=1.0 uniform across candidates (the McDonald's example default),
  greedy picks the first eligible candidate every time, so the same handful
  of workers absorb everything they can.
* ``LoadBalancingAssignmentAlgorithm`` divides ``score / (1 + load)``, so
  unloaded workers get preferred over already-loaded ones. The result
  should be visibly more even by every standard inequality measure.

If a future change to load-balancing makes it less effective at spreading
work, these tests fail and surface the regression.
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

from beekeeper import BaseAlgorithm, BeeKeeper, MixedInputAdapter, OutputAdapter, State  # noqa: E402
from beekeeper.adapters.inputs.json_allocation_input_adapter import JsonAllocationInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_entity_input_adapter import JsonEntityInputAdapter  # noqa: E402
from beekeeper.algorithm.implementations.greedy import GreedyAssignmentAlgorithm  # noqa: E402
from beekeeper.algorithm.implementations.load_balancing import LoadBalancingAssignmentAlgorithm  # noqa: E402
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule  # noqa: E402

FIXTURES_DIR = EXAMPLES_DIR / "mcdonalds"


class _CapturingOutput(OutputAdapter[McWorker, McDonaldsAllocationRequest]):
    def __init__(self) -> None:
        self.captured: State[McWorker, McDonaldsAllocationRequest] | None = None

    def handle_output(self, output_state: State[McWorker, McDonaldsAllocationRequest]) -> None:
        self.captured = output_state


def _load_workers(suffix: str) -> list[McWorker]:
    adapter: JsonEntityInputAdapter[McWorker] = JsonEntityInputAdapter(
        file=FIXTURES_DIR / f"workers_{suffix}.json",
        entity_type=McWorker,
    )
    return list(adapter.get_entities())


def _run_algorithm(
    algorithm: BaseAlgorithm[McWorker, McDonaldsAllocationRequest],
    suffix: str,
) -> State[McWorker, McDonaldsAllocationRequest]:
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
        algorithm=algorithm,
        preliminary_rules=[
            McRankRule(),
            AvailabilityRule[McWorker, McDonaldsAllocationRequest](),
            RequestedEntityRule[McWorker, McDonaldsAllocationRequest](),
        ],
        output_adapters=[sink],
    ).execute()
    assert sink.captured is not None
    return sink.captured


def _per_worker_counts(state: State[McWorker, McDonaldsAllocationRequest], all_workers: list[McWorker]) -> list[int]:
    """Allocations per worker, including zeros for workers who weren't picked."""
    counts: Counter[str] = Counter({w.name: 0 for w in all_workers})
    for planned in state.planned_allocations:
        for entity in planned.assigned_entities:
            counts[entity.name] += 1
    return list(counts.values())


def _gini(values: list[int]) -> float:
    """Gini coefficient. 0 = perfect equality, 1 = one element has everything.

    For integer counts, this is the canonical "how concentrated is the
    distribution" measure that's bounded in [0, 1] and easy to interpret.
    """
    sorted_values = sorted(values)
    n = len(sorted_values)
    total = sum(sorted_values)
    if n == 0 or total == 0:
        return 0.0
    cumulative = sum((i + 1) * v for i, v in enumerate(sorted_values))
    return (2 * cumulative) / (n * total) - (n + 1) / n


@pytest.fixture(scope="module")
def oversub_runs() -> dict[str, dict[str, State[McWorker, McDonaldsAllocationRequest]]]:
    """Run greedy and load-balancing once per fixture; share results across tests."""
    runs: dict[str, dict[str, State[McWorker, McDonaldsAllocationRequest]]] = {}
    for suffix in ("oversub_3x", "oversub_6x", "oversub_10x"):
        runs[suffix] = {
            "greedy": _run_algorithm(
                GreedyAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest](),
                suffix,
            ),
            "load_balancing": _run_algorithm(
                LoadBalancingAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest](),
                suffix,
            ),
        }
    return runs


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_both_algorithms_fill_comparable_allocation_counts(
    oversub_runs: dict[str, dict[str, State[McWorker, McDonaldsAllocationRequest]]],
    suffix: str,
) -> None:
    """Distribution differences shouldn't come from one algorithm just filling fewer
    allocations. Both algorithms should fulfill within 5% of each other."""
    greedy_total = len(oversub_runs[suffix]["greedy"].planned_allocations)
    lb_total = len(oversub_runs[suffix]["load_balancing"].planned_allocations)
    assert greedy_total > 0
    assert lb_total > 0
    ratio = min(greedy_total, lb_total) / max(greedy_total, lb_total)
    assert ratio >= 0.95, (
        f"On {suffix}: greedy filled {greedy_total}, load_balancing filled {lb_total}. "
        f"Distribution comparisons assume similar total fill; this is {ratio:.1%}."
    )


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_load_balancing_has_lower_gini_than_greedy(
    oversub_runs: dict[str, dict[str, State[McWorker, McDonaldsAllocationRequest]]],
    suffix: str,
) -> None:
    """Gini coefficient: 0 = perfect equality, 1 = max concentration.
    Load-balancing should be measurably lower than greedy."""
    workers = _load_workers(suffix)
    greedy_counts = _per_worker_counts(oversub_runs[suffix]["greedy"], workers)
    lb_counts = _per_worker_counts(oversub_runs[suffix]["load_balancing"], workers)

    greedy_gini = _gini(greedy_counts)
    lb_gini = _gini(lb_counts)

    assert lb_gini < greedy_gini, (
        f"On {suffix}: load_balancing Gini ({lb_gini:.3f}) should be lower than "
        f"greedy Gini ({greedy_gini:.3f}). Load balancing isn't doing its job."
    )


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_load_balancing_has_lower_stddev_than_greedy(
    oversub_runs: dict[str, dict[str, State[McWorker, McDonaldsAllocationRequest]]],
    suffix: str,
) -> None:
    """Standard deviation of per-worker counts: lower is more even."""
    workers = _load_workers(suffix)
    greedy_counts = _per_worker_counts(oversub_runs[suffix]["greedy"], workers)
    lb_counts = _per_worker_counts(oversub_runs[suffix]["load_balancing"], workers)

    greedy_std = statistics.pstdev(greedy_counts)
    lb_std = statistics.pstdev(lb_counts)

    assert lb_std < greedy_std, (
        f"On {suffix}: load_balancing stddev ({lb_std:.2f}) should be lower than greedy stddev ({greedy_std:.2f})."
    )


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_load_balancing_uses_more_workers_than_greedy(
    oversub_runs: dict[str, dict[str, State[McWorker, McDonaldsAllocationRequest]]],
    suffix: str,
) -> None:
    """Number of workers with at least one allocation. Load-balancing should use
    at least as many workers as greedy — strict-equality is allowed because at
    full saturation both might use everyone, but greedy should never use more."""
    workers = _load_workers(suffix)
    greedy_active = sum(1 for c in _per_worker_counts(oversub_runs[suffix]["greedy"], workers) if c > 0)
    lb_active = sum(1 for c in _per_worker_counts(oversub_runs[suffix]["load_balancing"], workers) if c > 0)

    assert lb_active >= greedy_active, (
        f"On {suffix}: greedy used {greedy_active} workers, "
        f"load_balancing used {lb_active}. Load balancing should not use fewer."
    )


@pytest.mark.parametrize("suffix", ["oversub_3x", "oversub_6x", "oversub_10x"])
def test_load_balancing_max_count_lower_than_greedy(
    oversub_runs: dict[str, dict[str, State[McWorker, McDonaldsAllocationRequest]]],
    suffix: str,
) -> None:
    """The single most-loaded worker under load-balancing should be loaded less
    than the single most-loaded worker under greedy. Direct test that the
    'no one carries the whole shift' goal is being met."""
    workers = _load_workers(suffix)
    greedy_max = max(_per_worker_counts(oversub_runs[suffix]["greedy"], workers))
    lb_max = max(_per_worker_counts(oversub_runs[suffix]["load_balancing"], workers))

    assert lb_max < greedy_max, (
        f"On {suffix}: greedy's busiest worker has {greedy_max} allocations, "
        f"load_balancing's busiest has {lb_max}. Load balancing should cap the peak lower."
    )
