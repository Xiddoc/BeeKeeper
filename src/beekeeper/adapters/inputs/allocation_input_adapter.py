from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest


class AllocationInputAdapter[TAllocationRequest: AllocationRequest[Any, Any]](ABC):
    @abstractmethod
    def get_allocations(self) -> Iterable[TAllocationRequest]:
        pass
