from abc import ABC, abstractmethod
from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.rules.rule_verdict import RuleVerdict


class PreliminaryRule[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](ABC):
    """A rule that can be evaluated without referring to the in-progress schedule.

    Preliminary rules answer "is this entity, on principle, capable of
    fulfilling this allocation?" — checks like rank eligibility, exemptions,
    or static availability. They run before the algorithm assigns anything,
    and their verdicts are aggregated into a per-(allocation, entity)
    candidate score the algorithm consumes.

    Most rules want one of the convenience subclasses — ``HardPreliminaryRule``
    for binary checks, ``SoftPreliminaryRule`` for scoring preferences.
    Subclass ``PreliminaryRule`` directly only when you need both axes
    (compatibility AND a non-trivial score) in a single rule.
    """

    @abstractmethod
    def evaluate(self, entity: TEntity, allocation: TAllocationRequest) -> RuleVerdict:
        """Return the rule's verdict for this (entity, allocation) pair."""


class HardPreliminaryRule[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    PreliminaryRule[TEntity, TAllocationRequest], ABC,
):
    """A preliminary rule that is purely binary: either the entity passes or it doesn't."""

    def evaluate(self, entity: TEntity, allocation: TAllocationRequest) -> RuleVerdict:
        return RuleVerdict(compatible=self.check(entity, allocation))

    @abstractmethod
    def check(self, entity: TEntity, allocation: TAllocationRequest) -> bool:
        """Return ``True`` if this entity may be considered for this allocation."""


class SoftPreliminaryRule[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    PreliminaryRule[TEntity, TAllocationRequest], ABC,
):
    """A preliminary rule that expresses preference rather than hard eligibility.

    Soft rules never veto an entity (``compatible`` is always ``True``); they
    only contribute to the entity's aggregate score so the algorithm can
    prefer one viable candidate over another.
    """

    def evaluate(self, entity: TEntity, allocation: TAllocationRequest) -> RuleVerdict:
        return RuleVerdict(compatible=True, score=self.score(entity, allocation))

    @abstractmethod
    def score(self, entity: TEntity, allocation: TAllocationRequest) -> float:
        """Return a non-negative preference score; higher is better."""
