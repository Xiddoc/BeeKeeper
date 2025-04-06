from abc import ABC, abstractmethod


class AllocationInputAdapter(ABC):
    @abstractmethod
    def get_allocations(self):
        pass
