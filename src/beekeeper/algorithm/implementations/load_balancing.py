from collections.abc import Iterable, Mapping
from typing import Any

from beekeeper.algorithm.algorithm_state import State
from beekeeper.algorithm.base_algorithm import BaseAlgorithm
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.stateful_rule import StatefulRule


class LoadBalancingAssignmentAlgorithm[
    TEntity: Entity[Any],
    TAllocationRequest: AllocationRequest[Any, Any],
](
    BaseAlgorithm[TEntity, TAllocationRequest],
):
    """Greedy with a load-balancing penalty so work disperses across the entity pool.

    The vanilla greedy reference picks the highest-scored compatible candidate
    for each allocation. When several allocations have overlapping candidate
    pools, that means the best-scoring entity gets assigned to most of them —
    realistic in toy data, miserable in production where the same worker ends
    up scheduled for every shift while everyone else sits idle.

    This algorithm replaces the raw candidate score with::

        adjusted_score = candidate.score / (1 + load)

    where ``load`` is the count of allocations the entity is already assigned
    to. The first time an entity is considered, the division is by 1 (no
    penalty); the second time, by 2 (half the score); etc. Other dynamics are
    otherwise identical to greedy: candidates are ranked, stateful rules are
    consulted, the top ``required_count`` are chosen, allocation is skipped
    if not enough candidates qualify.

    The result is that work spreads out — entities with no assignments yet
    are preferred over equally-scored entities who already have several. No
    randomness; the algorithm is fully deterministic for a given input.

    The load counter is maintained in a side dict keyed by ``id(entity)``
    rather than asking the State on every score evaluation; the State's
    ``get_allocations_done_by`` is O(n) per call, and on large fixtures
    that turns the per-allocation candidate sort into O(c·a) which dominates
    the runtime. The dict makes load lookup O(1) and keeps the algorithm
    in the same complexity class as greedy.
    """

    def run(
        self,
        allocations: Iterable[TAllocationRequest],
        entities: Iterable[TEntity],
        candidates: Mapping[int, list[Candidate[TEntity]]],
        rules: Iterable[StatefulRule[TEntity, TAllocationRequest]],
    ) -> State[TEntity, TAllocationRequest]:
        del entities
        rules_list = list(rules)
        state: State[TEntity, TAllocationRequest] = State()
        load: dict[int, int] = {}

        for allocation in allocations:
            alloc_candidates = candidates.get(id(allocation), [])
            ranked = sorted(
                alloc_candidates,
                key=lambda c: c.score / (1 + load.get(id(c.entity), 0)),
                reverse=True,
            )
            chosen: list[TEntity] = []

            for candidate in ranked:
                if len(chosen) >= allocation.required_count:
                    break
                if all(rule.evaluate(candidate.entity, allocation, state).compatible for rule in rules_list):
                    chosen.append(candidate.entity)

            if len(chosen) == allocation.required_count:
                for entity in chosen:
                    load[id(entity)] = load.get(id(entity), 0) + 1
                state.add_allocation(PlannedAllocation(request=allocation, assigned_entities=tuple(chosen)))

        return state
