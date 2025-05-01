from abc import abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from beekeeper import AllocationRequest, Entity
from beekeeper.algorithm.algorithm_state import State
from beekeeper.rules.stateful_rule import StatefulRule

EntityType = TypeVar("EntityType", bound=Entity)
AllocationType = TypeVar("AllocationType", bound=AllocationRequest)


class BaseAlgorithm(Generic[EntityType, AllocationType]):
    @abstractmethod
    def run(self, allocations: Iterable[AllocationType], rules: StatefulRule) -> State:
        """
        The entry point to your sorting and allocating algorithm.
        Here you will receive a list of allocations you need to assign.
        You also receive a list of rules that you must abide to.
        Good luck :)

        Args:
            allocations: The list of tasks you need to assign.
            rules: The rules that define how to assign these tasks.

        Returns:
            The final state of the algorithm, where all the allocations have been assigned.

        """
