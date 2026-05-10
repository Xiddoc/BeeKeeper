from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from beekeeper.inavailabilities.inavailability import Inavailability


class Entity[TInavailability: Inavailability[Any]](BaseModel):
    inavailabilities: Iterable[TInavailability]
