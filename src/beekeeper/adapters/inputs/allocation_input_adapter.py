from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.allocations.allocation_request import AllocationRequest


class AllocationInputAdapter[TAllocationRequest: AllocationRequest](ABC):
    @abstractmethod
    def get_allocations(self) -> Iterable[TAllocationRequest]:
        pass
