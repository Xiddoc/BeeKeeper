from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


class PlannedAllocation(AllocationRequest):
    assigned_entity: Entity
