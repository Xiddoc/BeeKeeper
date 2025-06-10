from abc import abstractmethod
from collections.abc import Iterable
from typing import Generic

from beekeeper.algorithm.algorithm_state import State
from beekeeper.allocations.allocation_type import TAllocationType
from beekeeper.entities.entity import TEntity
from beekeeper.rules.stateful_rule import StatefulRule


class BaseAlgorithm(Generic[TEntity, TAllocationType]):
    @abstractmethod
    def run(
        self, allocations: Iterable[TAllocationType], entities: Iterable[TEntity], rules: Iterable[StatefulRule]
    ) -> State:
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
