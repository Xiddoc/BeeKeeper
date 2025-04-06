from abc import ABC

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter


class InputAdapter(EntityInputAdapter, AllocationInputAdapter, ABC):
    pass
