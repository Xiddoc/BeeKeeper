from abc import ABC

from beekeeper.adapters.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.entity_input_adapter import EntityInputAdapter


class InputAdapter(EntityInputAdapter, AllocationInputAdapter, ABC):
    pass
