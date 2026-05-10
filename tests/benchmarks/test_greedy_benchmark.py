"""Benchmark the bundled greedy algorithm against the 65-worker / 25-allocation fixture.

Skipped during normal `pytest` runs (the `--benchmark-skip` default in
pyproject's pytest config); run explicitly with::

    uv run pytest --benchmark-only

Each benchmark test asserts a generous wall-clock ceiling so a serious
regression fails CI rather than just sliding into the timing report.
The thresholds are deliberately loose — the goal is to catch a
10x slowdown, not to police single-digit-percent variation that's
mostly CI-runner noise.
"""

import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

from mcdonalds.allocations.allocation_request import McDonaldsAllocationRequest  # noqa: E402
from mcdonalds.entities.mcdonalds_employee import McWorker  # noqa: E402
from mcdonalds.rules.mc_rank_rule import McRankRule  # noqa: E402

from beekeeper import BeeKeeper, MixedInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_allocation_input_adapter import JsonAllocationInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_entity_input_adapter import JsonEntityInputAdapter  # noqa: E402
from beekeeper.algorithm.implementations.greedy import GreedyAssignmentAlgorithm  # noqa: E402
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule  # noqa: E402

WORKERS = EXAMPLES_DIR / "mcdonalds" / "workers_large.json"
ALLOCATIONS = EXAMPLES_DIR / "mcdonalds" / "allocations_large.json"

# Generous: greedy on this fixture should land in the low single-digit ms range
# in any reasonable environment. 250 ms catches a regression of an order of
# magnitude or more without flaking on a busy CI runner.
WALL_CLOCK_BUDGET_SECONDS = 0.25


def _build_beekeeper() -> BeeKeeper[McWorker, McDonaldsAllocationRequest]:
    return BeeKeeper[McWorker, McDonaldsAllocationRequest](
        input_adapter=MixedInputAdapter(
            entity_adapter=JsonEntityInputAdapter(file=WORKERS, entity_type=McWorker),
            allocation_adapter=JsonAllocationInputAdapter(
                file=ALLOCATIONS,
                allocation_type=McDonaldsAllocationRequest,
            ),
        ),
        algorithm=GreedyAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest](),
        preliminary_rules=[
            McRankRule(),
            AvailabilityRule[McWorker, McDonaldsAllocationRequest](),
            RequestedEntityRule[McWorker, McDonaldsAllocationRequest](),
        ],
        output_adapters=[],
    )


def test_greedy_full_pipeline_under_budget(benchmark: pytest.FixtureRequest) -> None:
    """End-to-end: input adapters + 3-stage pipeline + greedy + output dispatch."""
    bk = _build_beekeeper()
    benchmark(bk.execute)
    assert benchmark.stats.stats.mean < WALL_CLOCK_BUDGET_SECONDS  # type: ignore[attr-defined]
