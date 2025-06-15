from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from beekeeper.allocations.allocation_type import TAllocationType
from beekeeper.entities.entity import TEntity
from beekeeper.time_constructs.date_range import DateRange


class AllocationRequest(BaseModel, Generic[TAllocationType, TEntity]):
    allocation_type: TAllocationType
    date_range: DateRange
    requested_entity: Optional[TEntity] = None


TAllocationRequest = TypeVar("TAllocationRequest", bound=AllocationRequest)
