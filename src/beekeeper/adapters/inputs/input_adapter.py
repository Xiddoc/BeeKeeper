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
    """The contract ``BeeKeeper`` consumes: a single source for both entities and allocations.

    Implement this directly when one source naturally yields both (a single
    database, a single JSON document), or use ``CompositeInputAdapter`` to
    wire two separate ``EntityInputAdapter`` / ``AllocationInputAdapter``
    instances together.
    """
