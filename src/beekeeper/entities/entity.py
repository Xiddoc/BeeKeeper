from typing import Any

from pydantic import BaseModel, ConfigDict

from beekeeper.unavailabilities.unavailability import Unavailability


class Entity[TUnavailability: Unavailability[Any]](BaseModel):
    model_config = ConfigDict(extra="forbid")
    unavailabilities: list[TUnavailability]
