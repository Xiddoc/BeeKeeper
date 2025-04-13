from beekeeper import PlannedAllocation
from beekeeper.algorithm.allocations_dal import AllocationsDAL


class State:
    def __init__(self) -> None:
        self._dal = AllocationsDAL()

    def add_allocation(self, allocation: PlannedAllocation) -> None:
        self._dal.append(allocation)

    def remove_allocation(self, allocation: PlannedAllocation) -> None:
        self._dal.remove(allocation)
