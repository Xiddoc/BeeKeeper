from typing import Any

from beekeeper.adapters.outputs.output_adapter import OutputAdapter
from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


class ConsoleOutputAdapter[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    OutputAdapter[TEntity, TAllocationRequest],
):
    """Prints planned allocations to stdout.

    Useful for examples, smoke testing, and manual inspection. Production
    code should ship a domain-specific output adapter (database write, API
    call, file export) instead of relying on this one.
    """

    def handle_output(self, output_state: AssignmentState[TEntity, TAllocationRequest]) -> None:
        for planned in output_state.planned_allocations:
            assigned = ", ".join(repr(e) for e in planned.assigned_entities)
            print(
                f"{planned.request.allocation_type.name} "
                f"[{planned.request.date_range.start_date} -> {planned.request.date_range.end_date}]: "
                f"{assigned}"
            )
