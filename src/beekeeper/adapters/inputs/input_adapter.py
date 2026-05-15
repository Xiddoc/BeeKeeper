from abc import ABC

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity


class InputAdapter[TEntity: AnyEntity, TAllocationRequest: AnyRequest](
    EntityInputAdapter[TEntity],
    AllocationInputAdapter[TAllocationRequest],
    ABC,
):
    pass
