from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity


class State:
    """
    This class represents the state of the algorithm, almost like the "memory"
    of the work that the algorithm has already completed.

    This class must be blazing fast, as it is one of the most commonly accessed objects.
    """

    def __init__(self) -> None:
        self._allocations: list[PlannedAllocation] = []

    def add_allocation(self, allocation: PlannedAllocation) -> None:
        self._allocations.append(allocation)

    def remove_allocation(self, allocation: PlannedAllocation) -> None:
        self._allocations.remove(allocation)

    def get_allocations_done_by(self, entity: Entity) -> list[PlannedAllocation]:
        return [allocation for allocation in self._allocations if allocation.requested_entity == entity]
