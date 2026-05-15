from collections.abc import Iterable, Mapping

from beekeeper.algorithm.algorithm import Algorithm
from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.allocations.assignment import Assignment
from beekeeper.entities.entity import AnyEntity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.stateful_rule import StatefulRule


class LoadBalancingAssignmentAlgorithm[
    TEntity: AnyEntity,
    TAllocationRequest: AnyRequest,
](
    Algorithm[TEntity, TAllocationRequest],
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

    Load is read from ``state.get_assignments_done_by`` (now O(k) thanks to
    the AssignmentState's per-entity index); no side bookkeeping is needed.
    """

    def run(
        self,
        allocations: Iterable[TAllocationRequest],
        entities: Iterable[TEntity],
        candidates: Mapping[int, list[Candidate[TEntity]]],
        rules: Iterable[StatefulRule[TEntity, TAllocationRequest]],
    ) -> AssignmentState[TEntity, TAllocationRequest]:
        del entities
        rules_list = list(rules)
        state: AssignmentState[TEntity, TAllocationRequest] = AssignmentState()

        for allocation in allocations:
            alloc_candidates = candidates.get(id(allocation), [])
            ranked = sorted(
                alloc_candidates,
                key=lambda c: c.score / (1 + len(state.get_assignments_done_by(c.entity))),
                reverse=True,
            )
            chosen: list[TEntity] = []

            for candidate in ranked:
                if len(chosen) >= allocation.required_count:
                    break
                if all(rule.evaluate(candidate.entity, allocation, state).compatible for rule in rules_list):
                    chosen.append(candidate.entity)

            if len(chosen) == allocation.required_count:
                state.add_assignment(Assignment(allocation=allocation, assigned_entities=tuple(chosen)))

        return state
