"""
Tests for the algorithm AssignmentState and its per-entity index.

The index is an internal optimization, but the public observable behavior of
add/remove/get must stay consistent with it. These tests pin that behavior down.
"""

from datetime import UTC, datetime
from enum import auto

import pytest

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    Unavailability,
)
from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.assignment import Assignment


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Unavailability]):
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
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    assert state.assignments == []
    worker = _Worker(name="W", unavailabilities=[])
    assert state.get_assignments_done_by(worker) == []


def test_add_assignment_appears_in_planned_and_in_lookup() -> None:
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])
    req = _request(1)
    planned = Assignment(allocation=req, assigned_entities=(worker,))

    state.add_assignment(planned)

    assert state.assignments == [planned]
    assert state.get_assignments_done_by(worker) == [planned]


def test_remove_assignment_clears_both_views() -> None:
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])
    planned = Assignment(allocation=_request(1), assigned_entities=(worker,))

    state.add_assignment(planned)
    state.remove_assignment(planned)

    assert state.assignments == []
    assert state.get_assignments_done_by(worker) == []


def test_multi_entity_allocation_indexed_under_each_entity() -> None:
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    a = _Worker(name="A", unavailabilities=[])
    b = _Worker(name="B", unavailabilities=[])
    planned = Assignment(allocation=_request(1), assigned_entities=(a, b))

    state.add_assignment(planned)

    assert state.get_assignments_done_by(a) == [planned]
    assert state.get_assignments_done_by(b) == [planned]


def test_lookup_isolated_per_entity() -> None:
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    a = _Worker(name="A", unavailabilities=[])
    b = _Worker(name="B", unavailabilities=[])
    plan_a = Assignment(allocation=_request(1), assigned_entities=(a,))
    plan_b = Assignment(allocation=_request(5), assigned_entities=(b,))

    state.add_assignment(plan_a)
    state.add_assignment(plan_b)

    assert state.get_assignments_done_by(a) == [plan_a]
    assert state.get_assignments_done_by(b) == [plan_b]


def test_lookup_returns_a_copy_not_internal_list() -> None:
    """Mutating the returned list must not corrupt internal state."""
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])
    planned = Assignment(allocation=_request(1), assigned_entities=(worker,))
    state.add_assignment(planned)

    returned = state.get_assignments_done_by(worker)
    returned.clear()

    assert state.get_assignments_done_by(worker) == [planned]


def test_remove_then_add_lookup_stays_correct() -> None:
    """Sanity check for the backtracking-style add/remove churn pattern."""
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])
    plan_one = Assignment(allocation=_request(1), assigned_entities=(worker,))
    plan_two = Assignment(allocation=_request(5), assigned_entities=(worker,))

    state.add_assignment(plan_one)
    state.remove_assignment(plan_one)
    state.add_assignment(plan_two)

    assert state.get_assignments_done_by(worker) == [plan_two]
    assert state.assignments == [plan_two]


def test_remove_uses_identity_not_equality() -> None:
    """
    Two structurally-equal ``Assignment`` objects must not be confused.

    ``Assignment`` is a frozen dataclass, so distinct instances built
    from the same allocation and entities compare ``==``. ``list.remove`` matches
    by equality; if we used that, removing one would silently pop the other and
    desync the flat list from the per-entity index. Backtracking-style search
    churn creates exactly this scenario.
    """
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])
    req = _request(1)
    first = Assignment(allocation=req, assigned_entities=(worker,))
    second = Assignment(allocation=req, assigned_entities=(worker,))

    # Pre-condition: the two instances are structurally equal but distinct.
    assert first == second
    assert first is not second

    state.add_assignment(first)
    state.add_assignment(second)

    state.remove_assignment(first)

    # ``second`` survives in both views — identity-based remove pulled only ``first``.
    assert state.assignments == [second]
    assert state.assignments[0] is second
    done = state.get_assignments_done_by(worker)
    assert done == [second]
    assert done[0] is second


def test_remove_missing_allocation_raises_value_error() -> None:
    """Removing an allocation that was never added is a misuse — surface it loudly."""
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])
    stray = Assignment(allocation=_request(1), assigned_entities=(worker,))

    with pytest.raises(ValueError, match="not present"):
        state.remove_assignment(stray)


def test_remove_missing_allocation_with_known_entity_raises_value_error() -> None:
    """
    Even if a different planned allocation for the same entity was added,
    removing one that wasn't added must raise (not silently corrupt state)."""
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])
    other_worker = _Worker(name="O", unavailabilities=[])

    added = Assignment(allocation=_request(1), assigned_entities=(worker,))
    state.add_assignment(added)

    # An allocation whose flat-list lookup succeeds but whose entity bucket does
    # not contain it. We trip this by hand-constructing the corruption: add an
    # allocation referencing an entity that was never indexed.
    not_in_index = Assignment(allocation=_request(5), assigned_entities=(other_worker,))
    state._allocations.append(not_in_index)  # hand-corrupt the flat list to hit the missing-bucket branch

    with pytest.raises(ValueError, match="not present"):
        state.remove_assignment(not_in_index)


def test_remove_inconsistent_entity_bucket_raises_value_error() -> None:
    """
    If the per-entity bucket exists but doesn't contain the allocation,
    we still raise ValueError rather than letting list.remove emit its own."""
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    worker = _Worker(name="W", unavailabilities=[])

    real = Assignment(allocation=_request(1), assigned_entities=(worker,))
    state.add_assignment(real)

    phantom = Assignment(allocation=_request(5), assigned_entities=(worker,))
    state._allocations.append(phantom)  # hand-corrupt the flat list, leaving the entity bucket without it

    with pytest.raises(ValueError, match="not present"):
        state.remove_assignment(phantom)
