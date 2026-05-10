from collections.abc import Iterable
from dataclasses import dataclass

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.adapters.inputs.input_adapter import InputAdapter
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


@dataclass
class MixedInputAdapter(InputAdapter):
    entity_adapter: EntityInputAdapter
    allocation_adapter: AllocationInputAdapter

    def get_entities(self) -> Iterable[Entity]:
        return self.entity_adapter.get_entities()

    def get_allocations(self) -> Iterable[AllocationRequest]:
        return self.allocation_adapter.get_allocations()
