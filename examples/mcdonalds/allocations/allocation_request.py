from beekeeper import AllocationRequest, Entity
from examples.mcdonalds.allocations.allocation_type import McDonaldsAllocationType
from examples.mcdonalds.entities.entity_properties import McDonaldsExemption, McDonaldsLocation, McDonaldsRank


class McDonaldsAllocationRequest(
    AllocationRequest[McDonaldsAllocationType, McDonaldsRank, McDonaldsExemption, McDonaldsLocation, Entity]
):
    pass
