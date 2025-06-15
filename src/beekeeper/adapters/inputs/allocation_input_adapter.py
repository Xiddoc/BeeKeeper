from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.allocations.allocation_request import TAllocationRequest


class AllocationInputAdapter(ABC):
    @abstractmethod
    def get_allocations(self) -> Iterable[TAllocationRequest]:
        pass
