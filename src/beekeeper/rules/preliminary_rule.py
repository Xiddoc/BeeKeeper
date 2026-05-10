from abc import ABC, abstractmethod

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.rules.base_rule import BaseRule


class PreliminaryRule[TEntity: Entity, TAllocationRequest: AllocationRequest](BaseRule, ABC):
    @abstractmethod
    def is_compatible(self, entity: TEntity, allocation: TAllocationRequest) -> bool:
        """
        Check if this entity can possibly perform this allocation at all.
        This is a preliminary run meant to check impossibilities between entities
        and allocations they might need to fulfill. The easiest example of this is
        checking if the entity has any exemptions which might prevent them from
        performing the allocation at all.

        Args:
            entity: The entity to check compatiblity for.
            allocation: The allocation they are expected to fulfill.

        Returns:
            ``True`` if the entity can perform the allocation, ``False`` if they can't.
        """
