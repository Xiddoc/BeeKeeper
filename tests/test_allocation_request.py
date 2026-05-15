"""Validation tests for ``AllocationRequest``.

The pipeline assumes ``required_count`` is a positive integer. Negative
values crash deep in the algorithm layer (``itertools.combinations``
with a negative second argument); zero is silently a no-op that wastes
a candidate-evaluation pass. We reject both at the IO boundary so
malformed JSON inputs fail fast.
"""

from datetime import UTC, datetime
from enum import auto

import pytest
from pydantic import ValidationError

from beekeeper import AllocationRequest, AllocationType, DateRange, Entity, Inavailability


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Inavailability]):
    name: str


class _Request(AllocationRequest[_Task, _Worker]):
    pass


def _date_range() -> DateRange[datetime]:
    return DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=UTC),
        end_date=datetime(2025, 1, 2, tzinfo=UTC),
    )


def test_default_required_count_is_one() -> None:
    request = _Request(allocation_type=_Task.SHIFT, date_range=_date_range())
    assert request.required_count == 1


def test_positive_required_count_accepted() -> None:
    request = _Request(allocation_type=_Task.SHIFT, date_range=_date_range(), required_count=3)
    assert request.required_count == 3


def test_zero_required_count_rejected() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        _Request(allocation_type=_Task.SHIFT, date_range=_date_range(), required_count=0)


def test_negative_required_count_rejected() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 1"):
        _Request(allocation_type=_Task.SHIFT, date_range=_date_range(), required_count=-5)
