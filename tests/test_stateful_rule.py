"""Behavior tests for the stateful-rule convenience classes.

``StatefulRule`` itself is an ABC tested implicitly via algorithm tests.
``HardStatefulRule`` is exercised by every algorithm test (the no-double-booking
rule). ``SoftStatefulRule`` has no production caller today, but it's part of
the public API — so we cover its ``evaluate`` wrapper directly.
"""

from datetime import UTC, datetime
from enum import auto

from beekeeper import (
    AllocationRequest,
    AllocationType,
    AssignmentState,
    DateRange,
    Entity,
    SoftStatefulRule,
    Unavailability,
)


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


class _LoadAdjustedScore(SoftStatefulRule[_Worker, _Request]):
    """Score 1.0 for unloaded entities, 0.25 if they already have an assignment."""

    def score(self, entity: _Worker, allocation: _Request, state: AssignmentState[_Worker, _Request]) -> float:
        return 0.25 if state.get_assignments_done_by(entity) else 1.0


def test_soft_stateful_rule_evaluate_returns_compatible_with_score() -> None:
    """``SoftStatefulRule.evaluate`` wraps ``score`` and never vetoes a candidate."""
    worker = _Worker(name="W", unavailabilities=[])
    state: AssignmentState[_Worker, _Request] = AssignmentState()
    rule = _LoadAdjustedScore()

    verdict = rule.evaluate(worker, _request(), state)

    assert verdict.compatible is True
    assert verdict.score == 1.0
