from beekeeper import PlannedAllocation


class AllocationsDAL:
    def __init__(self) -> None:
        self._planned_allocations = []

    def append(self, allocation: PlannedAllocation) -> None:
        self._planned_allocations.append(allocation)

    def remove(self, allocation: PlannedAllocation) -> None:
        self._planned_allocations.remove(allocation)
