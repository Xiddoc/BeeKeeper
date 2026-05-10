from datetime import UTC, datetime
from enum import auto

import pytest

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    Inavailability,
)
from beekeeper.flow.candidate import Candidate

# Skip the whole module if ortools isn't installed (the dep is optional).
pytest.importorskip("ortools.sat.python.cp_model")

from beekeeper.algorithm.implementations.or_tools import OrToolsAssignmentAlgorithm


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Inavailability]):
    name: str


class _Request(AllocationRequest[_Task, _Worker]):
    pass


def _request(start: int, end: int, **kwargs: object) -> _Request:
    return _Request(
        allocation_type=_Task.SHIFT,
        date_range=DateRange(
            start_date=datetime(2025, 1, start, tzinfo=UTC),
            end_date=datetime(2025, 1, end, tzinfo=UTC),
        ),
        **kwargs,  # type: ignore[arg-type]
    )


def test_assigns_simple_problem() -> None:
    worker = _Worker(name="solo", inavailabilities=[])
    request = _request(1, 2)
    candidates = {id(request): [Candidate(entity=worker)]}

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[worker],
        candidates=candidates,
        rules=[],
    )

    assert len(result.planned_allocations) == 1
    assert result.planned_allocations[0].assigned_entities == (worker,)


def test_picks_higher_scored_candidate() -> None:
    a = _Worker(name="A", inavailabilities=[])
    b = _Worker(name="B", inavailabilities=[])
    request = _request(1, 2)
    candidates = {id(request): [Candidate(entity=a, score=0.3), Candidate(entity=b, score=0.9)]}

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[a, b],
        candidates=candidates,
        rules=[],
    )

    assert result.planned_allocations[0].assigned_entities == (b,)


def test_finds_complete_assignment_where_greedy_might_fail() -> None:
    """The OR-Tools optimizer can find a globally-optimal assignment."""
    a = _Worker(name="A", inavailabilities=[])
    b = _Worker(name="B", inavailabilities=[])
    alloc_one = _request(1, 2)
    alloc_two = _request(3, 4)

    # Each worker is the only candidate for one allocation. OR-Tools gets both.
    candidates = {
        id(alloc_one): [Candidate(entity=a)],
        id(alloc_two): [Candidate(entity=b)],
    }

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[alloc_one, alloc_two],
        entities=[a, b],
        candidates=candidates,
        rules=[],
    )

    assert len(result.planned_allocations) == 2


def test_skips_allocation_with_insufficient_candidates() -> None:
    """An allocation whose candidate pool is smaller than required_count goes unfilled."""
    a = _Worker(name="A", inavailabilities=[])
    request = _request(1, 2, required_count=3)
    candidates = {id(request): [Candidate(entity=a)]}

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[a],
        candidates=candidates,
        rules=[],
    )

    assert result.planned_allocations == []


def test_fills_multi_entity_allocation() -> None:
    a = _Worker(name="A", inavailabilities=[])
    b = _Worker(name="B", inavailabilities=[])
    c = _Worker(name="C", inavailabilities=[])
    request = _request(1, 2, required_count=2)
    candidates = {
        id(request): [
            Candidate(entity=a, score=0.5),
            Candidate(entity=b, score=0.9),
            Candidate(entity=c, score=0.7),
        ],
    }

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[a, b, c],
        candidates=candidates,
        rules=[],
    )

    planned = result.planned_allocations
    assert len(planned) == 1
    # OR-Tools picks the two highest-scored: B and C.
    assigned_names = {e.name for e in planned[0].assigned_entities}
    assert assigned_names == {"B", "C"}
