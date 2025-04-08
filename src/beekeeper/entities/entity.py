from collections.abc import Iterable
from dataclasses import dataclass

from beekeeper.entities.entity_properties import Exemption, Rank
from beekeeper.inavailabilities.inavailability import Inavailability


@dataclass
class Entity:
    inavailabilities: Iterable[Inavailability]
    exemptions: Iterable[Exemption]
    rank: Rank
