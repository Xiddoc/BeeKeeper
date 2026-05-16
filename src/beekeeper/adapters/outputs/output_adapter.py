from abc import ABC, abstractmethod

from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity


class OutputAdapter[TEntity: AnyEntity, TAllocationRequest: AnyRequest](ABC):
    """Receives the final ``AssignmentState`` after the algorithm chain runs.

    Multiple output adapters can be wired into a single pipeline (a console
    printer + a database writer + a metrics sink); the framework calls
    ``handle_output`` on each in order. Adapters report errors by raising,
    not by return value — exceptions propagate to the ``execute()`` caller.
    """

    @abstractmethod
    def handle_output(self, output_state: AssignmentState[TEntity, TAllocationRequest]) -> None:
        pass
