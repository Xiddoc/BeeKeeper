"""Tests for the algorithm State and its per-entity index.

The index is an internal optimization, but the public observable behavior of
add/remove/get must stay consistent with it. These tests pin that behavior down.
"""

from datetime import UTC, datetime
from enum import auto

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    Inavailability,
)
from beekeeper.algorithm.algorithm_state import State
from beekeeper.allocations.planned_allocation import PlannedAllocation


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Inavailability]):
    name: str


class _Request(AllocationRequest[_Task, _Worker]):
    pass


def _request(start_day: int) -> _Request:
    return _Request(
        allocation_type=_Task.SHIFT,
        date_range=DateRange(
            start_date=datetime(2025, 1, start_day, tzinfo=UTC),
            end_date=datetime(2025, 1, start_day + 1, tzinfo=UTC),
        ),
    )


def test_empty_state_has_no_allocations() -> None:
    state: State[_Worker, _Request] = State()
    assert state.planned_allocations == []
    worker = _Worker(name="W", inavailabilities=[])
    assert state.get_allocations_done_by(worker) == []


def test_add_allocation_appears_in_planned_and_in_lookup() -> None:
    state: State[_Worker, _Request] = State()
    worker = _Worker(name="W", inavailabilities=[])
    req = _request(1)
    planned = PlannedAllocation(request=req, assigned_entities=(worker,))

    state.add_allocation(planned)

    assert state.planned_allocations == [planned]
    assert state.get_allocations_done_by(worker) == [planned]


def test_remove_allocation_clears_both_views() -> None:
    state: State[_Worker, _Request] = State()
    worker = _Worker(name="W", inavailabilities=[])
    planned = PlannedAllocation(request=_request(1), assigned_entities=(worker,))

    state.add_allocation(planned)
    state.remove_allocation(planned)

    assert state.planned_allocations == []
    assert state.get_allocations_done_by(worker) == []


def test_multi_entity_allocation_indexed_under_each_entity() -> None:
    state: State[_Worker, _Request] = State()
    a = _Worker(name="A", inavailabilities=[])
    b = _Worker(name="B", inavailabilities=[])
    planned = PlannedAllocation(request=_request(1), assigned_entities=(a, b))

    state.add_allocation(planned)

    assert state.get_allocations_done_by(a) == [planned]
    assert state.get_allocations_done_by(b) == [planned]


def test_lookup_isolated_per_entity() -> None:
    state: State[_Worker, _Request] = State()
    a = _Worker(name="A", inavailabilities=[])
    b = _Worker(name="B", inavailabilities=[])
    plan_a = PlannedAllocation(request=_request(1), assigned_entities=(a,))
    plan_b = PlannedAllocation(request=_request(5), assigned_entities=(b,))

    state.add_allocation(plan_a)
    state.add_allocation(plan_b)

    assert state.get_allocations_done_by(a) == [plan_a]
    assert state.get_allocations_done_by(b) == [plan_b]


def test_lookup_returns_a_copy_not_internal_list() -> None:
    """Mutating the returned list must not corrupt internal state."""
    state: State[_Worker, _Request] = State()
    worker = _Worker(name="W", inavailabilities=[])
    planned = PlannedAllocation(request=_request(1), assigned_entities=(worker,))
    state.add_allocation(planned)

    returned = state.get_allocations_done_by(worker)
    returned.clear()

    assert state.get_allocations_done_by(worker) == [planned]


def test_remove_then_add_lookup_stays_correct() -> None:
    """Sanity check for the backtracking-style add/remove churn pattern."""
    state: State[_Worker, _Request] = State()
    worker = _Worker(name="W", inavailabilities=[])
    plan_one = PlannedAllocation(request=_request(1), assigned_entities=(worker,))
    plan_two = PlannedAllocation(request=_request(5), assigned_entities=(worker,))

    state.add_allocation(plan_one)
    state.remove_allocation(plan_one)
    state.add_allocation(plan_two)

    assert state.get_allocations_done_by(worker) == [plan_two]
    assert state.planned_allocations == [plan_two]
