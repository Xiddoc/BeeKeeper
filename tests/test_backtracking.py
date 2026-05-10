from datetime import UTC, datetime
from enum import auto

import pytest

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    HardStatefulRule,
    Inavailability,
    State,
)
from beekeeper.algorithm.errors import IncompleteSolutionError
from beekeeper.algorithm.implementations.backtracking import BacktrackingAssignmentAlgorithm
from beekeeper.flow.candidate import Candidate


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Inavailability]):
    name: str


class _Request(AllocationRequest[_Task, _Worker]):
    pass


def _request(start_day: int, end_day: int, **kwargs: object) -> _Request:
    return _Request(
        allocation_type=_Task.SHIFT,
        date_range=DateRange(
            start_date=datetime(2025, 1, start_day, tzinfo=UTC),
            end_date=datetime(2025, 1, end_day, tzinfo=UTC),
        ),
        **kwargs,  # type: ignore[arg-type]
    )


class _NoDoubleBooking(HardStatefulRule[_Worker, _Request]):
    """Disallow assigning the same worker to overlapping allocations."""

    def check(self, entity: _Worker, allocation: _Request, state: State[_Worker, _Request]) -> bool:
        for already in state.get_allocations_done_by(entity):
            if (
                allocation.date_range.start_date <= already.request.date_range.end_date
                and allocation.date_range.end_date >= already.request.date_range.start_date
            ):
                return False
        return True


class TestBacktrackingFindsCompleteSolution:
    def test_assigns_simple_problem(self) -> None:
        worker = _Worker(name="solo", inavailabilities=[])
        request = _request(1, 2)
        candidates = {id(request): [Candidate(entity=worker)]}

        result = BacktrackingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[request],
            entities=[worker],
            candidates=candidates,
            rules=[],
        )

        assert len(result.planned_allocations) == 1

    def test_assigns_two_independent_allocations(self) -> None:
        """Two non-overlapping allocations both filled."""
        worker_a = _Worker(name="A", inavailabilities=[])
        worker_b = _Worker(name="B", inavailabilities=[])
        alloc_first = _request(1, 2)
        alloc_second = _request(10, 11)

        candidates = {
            id(alloc_first): [Candidate(entity=worker_a)],
            id(alloc_second): [Candidate(entity=worker_b)],
        }

        result = BacktrackingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[alloc_first, alloc_second],
            entities=[worker_a, worker_b],
            candidates=candidates,
            rules=[],
        )

        assert len(result.planned_allocations) == 2


class TestBacktrackingWithOverlappingAllocations:
    def test_overlapping_allocations_force_smart_assignment(self) -> None:
        """Backtracking handles the case greedy fails on."""
        worker_a = _Worker(name="A", inavailabilities=[])
        worker_b = _Worker(name="B", inavailabilities=[])
        # Both allocations cover days 1-2: they OVERLAP.
        alloc_first = _request(1, 2)
        alloc_second = _request(1, 2)

        # alloc_second can ONLY be filled by B. alloc_first can take either.
        # Greedy with score-sorted candidates sees A's score=0.9 for alloc_first,
        # picks A, then alloc_second needs B and gets B. So greedy succeeds.
        # To force backtracking to do better than greedy: alloc_first's
        # candidates rank B first (higher score), so greedy picks B for
        # alloc_first, then alloc_second has no candidate and fails.
        candidates = {
            id(alloc_first): [Candidate(entity=worker_b, score=0.9), Candidate(entity=worker_a, score=0.1)],
            id(alloc_second): [Candidate(entity=worker_b, score=0.9)],
        }

        result = BacktrackingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[alloc_first, alloc_second],
            entities=[worker_a, worker_b],
            candidates=candidates,
            rules=[_NoDoubleBooking()],
        )

        # Backtracking must put A on alloc_first so B is free for alloc_second.
        assert len(result.planned_allocations) == 2
        first_planned = next(p for p in result.planned_allocations if p.request is alloc_first)
        second_planned = next(p for p in result.planned_allocations if p.request is alloc_second)
        assert first_planned.assigned_entities == (worker_a,)
        assert second_planned.assigned_entities == (worker_b,)


class TestBacktrackingRaisesOnIncomplete:
    def test_no_complete_solution_raises_incomplete_solution_error(self) -> None:
        """Backtracking signals failure with an exception so an algorithm chain can fall back."""
        worker = _Worker(name="solo", inavailabilities=[])
        # Two overlapping allocations, only one worker, no-double-booking rule.
        # No complete solution exists.
        alloc_a = _request(1, 2)
        alloc_b = _request(1, 2)

        candidates = {
            id(alloc_a): [Candidate(entity=worker)],
            id(alloc_b): [Candidate(entity=worker)],
        }

        with pytest.raises(IncompleteSolutionError):
            BacktrackingAssignmentAlgorithm[_Worker, _Request]().run(
                allocations=[alloc_a, alloc_b],
                entities=[worker],
                candidates=candidates,
                rules=[_NoDoubleBooking()],
            )


class TestBacktrackingTopKCap:
    def test_top_k_limits_branching(self) -> None:
        """The top_k_candidates parameter controls the search width."""
        workers = [_Worker(name=f"W{i}", inavailabilities=[]) for i in range(50)]
        request = _request(1, 2)
        candidates_list = [Candidate(entity=w, score=1.0 - i / 100) for i, w in enumerate(workers)]
        cap = 5
        algo = BacktrackingAssignmentAlgorithm[_Worker, _Request](top_k_candidates=cap)

        result = algo.run(
            allocations=[request],
            entities=workers,
            candidates={id(request): candidates_list},
            rules=[],
        )

        # First top-K candidate is picked; the rest don't enter consideration.
        assigned = result.planned_allocations[0].assigned_entities
        assert len(assigned) == 1
        assert assigned[0] in workers[:cap]
