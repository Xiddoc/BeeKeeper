from typing import Any

from pydantic import BaseModel

from beekeeper.allocations.allocation_type import AllocationType
from beekeeper.entities.entity import Entity
from beekeeper.time_constructs.date_range import DateRange


class AllocationRequest[TAllocationType: AllocationType, TEntity: Entity[Any]](BaseModel):
    allocation_type: TAllocationType
    date_range: DateRange
    requested_entity: TEntity | None = None
