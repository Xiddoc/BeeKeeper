from abc import ABC, abstractmethod

from beekeeper.algorithm.algorithm_state import State
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity
from beekeeper.rules.base_rule import BaseRule


class StatefulRule[TEntity: Entity, TPlannedAllocation: PlannedAllocation](BaseRule, ABC):
    @abstractmethod
    def is_compatible(self, entity: TEntity, allocation: TPlannedAllocation, state: State) -> bool:
        """
        Check if this entity can possibly perform this allocation with due
        regard to the current state of the timetable. This is a more comprehensive
        function meant to analyse if an entity has performed too many allocations,
        has performed consecutive allocations, and other such rules that can only
        be determined in real-time as the algorithm is positioning the allocations.

        Args:
            entity: The entity to check compatiblity for.
            allocation: The allocation they are expected to fulfill.
            state: The current state of the timetable.

        Returns:
            ``True`` if the entity can perform the allocation, ``False`` if they can't.
        """
