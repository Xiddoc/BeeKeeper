from abc import ABC, abstractmethod
from typing import Any

from beekeeper.algorithm.algorithm_state import State
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.rules.rule_verdict import RuleVerdict


class StatefulRule[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](ABC):
    """A rule whose verdict depends on the in-progress assignment state.

    Stateful rules answer "given what's already been planned, can this entity
    take this allocation?" — checks like consecutive-shift limits, weekly
    hour caps, or rotation requirements. The algorithm consults them as it
    assigns, so they have access to the current ``State``.

    Most rules want one of the convenience subclasses — ``HardStatefulRule``
    for binary checks, ``SoftStatefulRule`` for scoring preferences.
    """

    @abstractmethod
    def evaluate(
        self,
        entity: TEntity,
        allocation: TAllocationRequest,
        state: State[TEntity, TAllocationRequest],
    ) -> RuleVerdict:
        """Return the rule's verdict for this (entity, allocation, state) triple."""


class HardStatefulRule[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    StatefulRule[TEntity, TAllocationRequest],
    ABC,
):
    """A stateful rule that is purely binary: either the entity passes or it doesn't."""

    def evaluate(
        self,
        entity: TEntity,
        allocation: TAllocationRequest,
        state: State[TEntity, TAllocationRequest],
    ) -> RuleVerdict:
        return RuleVerdict(compatible=self.check(entity, allocation, state))

    @abstractmethod
    def check(
        self,
        entity: TEntity,
        allocation: TAllocationRequest,
        state: State[TEntity, TAllocationRequest],
    ) -> bool:
        """Return ``True`` if this entity may take this allocation given the current state."""


class SoftStatefulRule[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    StatefulRule[TEntity, TAllocationRequest],
    ABC,
):
    """A stateful rule that expresses preference rather than hard eligibility.

    Soft rules never veto an entity (``compatible`` is always ``True``); they
    only contribute to the entity's aggregate score given the current state.
    """

    def evaluate(
        self,
        entity: TEntity,
        allocation: TAllocationRequest,
        state: State[TEntity, TAllocationRequest],
    ) -> RuleVerdict:
        return RuleVerdict(compatible=True, score=self.score(entity, allocation, state))

    @abstractmethod
    def score(
        self,
        entity: TEntity,
        allocation: TAllocationRequest,
        state: State[TEntity, TAllocationRequest],
    ) -> float:
        """Return a non-negative preference score given the current state; higher is better."""
