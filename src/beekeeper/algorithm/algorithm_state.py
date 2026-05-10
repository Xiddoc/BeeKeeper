from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity


class State[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]:
    """
    This class represents the state of the algorithm, almost like the "memory"
    of the work that the algorithm has already completed.

    This class must be blazing fast, as it is one of the most commonly accessed objects.
    """

    def __init__(self) -> None:
        self._allocations: list[PlannedAllocation[Any, TEntity]] = []

    def add_allocation(self, allocation: PlannedAllocation[Any, TEntity]) -> None:
        self._allocations.append(allocation)

    def remove_allocation(self, allocation: PlannedAllocation[Any, TEntity]) -> None:
        self._allocations.remove(allocation)

    def get_allocations_done_by(self, entity: TEntity) -> list[PlannedAllocation[Any, TEntity]]:
        return [allocation for allocation in self._allocations if allocation.assigned_entity == entity]
