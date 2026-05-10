"""Benchmark the bundled greedy algorithm against the McDonald's stress fixtures.

Skipped during normal `pytest` runs (the `--benchmark-skip` default in
pyproject's pytest config); run explicitly with::

    uv run pytest --benchmark-only

Each benchmark records timing for the *full* pipeline — input adapters
through algorithm through output dispatch — and applies two budgets:

* **Warning at 500 ms** — emits a ``UserWarning`` so the slowdown is
  visible in the test output without failing CI. Useful for catching
  drift before it becomes critical.
* **Hard ceiling at 1 s** — fails the test outright. The framework
  should be solving these sizes in well under a second; if it takes
  longer, something is materially wrong.

These thresholds are deliberately loose: greedy on the 200-worker
fixture lands in the low double-digit milliseconds in any reasonable
environment. The point of the budgets is to catch order-of-magnitude
regressions, not to police single-digit-percent variation that's
mostly CI-runner noise.
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

from beekeeper import BeeKeeper, MixedInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_allocation_input_adapter import JsonAllocationInputAdapter  # noqa: E402
from beekeeper.adapters.inputs.json_entity_input_adapter import JsonEntityInputAdapter  # noqa: E402
from beekeeper.algorithm.implementations.greedy import GreedyAssignmentAlgorithm  # noqa: E402
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule  # noqa: E402

WARN_THRESHOLD_SECONDS = 0.5
FAIL_THRESHOLD_SECONDS = 1.0

FIXTURES_DIR = EXAMPLES_DIR / "mcdonalds"


def _build_beekeeper(suffix: str) -> BeeKeeper[McWorker, McDonaldsAllocationRequest]:
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
        algorithm=GreedyAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest](),
        preliminary_rules=[
            McRankRule(),
            AvailabilityRule[McWorker, McDonaldsAllocationRequest](),
            RequestedEntityRule[McWorker, McDonaldsAllocationRequest](),
        ],
        output_adapters=[],
    )


def _check_budget(mean_seconds: float, fixture_label: str) -> None:
    if mean_seconds > WARN_THRESHOLD_SECONDS:
        warnings.warn(
            f"{fixture_label}: mean {mean_seconds * 1000:.1f}ms exceeded "
            f"warning threshold of {WARN_THRESHOLD_SECONDS * 1000:.0f}ms",
            stacklevel=2,
        )
    assert mean_seconds < FAIL_THRESHOLD_SECONDS, (
        f"{fixture_label}: mean {mean_seconds * 1000:.1f}ms exceeded "
        f"hard ceiling of {FAIL_THRESHOLD_SECONDS * 1000:.0f}ms"
    )


@pytest.mark.parametrize(
    ("suffix", "label"),
    [
        ("large", "65 workers / 25 allocations"),
        ("xlarge", "100 workers / 40 allocations"),
        ("xxlarge", "200 workers / 80 allocations"),
    ],
)
def test_greedy_full_pipeline_budget(
    benchmark: pytest.FixtureRequest,
    suffix: str,
    label: str,
) -> None:
    """End-to-end greedy run for each fixture size."""
    bk = _build_beekeeper(suffix)
    benchmark(bk.execute)
    _check_budget(benchmark.stats.stats.mean, label)  # type: ignore[attr-defined]
