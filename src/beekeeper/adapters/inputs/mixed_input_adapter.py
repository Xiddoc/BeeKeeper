from collections.abc import Iterable
from dataclasses import dataclass

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.adapters.inputs.input_adapter import InputAdapter
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


@dataclass
class MixedInputAdapter[TEntity: Entity, TAllocationRequest: AllocationRequest](
    InputAdapter[TEntity, TAllocationRequest],
):
    entity_adapter: EntityInputAdapter[TEntity]
    allocation_adapter: AllocationInputAdapter[TAllocationRequest]

    def get_entities(self) -> Iterable[TEntity]:
        return self.entity_adapter.get_entities()

    def get_allocations(self) -> Iterable[TAllocationRequest]:
        return self.allocation_adapter.get_allocations()
