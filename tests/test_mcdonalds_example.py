"""End-to-end smoke test for the McDonald's example.

Imports mcdonalds via the conftest sys.path insertion (the example package is
not installable on its own; it's expected to be run via PYTHONPATH=examples
or `python -m mcdonalds.main` from the examples/ directory).
"""

import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

from mcdonalds.main import McDonaldsBeeKeeperInputs, run  # noqa: E402


def test_mcdonalds_example_runs_end_to_end(capsys: object) -> None:
    inputs = McDonaldsBeeKeeperInputs(
        workers_input_file=EXAMPLES_DIR / "mcdonalds" / "workers.json",
        allocations_input_file=EXAMPLES_DIR / "mcdonalds" / "allocations.json",
    )
    run(inputs)

    captured = capsys.readouterr().out  # type: ignore[attr-defined]
    # Three allocations in the fixture; load-balancing fills all three under our rules.
    assert "CLEANING" in captured
    assert "SERVING_FOOD" in captured
    assert "COOKING" in captured
    # Alice (CASHIER) should be assigned to at least one cashier-eligible task.
    assert "Alice" in captured
