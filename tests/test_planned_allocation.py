"""Behavioral tests for ``PlannedAllocation``'s hash + equality contract.

The dataclass is ``frozen=True`` but embeds a pydantic ``BaseModel``
(``request``), and pydantic models are deliberately unhashable. Rather
than letting ``hash(planned)`` fail deep inside set/dict use, the class
explicitly opts out of hashing so the failure is upfront and clear.
"""

from datetime import UTC, datetime
from enum import auto

import pytest

from beekeeper import AllocationRequest, AllocationType, DateRange, Entity, PlannedAllocation, Unavailability


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Unavailability]):
    name: str


class _Request(AllocationRequest[_Task, _Worker]):
    pass


def _request() -> _Request:
    return _Request(
        allocation_type=_Task.SHIFT,
        date_range=DateRange(
            start_date=datetime(2025, 1, 1, tzinfo=UTC),
            end_date=datetime(2025, 1, 2, tzinfo=UTC),
        ),
    )


def test_hash_raises_type_error() -> None:
    """Hashing a planned allocation fails fast and obviously.

    The embedded ``request`` is a pydantic ``BaseModel`` which is
    unhashable by design. The dataclass refuses to advertise a
    ``__hash__`` it can't actually deliver, so the failure surfaces
    here — at the hash call — rather than later inside a set or dict.
    """
    planned = PlannedAllocation(request=_request(), assigned_entities=(_Worker(name="W", unavailabilities=[]),))
    with pytest.raises(TypeError, match="unhashable"):
        hash(planned)


def test_field_equality_preserved() -> None:
    """Setting ``__hash__ = None`` doesn't disturb the dataclass-generated ``__eq__``.

    Two planned allocations built from the same request and the same
    entity tuple still compare equal (the dataclass walks fields and
    pydantic's ``__eq__`` does the right thing on the request).
    """
    request = _request()
    worker = _Worker(name="W", unavailabilities=[])
    a = PlannedAllocation(request=request, assigned_entities=(worker,))
    b = PlannedAllocation(request=request, assigned_entities=(worker,))
    assert a == b


def test_unhashable_in_set() -> None:
    """The unhashability is enforced when inserting into a set, too."""
    planned = PlannedAllocation(request=_request(), assigned_entities=(_Worker(name="W", unavailabilities=[]),))
    with pytest.raises(TypeError, match="unhashable"):
        {planned}  # noqa: B018 — constructing the set is the operation under test
