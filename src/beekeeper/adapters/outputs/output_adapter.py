from abc import ABC, abstractmethod

from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity


class OutputAdapter[TEntity: AnyEntity, TAllocationRequest: AnyRequest](ABC):
    @abstractmethod
    def handle_output(self, output_state: AssignmentState[TEntity, TAllocationRequest]) -> None:
        pass
