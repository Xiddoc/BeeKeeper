from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.candidate import Candidate
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class AssignPossibleEntitiesToAllocations[TEntity: AnyEntity, TAllocationRequest: AnyRequest](
    BaseBeeKeeperFlowStage[TEntity, TAllocationRequest],
):
    """Build the per-allocation candidate set the rule pipeline and algorithm consume.

    For each allocation, walks the entity list and includes the entity as a
    candidate unless it's *definitively* unavailable: either because the
    allocation specifies ``requested_entities`` and this entity isn't one of
    them, or because the entity has an unavailability that fully covers the
    allocation's date range. Partial overlaps pass through — preliminary
    rules and the algorithm get the final say on partial-day semantics.

    Membership in ``requested_entities`` is checked by **identity** (``is``),
    matching ``RequestedEntityRule`` in ``beekeeper.rules.builtins``. Pydantic's
    auto-generated ``__eq__`` walks fields, so two ``Entity`` instances with
    identical attribute values compare equal — and a structural ``in`` check
    would admit a look-alike entity the caller never named. The contract is
    "these specific objects", so identity is the right relation.

    All candidates start with a neutral score (``1.0``); the preliminary-rule
    stage multiplies in soft-rule scores and prunes hard-rule failures.
    """

    def run_stage(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> BeeKeeperFlowState[TEntity, TAllocationRequest]:
        for allocation in state.allocations:
            candidates: list[Candidate[TEntity]] = []
            for entity in state.entities:
                if allocation.requested_entities and not any(e is entity for e in allocation.requested_entities):
                    continue
                if self._is_blocked_by_unavailability(entity, allocation):
                    continue
                candidates.append(Candidate(entity=entity))
            state.candidate_map[id(allocation)] = candidates
        return state

    @staticmethod
    def _is_blocked_by_unavailability(entity: TEntity, allocation: TAllocationRequest) -> bool:
        alloc_start = allocation.date_range.start_date
        alloc_end = allocation.date_range.end_date
        return any(inav.start_date <= alloc_start and inav.end_date >= alloc_end for inav in entity.unavailabilities)
