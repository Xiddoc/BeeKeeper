from abc import ABC, abstractmethod
from typing import Any

from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


class OutputAdapter[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](ABC):
    @abstractmethod
    def handle_output(self, output_state: AssignmentState[TEntity, TAllocationRequest]) -> None:
        pass
