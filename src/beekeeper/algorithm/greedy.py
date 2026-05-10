from collections.abc import Iterable, Mapping
from typing import Any

from beekeeper.algorithm.algorithm_state import State
from beekeeper.algorithm.base_algorithm import BaseAlgorithm
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.stateful_rule import StatefulRule


class GreedyAssignmentAlgorithm[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    BaseAlgorithm[TEntity, TAllocationRequest],
):
    """A trivial greedy reference implementation.

    For each allocation in input order, picks the highest-scoring compatible
    candidates (per the stateful rules) and fills ``required_count`` slots.
    If a candidate fails any stateful rule, it's skipped and the next
    candidate is tried; if not enough candidates qualify, the allocation
    goes unfulfilled and is omitted from the resulting State.

    This is a baseline — it doesn't backtrack, doesn't optimize globally,
    and doesn't care about anything beyond "fill the required count with
    the best available entities". Domains that want non-trivial scheduling
    should write their own ``BaseAlgorithm`` subclass; this one exists so
    every example in the framework's docs has a runnable algorithm and so
    domain code has a working starting point to adapt.
    """

    def run(
        self,
        allocations: Iterable[TAllocationRequest],
        entities: Iterable[TEntity],  # noqa: ARG002 — algorithms may use the full entity list, but greedy doesn't
        candidates: Mapping[int, list[Candidate[TEntity]]],
        rules: Iterable[StatefulRule[TEntity, TAllocationRequest]],
    ) -> State[TEntity, TAllocationRequest]:
        rules_list = list(rules)
        state: State[TEntity, TAllocationRequest] = State()

        for allocation in allocations:
            alloc_candidates = candidates.get(id(allocation), [])
            ranked = sorted(alloc_candidates, key=lambda c: c.score, reverse=True)
            chosen: list[TEntity] = []

            for candidate in ranked:
                if len(chosen) >= allocation.required_count:
                    break
                if all(
                    rule.evaluate(candidate.entity, allocation, state).compatible for rule in rules_list
                ):
                    chosen.append(candidate.entity)

            if len(chosen) == allocation.required_count:
                state.add_allocation(
                    PlannedAllocation(request=allocation, assigned_entities=tuple(chosen))
                )

        return state
