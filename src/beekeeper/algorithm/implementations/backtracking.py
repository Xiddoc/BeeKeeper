from collections.abc import Iterable, Mapping
from itertools import combinations
from typing import Any

from beekeeper.algorithm.algorithm import Algorithm
from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.algorithm.errors import IncompleteSolutionError
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.stateful_rule import StatefulRule

DEFAULT_TOP_K_CANDIDATES = 30
DEFAULT_MAX_ITERATIONS = 1_000_000


class BacktrackingAssignmentAlgorithm[
    TEntity: Entity[Any],
    TAllocationRequest: AllocationRequest[Any, Any],
](
    Algorithm[TEntity, TAllocationRequest],
):
    """Depth-first backtracking solver.

    For each feasible allocation in input order, tries combinations of candidate
    entities (top-K by score). When a combination satisfies every stateful rule,
    the algorithm tentatively assigns it and recurses into the next allocation.
    If a downstream allocation fails to find any valid combination, the
    algorithm backtracks and tries the next combination at the previous level.

    This finds complete solutions where greedy gets stuck — e.g., when an
    entity is the only candidate for two overlapping allocations and a
    stateful rule (like "no double-booking") forbids both. Greedy assigns
    the first one and fails the second; backtracking explores both
    orderings.

    Three guards keep the worst-case search tractable:

    * **Feasibility filter.** Allocations whose candidate pool is smaller than
      their ``required_count`` are unfulfillable by definition and are skipped
      before the search starts. Letting them through would cause the search
      to exhaustively try every combination of every *earlier* allocation
      before giving up.
    * **Top-K candidate cap.** Only the ``top_k_candidates`` highest-scored
      candidates per allocation enter the search. Default 30.
    * **Iteration cap.** A hard ``max_iterations`` budget on recursive calls
      so even pathological inputs don't run forever.

    If the search exhausts without finding a complete assignment for the
    feasible set, raises ``IncompleteSolutionError``. Wire this algorithm
    in front of ``LoadBalancingAssignmentAlgorithm`` (which never raises)
    via ``BeeKeeper(algorithm=[BacktrackingAssignmentAlgorithm(),
    LoadBalancingAssignmentAlgorithm()])`` to fall back automatically.
    """

    def __init__(
        self,
        top_k_candidates: int = DEFAULT_TOP_K_CANDIDATES,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        self._top_k_candidates = top_k_candidates
        self._max_iterations = max_iterations

    def run(
        self,
        allocations: Iterable[TAllocationRequest],
        entities: Iterable[TEntity],
        candidates: Mapping[int, list[Candidate[TEntity]]],
        rules: Iterable[StatefulRule[TEntity, TAllocationRequest]],
    ) -> AssignmentState[TEntity, TAllocationRequest]:
        del entities  # backtracking works only off the pre-pruned candidate map
        rules_list = list(rules)
        allocations_list = list(allocations)
        ranked = self._rank_candidates(allocations_list, candidates)

        feasible = [a for a in allocations_list if len(ranked[id(a)]) >= a.required_count]

        state: AssignmentState[TEntity, TAllocationRequest] = AssignmentState()
        budget = [self._max_iterations]
        if self._search(feasible, 0, ranked, rules_list, state, budget):
            return state

        msg = (
            "BacktrackingAssignmentAlgorithm could not find a complete assignment "
            f"for {len(feasible)} feasible allocations within the iteration budget."
        )
        raise IncompleteSolutionError(msg, partial_state=state)

    def _rank_candidates(
        self,
        allocations: list[TAllocationRequest],
        candidates: Mapping[int, list[Candidate[TEntity]]],
    ) -> dict[int, list[TEntity]]:
        return {
            id(alloc): [
                c.entity
                for c in sorted(candidates.get(id(alloc), []), key=lambda c: c.score, reverse=True)[
                    : self._top_k_candidates
                ]
            ]
            for alloc in allocations
        }

    def _search(
        self,
        allocations: list[TAllocationRequest],
        index: int,
        ranked: dict[int, list[TEntity]],
        rules: list[StatefulRule[TEntity, TAllocationRequest]],
        state: AssignmentState[TEntity, TAllocationRequest],
        budget: list[int],
    ) -> bool:
        if index >= len(allocations):
            return True

        if budget[0] <= 0:
            return False
        budget[0] -= 1

        allocation = allocations[index]
        pool = ranked[id(allocation)]

        for combo in combinations(pool, allocation.required_count):
            if all(rule.evaluate(entity, allocation, state).compatible for entity in combo for rule in rules):
                planned = PlannedAllocation(request=allocation, assigned_entities=tuple(combo))
                state.add_allocation(planned)
                if self._search(allocations, index + 1, ranked, rules, state, budget):
                    return True
                state.remove_allocation(planned)

        return False
