from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.allocations.allocation_type import AllocationType
from beekeeper.entities.entity import Entity


class PlannedAllocation[TAllocationType: AllocationType, TEntity: Entity[Any]](
    AllocationRequest[TAllocationType, TEntity],
):
    assigned_entity: TEntity
