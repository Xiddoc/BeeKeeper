from collections.abc import Iterable

from pydantic import BaseModel

from beekeeper.entities.entity_properties import Exemption, Rank
from beekeeper.inavailabilities.inavailability import Inavailability


class Entity(BaseModel):
    inavailabilities: Iterable[Inavailability]
    exemptions: Iterable[Exemption]
    rank: Rank
