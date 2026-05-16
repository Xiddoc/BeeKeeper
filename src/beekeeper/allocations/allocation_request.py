from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from beekeeper.allocations.allocation_type import AllocationType
from beekeeper.entities.entity import AnyEntity
from beekeeper.time_constructs.date_range import DateRange


class AllocationRequest[
    TAllocationType: AllocationType,
    TEntity: AnyEntity,
    TDate: date = datetime,
](BaseModel):
    """A request for entities to be assigned over a date range.

    The third type parameter ``TDate`` controls the granularity of the
    contained ``date_range``. It defaults to ``datetime`` (the common
    case) but a domain that only schedules in whole-day units can
    parameterize as ``AllocationRequest[MyType, MyEntity, date]`` and
    drop the time-of-day component everywhere.
    """

    model_config = ConfigDict(extra="forbid")
    allocation_type: TAllocationType
    date_range: DateRange[TDate]
    # An allocation that asks for zero entities is a no-op the pipeline would
    # silently skip; a negative count would crash downstream in the algorithm
    # layer (e.g. ``combinations(pool, -5)``). Reject both at the IO boundary.
    required_count: int = Field(default=1, ge=1)
    requested_entities: tuple[TEntity, ...] = ()


# Convenience alias for generic-bound positions where the user just needs
# "any AllocationRequest parameterization". Use as
# ``[TRequest: AnyRequest]`` instead of ``[TRequest: AllocationRequest[Any, Any, Any]]``.
type AnyRequest = AllocationRequest[Any, Any, Any]
