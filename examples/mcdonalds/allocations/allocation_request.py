from mcdonalds.allocations.allocation_type import McDonaldsAllocationType
from mcdonalds.entities.entity_properties import McJobPosition
from mcdonalds.entities.mcdonalds_employee import McWorker

from beekeeper import AllocationRequest


class McDonaldsAllocationRequest(AllocationRequest[McDonaldsAllocationType, McWorker]):
    allowed_ranks: frozenset[McJobPosition]
