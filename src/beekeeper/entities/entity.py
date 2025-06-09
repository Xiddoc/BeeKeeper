from collections.abc import Iterable
from typing import TypeVar

from pydantic import BaseModel

from beekeeper.inavailabilities.inavailability import Inavailability


class Entity[TInavailability: Inavailability](BaseModel):
    inavailabilities: Iterable[Inavailability]


TEntity = TypeVar("TEntity", bound=Entity)
