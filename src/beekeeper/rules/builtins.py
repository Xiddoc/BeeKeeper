"""
Domain-agnostic rules every scheduler probably wants.

These rules are imported via ``from beekeeper.rules.builtins import ...``.
They're deliberately not re-exported from ``beekeeper`` itself — they're
opinions about what most schedulers want, not framework primitives, and
the user is expected to choose them explicitly.
"""

from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity
from beekeeper.rules.preliminary_rule import HardPreliminaryRule


class AvailabilityRule[TEntity: AnyEntity, TAllocationRequest: AnyRequest](
    HardPreliminaryRule[TEntity, TAllocationRequest],
):
    """
    Reject an entity whose unavailabilities overlap the allocation's date range at all.

    Stricter than the stage-1 candidate filter (which only blocks on *full*
    coverage). Use this rule when "any conflict at all" should disqualify —
    e.g. "if you have any appointment during the shift, you can't take it"
    semantics. Stage 1 alone would still let an entity through if their
    unavailability covered only part of the allocation's range.
    """

    def check(self, entity: TEntity, allocation: TAllocationRequest) -> bool:
        alloc_start = allocation.date_range.start_date
        alloc_end = allocation.date_range.end_date
        return not any(
            inav.start_date <= alloc_end and inav.end_date >= alloc_start for inav in entity.unavailabilities
        )


class RequestedEntityRule[TEntity: AnyEntity, TAllocationRequest: AnyRequest](
    HardPreliminaryRule[TEntity, TAllocationRequest],
):
    """
    If the allocation explicitly requests entities, only those entities are eligible.

    Stage 1 already enforces this when the default pipeline is used, but
    the rule is available for domains that supply custom flow stages and
    want the same semantic without re-implementing it.

    Membership is checked by **identity** (``is``), not structural
    equality. Pydantic's auto-generated ``__eq__`` walks fields, so two
    ``Entity`` instances with identical names / unavailabilities /
    domain attributes would compare equal — and a request "I want
    *this* worker" would then accept "any worker that happens to look
    like this one". The contract is "this specific object", so identity
    is the right relation.
    """

    def check(self, entity: TEntity, allocation: TAllocationRequest) -> bool:
        if not allocation.requested_entities:
            return True
        return any(e is entity for e in allocation.requested_entities)
