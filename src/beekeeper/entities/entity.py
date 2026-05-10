from typing import Any

from pydantic import BaseModel, ConfigDict

from beekeeper.inavailabilities.inavailability import Inavailability


class Entity[TInavailability: Inavailability[Any]](BaseModel):
    model_config = ConfigDict(extra="forbid")
    inavailabilities: list[TInavailability]
