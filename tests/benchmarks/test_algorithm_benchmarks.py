"""Benchmarks for the bundled algorithm implementations against the McDonald's fixtures.

Skipped during normal `pytest` runs (the `--benchmark-skip` default in
pyproject's pytest config); run explicitly with::

    uv run pytest --benchmark-only

Each benchmark records timing for the *full* pipeline — input adapters
through algorithm through output dispatch — across all bundled
algorithms and all three fixture sizes. Two budgets apply:

* **Warning at 500 ms** — emits a ``UserWarning`` so the slowdown is
  visible in the test output without failing CI.
* **Hard ceiling at 1 s** — fails the test outright. The framework
  should be solving these sizes in well under a second.

The thresholds are deliberately loose; load_balancing on the 200-worker
fixture lands in the low double-digit milliseconds. The budgets catch
order-of-magnitude regressions, not single-digit-percent variation
that's mostly CI-runner noise.
"""

import sys
import warnings
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

from mcdonalds.allocations.allocation_request import McDonaldsAllocationRequest  # noqa: E402
from mcdonalds.entities.mcdonalds_employee import McWorker  # noqa: E402
from mcdonalds.rules.mc_rank_rule import McRankRule  # noqa: E402

from beekeeper import Algorithm, BeeKeeper, MixedInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_allocation_input_adapter import JsonAllocationInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_entity_input_adapter import JsonEntityInputAdapter  # noqa: E402
from beekeeper.algorithm.implementations.backtracking import BacktrackingAssignmentAlgorithm  # noqa: E402
from beekeeper.algorithm.implementations.load_balancing import LoadBalancingAssignmentAlgorithm  # noqa: E402
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule  # noqa: E402

WARN_THRESHOLD_SECONDS = 0.5
FAIL_THRESHOLD_SECONDS = 1.0

FIXTURES_DIR = EXAMPLES_DIR / "mcdonalds"

ALGORITHMS: dict[str, type[Algorithm[McWorker, McDonaldsAllocationRequest]]] = {
    "backtracking": BacktrackingAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest],
    "load_balancing": LoadBalancingAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest],
}

# OR-Tools is an optional dep; include it in the benchmark grid only if available.
try:
    from beekeeper.algorithm.implementations.or_tools import OrToolsAssignmentAlgorithm

    ALGORITHMS["or_tools"] = OrToolsAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest]
except ImportError:
    pass


def _build_beekeeper(
    suffix: str, algorithm_factory: type[Algorithm[McWorker, McDonaldsAllocationRequest]]
) -> BeeKeeper[McWorker, McDonaldsAllocationRequest]:
    return BeeKeeper[McWorker, McDonaldsAllocationRequest](
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
        algorithm=algorithm_factory(),
        preliminary_rules=[
            McRankRule(),
            AvailabilityRule[McWorker, McDonaldsAllocationRequest](),
            RequestedEntityRule[McWorker, McDonaldsAllocationRequest](),
        ],
        output_adapters=[],
    )


def _check_budget(mean_seconds: float, label: str) -> None:
    if mean_seconds > WARN_THRESHOLD_SECONDS:
        warnings.warn(
            f"{label}: mean {mean_seconds * 1000:.1f}ms exceeded "
            f"warning threshold of {WARN_THRESHOLD_SECONDS * 1000:.0f}ms",
            stacklevel=2,
        )
    assert mean_seconds < FAIL_THRESHOLD_SECONDS, (
        f"{label}: mean {mean_seconds * 1000:.1f}ms exceeded hard ceiling of {FAIL_THRESHOLD_SECONDS * 1000:.0f}ms"
    )


@pytest.mark.parametrize("algorithm_name", list(ALGORITHMS.keys()))
@pytest.mark.parametrize(
    ("suffix", "size_label"),
    [
        # Worker-rich fixtures: more workers than allocations, mixed required_count.
        ("large", "65w/25a"),
        ("xlarge", "100w/40a"),
        ("xxlarge", "200w/80a"),
        # Worker-scarce (oversubscribed) fixtures: many more allocations than
        # workers, every allocation n=1. Stress-tests how each algorithm
        # distributes work across a constrained pool.
        ("oversub_3x", "50w/150a (3x)"),
        ("oversub_6x", "50w/300a (6x)"),
        ("oversub_10x", "50w/500a (10x)"),
    ],
)
def test_full_pipeline_budget(
    benchmark: pytest.FixtureRequest,
    algorithm_name: str,
    suffix: str,
    size_label: str,
) -> None:
    """End-to-end run for each algorithm × fixture size."""
    factory = ALGORITHMS[algorithm_name]
    bk = _build_beekeeper(suffix, factory)
    benchmark(bk.execute)
    _check_budget(benchmark.stats.stats.mean, f"{algorithm_name} on {size_label}")  # type: ignore[attr-defined]
