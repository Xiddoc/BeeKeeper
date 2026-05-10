from abc import abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any

from beekeeper.algorithm.algorithm_state import State
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.stateful_rule import StatefulRule


class BaseAlgorithm[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]:
    @abstractmethod
    def run(
        self,
        allocations: Iterable[TAllocationRequest],
        entities: Iterable[TEntity],
        candidates: Mapping[int, list[Candidate[TEntity]]],
        rules: Iterable[StatefulRule[TEntity, TAllocationRequest]],
    ) -> State[TEntity, TAllocationRequest]:
        """The entry point to your sorting and allocating algorithm.

        You receive the full list of allocations to assign, the full list of
        entities, the per-allocation candidate map (already pruned by
        preliminary rules and decorated with aggregate scores), and the
        stateful rules you must consult during assignment.

        Args:
            allocations: The list of tasks you need to assign.
            entities: The work entities ("employees") you have to complete the allocations.
            candidates: For each allocation (keyed by ``id(allocation)``), the
                viable entities and their preliminary-rule scores. Candidates
                with ``compatible=False`` from any preliminary rule have
                already been pruned; what's left passed every binary check.
            rules: The stateful rules that must hold given the in-progress
                State — consult them before adding a PlannedAllocation.

        Returns:
            The final state of the algorithm, where the chosen allocations
            have been assigned via ``State.add_allocation``.
        """
