from collections.abc import Iterable
from dataclasses import dataclass

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.adapters.inputs.input_adapter import InputAdapter


@dataclass
class MixedInputAdapter(InputAdapter):
    entity_adapter: EntityInputAdapter
    allocation_adapter: AllocationInputAdapter

    def get_entities(self) -> Iterable[EntityInputAdapter]:
        return self.entity_adapter.get_entities()

    def get_allocations(self):
        return self.allocation_adapter.get_allocations()
