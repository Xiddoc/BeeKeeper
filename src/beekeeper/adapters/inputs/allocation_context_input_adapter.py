from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.allocations.allocation_request import AllocationRequest


class AllocationContextInputAdapter(ABC):

    @abstractmethod
    def get_already_assigned_allocations(self) -> Iterable[AllocationRequest]:
        pass
