from dataclasses import dataclass
from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity


@dataclass(frozen=True)
class PlannedAllocation[TAllocationRequest: AllocationRequest[Any, Any], TEntity: Entity[Any]]:
    """The result of assigning one or more entities to an allocation request.

    Composition rather than inheritance: a planned allocation *has* a request
    and *has* its assigned entities. Treating it as an ``AllocationRequest``
    subclass blurred those concerns and made it harder to add fields like
    assignment confidence or audit trail without polluting the request schema.

    Plain ``@dataclass`` rather than a pydantic ``BaseModel``: planned
    allocations are framework-constructed result objects, not crossings of an
    IO boundary. They never need validation (the request and the entities
    were already validated when they entered the pipeline) and they never
    need to be parsed from JSON. Skipping pydantic also sidesteps the bound
    + ``extra="forbid"`` interaction that would reject domain-specific fields
    on the assigned entities when ``PlannedAllocation`` is constructed
    without explicit parameterization.

    If you need to serialize a planned allocation to JSON, use
    ``dataclasses.asdict`` or write your own serializer in your output
    adapter.
    """

    request: TAllocationRequest
    assigned_entities: tuple[TEntity, ...]
