from typing import Any

from pydantic import BaseModel, ConfigDict

from beekeeper.unavailabilities.unavailability import Unavailability


class Entity[TUnavailability: Unavailability[Any]](BaseModel):
    """
    An assignable thing — worker, vehicle, machine — that carries its own time-off list.

    Generic over the concrete ``Unavailability`` subtype so a domain that
    extends the base class (e.g. with an ``is_paid_leave`` boolean) keeps
    its richer type visible end-to-end through the pipeline.
    """

    model_config = ConfigDict(extra="forbid")
    unavailabilities: list[TUnavailability]


# Convenience alias for generic-bound positions where the user just needs
# "any Entity parameterization". Writing ``[TEntity: Entity[Any]]`` on
# every subclass is verbose; ``[TEntity: AnyEntity]`` says the same thing.
type AnyEntity = Entity[Any]
