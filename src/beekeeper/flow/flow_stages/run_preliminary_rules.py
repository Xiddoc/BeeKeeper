import math
from dataclasses import replace
from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.candidate import (
    Candidate,  # noqa: TC001 — runtime use is via dataclasses.replace, but the type alias is needed for the local annotation
)
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class RunPreliminaryRules[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    BaseBeeKeeperFlowStage[TEntity, TAllocationRequest],
):
    """Apply preliminary rules to the candidate map: prune incompatibilities, aggregate scores.

    For every (allocation, candidate) pair populated by stage 1, every
    preliminary rule is evaluated. The combined verdict:

    * **Compatibility is logical AND.** Any rule reporting ``compatible=False``
      drops the candidate from the allocation's list — there's no point
      scoring an entity that's hard-disqualified.
    * **Score is the geometric mean** of the per-rule verdict scores. The
      geometric mean treats each rule as an independent multiplicative
      factor and stays bounded in the same range as its inputs, so a single
      lukewarm soft rule doesn't tank the whole candidate the way a pure
      product would (and vice versa, a single high score doesn't drown out
      the others the way an arithmetic mean might).

    Preliminary rules can be run before the algorithm because their verdicts
    don't depend on what's already been planned. Stateful rules — which do
    depend on the in-progress schedule — are consulted by the algorithm
    itself in stage 3.
    """

    def run_stage(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> BeeKeeperFlowState[TEntity, TAllocationRequest]:
        rules = list(state.preliminary_rules)
        for allocation in state.allocations:
            alloc_key = id(allocation)
            previous_candidates = state.candidate_map.get(alloc_key, [])
            surviving: list[Candidate[TEntity]] = []

            for candidate in previous_candidates:
                verdicts = [rule.evaluate(candidate.entity, allocation) for rule in rules]
                if all(v.compatible for v in verdicts):
                    aggregate_score = self._geometric_mean([v.score for v in verdicts])
                    surviving.append(replace(candidate, score=aggregate_score))

            state.candidate_map[alloc_key] = surviving
        return state

    @staticmethod
    def _geometric_mean(scores: list[float]) -> float:
        """Geometric mean of non-negative scores; empty input returns 1.0 (neutral)."""
        if not scores:
            return 1.0
        if any(s <= 0 for s in scores):
            return 0.0
        return math.exp(sum(math.log(s) for s in scores) / len(scores))
