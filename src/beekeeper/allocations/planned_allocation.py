from typing import Any

from pydantic import BaseModel

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


class PlannedAllocation[TAllocationRequest: AllocationRequest[Any, Any], TEntity: Entity[Any]](BaseModel):
    """The result of assigning one or more entities to an allocation request.

    Composition rather than inheritance: a planned allocation *has* a request and
    *has* its assigned entities. Treating it as an `AllocationRequest` subclass
    blurred those concerns and made it harder to add fields like assignment
    confidence or audit trail without polluting the request schema.
    """

    request: TAllocationRequest
    assigned_entities: tuple[TEntity, ...]
