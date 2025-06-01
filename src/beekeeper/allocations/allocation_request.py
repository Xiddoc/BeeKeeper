from collections.abc import Iterable
from typing import Optional

from pydantic import BaseModel

from beekeeper.allocations.allocation_type import AllocationType
from beekeeper.entities.entity import Entity
from beekeeper.entities.entity_properties import Exemption, Location, Rank
from beekeeper.time_constructs.date_range import DateRange


class AllocationRequest(BaseModel):
    allocation_type: AllocationType
    date_range: DateRange
    location: Location
    allowed_ranks: Iterable[Rank]
    prohibited_exemptions: Iterable[Exemption]
    requested_entity: Optional[Entity]
