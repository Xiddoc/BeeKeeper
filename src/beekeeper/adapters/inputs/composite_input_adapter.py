from collections.abc import Iterable
from dataclasses import dataclass

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.adapters.inputs.input_adapter import InputAdapter
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity


@dataclass
class CompositeInputAdapter[TEntity: AnyEntity, TAllocationRequest: AnyRequest](
    InputAdapter[TEntity, TAllocationRequest],
):
    """Composes a separate entity adapter and allocation adapter into one ``InputAdapter``.

    The two halves of the input contract — entities and allocations — often
    come from different sources (a workforce DB and a request queue, two
    different JSON files, etc.). This adapter wires them together so the
    ``BeeKeeper`` pipeline can consume a single object.
    """

    entity_adapter: EntityInputAdapter[TEntity]
    allocation_adapter: AllocationInputAdapter[TAllocationRequest]

    def get_entities(self) -> Iterable[TEntity]:
        return self.entity_adapter.get_entities()

    def get_allocations(self) -> Iterable[TAllocationRequest]:
        return self.allocation_adapter.get_allocations()
