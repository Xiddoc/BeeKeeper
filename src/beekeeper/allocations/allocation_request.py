from typing import Optional

from pydantic import BaseModel

from beekeeper.allocations.allocation_type import AllocationType
from beekeeper.entities.entity import Entity
from beekeeper.entities.entity_properties import Exemption, Location, Rank
from beekeeper.inavailabilities.inavailability import Inavailability
from beekeeper.time_constructs.date_range import DateRange


class AllocationRequest[
    TAllocationType: AllocationType,
    TRank: Rank,
    TExemption: Exemption,
    TLocation: Location,
    TEntity: Entity[Inavailability, Exemption, Rank],
](BaseModel):
    allocation_type: TAllocationType
    date_range: DateRange
    location: TLocation
    allowed_ranks: list[TRank]
    prohibited_exemptions: list[TExemption]
    requested_entity: Optional[TEntity] = None
