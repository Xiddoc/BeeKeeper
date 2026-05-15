from beekeeper.adapters.outputs.output_adapter import OutputAdapter
from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity


class ConsoleOutputAdapter[TEntity: AnyEntity, TAllocationRequest: AnyRequest](
    OutputAdapter[TEntity, TAllocationRequest],
):
    """Prints planned allocations to stdout.

    Useful for examples, smoke testing, and manual inspection. Production
    code should ship a domain-specific output adapter (database write, API
    call, file export) instead of relying on this one.
    """

    def handle_output(self, output_state: AssignmentState[TEntity, TAllocationRequest]) -> None:
        for planned in output_state.assignments:
            assigned = ", ".join(repr(e) for e in planned.assigned_entities)
            print(
                f"{planned.allocation.allocation_type.name} "
                f"[{planned.allocation.date_range.start_date} -> {planned.allocation.date_range.end_date}]: "
                f"{assigned}"
            )
