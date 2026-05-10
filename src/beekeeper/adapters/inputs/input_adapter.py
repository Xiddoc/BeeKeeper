from abc import ABC

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


class InputAdapter[TEntity: Entity, TAllocationRequest: AllocationRequest](
    EntityInputAdapter[TEntity],
    AllocationInputAdapter[TAllocationRequest],
    ABC,
):
    pass
