from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.allocations.allocation_request import AnyRequest


class AllocationInputAdapter[TAllocationRequest: AnyRequest](ABC):
    @abstractmethod
    def get_allocations(self) -> Iterable[TAllocationRequest]:
        pass
