from abc import ABC
from typing import Any

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


class InputAdapter[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    EntityInputAdapter[TEntity],
    AllocationInputAdapter[TAllocationRequest],
    ABC,
):
    pass
