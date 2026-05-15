from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity


class State[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]:
    """
    This class represents the state of the algorithm, almost like the "memory"
    of the work that the algorithm has already completed.

    This class must be blazing fast, as it is one of the most commonly accessed objects.

    Two parallel views of the same data are maintained:

    * ``_allocations`` — the canonical insertion-ordered list of planned
      allocations. Iterated by ``planned_allocations`` for output adapters.
    * ``_by_entity`` — a per-entity index keyed by ``id(entity)``. Made the
      primary lookup path for ``get_allocations_done_by`` so queries don't
      scan the whole schedule. Worth its weight: stateful rules and
      load-balancing algorithms call this method often, and an O(n) scan
      per call dominated the wall-clock runtime on the 200-worker fixture
      before the index existed.

    The two views are kept in sync inside ``add_allocation`` /
    ``remove_allocation``; everything else is read-only.
    """

    def __init__(self) -> None:
        self._allocations: list[PlannedAllocation[TAllocationRequest, TEntity]] = []
        self._by_entity: dict[int, list[PlannedAllocation[TAllocationRequest, TEntity]]] = {}

    def add_allocation(self, allocation: PlannedAllocation[TAllocationRequest, TEntity]) -> None:
        self._allocations.append(allocation)
        for entity in allocation.assigned_entities:
            self._by_entity.setdefault(id(entity), []).append(allocation)

    def remove_allocation(self, allocation: PlannedAllocation[TAllocationRequest, TEntity]) -> None:
        """Remove ``allocation`` from both views by **identity**, not equality.

        ``PlannedAllocation`` is a frozen dataclass and so compares structurally
        equal whenever two distinct instances share the same request and
        assigned entities. ``list.remove`` matches by ``__eq__`` and would pop
        the first equal entry — silently desynchronising the flat list from the
        per-entity index during backtracking churn where multiple structurally
        equal planned allocations coexist. Scanning for the exact instance
        keeps the two views in lock-step. The lists are short enough that the
        linear scan is fine.
        """
        try:
            index = next(i for i, p in enumerate(self._allocations) if p is allocation)
        except StopIteration:
            msg = "allocation is not present in this State"
            raise ValueError(msg) from None
        del self._allocations[index]

        for entity in allocation.assigned_entities:
            bucket = self._by_entity.get(id(entity))
            if bucket is None:
                msg = "allocation is not present in this State"
                raise ValueError(msg)
            try:
                entity_index = next(i for i, p in enumerate(bucket) if p is allocation)
            except StopIteration:
                msg = "allocation is not present in this State"
                raise ValueError(msg) from None
            del bucket[entity_index]

    def get_allocations_done_by(self, entity: TEntity) -> list[PlannedAllocation[TAllocationRequest, TEntity]]:
        """Allocations the given entity is assigned to. O(k) where k is that entity's count."""
        return list(self._by_entity.get(id(entity), []))

    @property
    def planned_allocations(self) -> list[PlannedAllocation[TAllocationRequest, TEntity]]:
        """All planned allocations recorded in this state, in the order they were added."""
        return list(self._allocations)
