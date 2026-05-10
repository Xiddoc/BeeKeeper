from abc import abstractmethod
from collections.abc import Iterable
from typing import Any

from beekeeper.algorithm.algorithm_state import State
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.rules.stateful_rule import StatefulRule


class BaseAlgorithm[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]:
    @abstractmethod
    def run(
        self,
        allocations: Iterable[TAllocationRequest],
        entities: Iterable[TEntity],
        rules: Iterable[StatefulRule[TEntity, TAllocationRequest]],
    ) -> State[TEntity, TAllocationRequest]:
        """
        The entry point to your sorting and allocating algorithm.
        Here you will receive a list of allocations you need to assign.
        You also receive a list of rules that you must abide to.
        Good luck :)

        Args:
            allocations: The list of tasks you need to assign.
            entities: The work entities ("employees") you have to complete the allocations.
            rules: The rules that define how to assign these tasks.

        Returns:
            The final state of the algorithm, where all the allocations have been assigned.

        """
