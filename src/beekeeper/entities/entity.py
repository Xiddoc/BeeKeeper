from collections.abc import Iterable

from pydantic import BaseModel

from beekeeper.inavailabilities.inavailability import Inavailability


class Entity[TInavailability: Inavailability](BaseModel):
    inavailabilities: Iterable[TInavailability]
