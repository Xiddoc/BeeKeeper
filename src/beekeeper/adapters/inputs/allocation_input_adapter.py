from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.allocations.allocation_request import AnyRequest


class AllocationInputAdapter[TAllocationRequest: AnyRequest](ABC):
    """
    Yields the allocation requests the pipeline must fill.

    Implementations decide where requests come from — JSON, a DB, an HTTP
    call, an in-memory fixture. The framework iterates the result exactly
    once per ``BeeKeeper.execute()`` call.
    """

    @abstractmethod
    def get_allocations(self) -> Iterable[TAllocationRequest]:
        pass
