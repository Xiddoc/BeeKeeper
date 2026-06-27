from datetime import UTC, datetime
from enum import auto

import pytest

from beekeeper import (
    AllocationRequest,
    AllocationType,
    AssignmentState,
    DateRange,
    Entity,
    HardStatefulRule,
    Unavailability,
)
from beekeeper.algorithm.errors import IncompleteSolutionError
from beekeeper.algorithm.implementations.backtracking import BacktrackingAssignmentAlgorithm
from beekeeper.algorithm.implementations.load_balancing import LoadBalancingAssignmentAlgorithm
from beekeeper.flow.candidate import Candidate


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Unavailability]):
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

    def check(self, entity: _Worker, allocation: _Request, state: AssignmentState[_Worker, _Request]) -> bool:
        for already in state.get_assignments_done_by(entity):
            if (
                allocation.date_range.start_date <= already.allocation.date_range.end_date
                and allocation.date_range.end_date >= already.allocation.date_range.start_date
            ):
                return False
        return True


class TestBacktrackingFindsCompleteSolution:
    def test_assigns_simple_problem(self) -> None:
        worker = _Worker(name="solo", unavailabilities=[])
        allocation = _request(1, 2)
        candidates = {id(allocation): [Candidate(entity=worker)]}

        result = BacktrackingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[allocation],
            entities=[worker],
            candidates=candidates,
            rules=[],
        )

        assert len(result.assignments) == 1

    def test_assigns_two_independent_allocations(self) -> None:
        """Two non-overlapping allocations both filled."""
        worker_a = _Worker(name="A", unavailabilities=[])
        worker_b = _Worker(name="B", unavailabilities=[])
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

        assert len(result.assignments) == 2


class TestBacktrackingWithOverlappingAllocations:
    def test_overlapping_allocations_force_smart_assignment(self) -> None:
        """Backtracking handles the case greedy fails on."""
        worker_a = _Worker(name="A", unavailabilities=[])
        worker_b = _Worker(name="B", unavailabilities=[])
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
        assert len(result.assignments) == 2
        first_planned = next(p for p in result.assignments if p.allocation is alloc_first)
        second_planned = next(p for p in result.assignments if p.allocation is alloc_second)
        assert first_planned.assigned_entities == (worker_a,)
        assert second_planned.assigned_entities == (worker_b,)


class TestBacktrackingRaisesOnIncomplete:
    def test_no_complete_solution_raises_incomplete_solution_error(self) -> None:
        """Backtracking signals failure with an exception so an algorithm chain can fall back."""
        worker = _Worker(name="solo", unavailabilities=[])
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


class TestBacktrackingIterationBudget:
    def test_exhausted_budget_raises_incomplete_solution_error(self) -> None:
        """When the iteration budget hits zero before the search finishes, backtracking gives up."""
        worker_a = _Worker(name="A", unavailabilities=[])
        worker_b = _Worker(name="B", unavailabilities=[])
        # Two non-trivial allocations so the search has to recurse at least once.
        alloc_first = _request(1, 2)
        alloc_second = _request(3, 4)
        candidates = {
            id(alloc_first): [Candidate(entity=worker_a), Candidate(entity=worker_b)],
            id(alloc_second): [Candidate(entity=worker_a), Candidate(entity=worker_b)],
        }

        # max_iterations=0 forces the budget check to trip on the very first recursive call.
        algo = BacktrackingAssignmentAlgorithm[_Worker, _Request](max_iterations=0)

        with pytest.raises(IncompleteSolutionError):
            algo.run(
                allocations=[alloc_first, alloc_second],
                entities=[worker_a, worker_b],
                candidates=candidates,
                rules=[],
            )


class TestBacktrackingTopKCap:
    def test_top_k_limits_branching(self) -> None:
        """The top_k_candidates parameter controls the search width."""
        workers = [_Worker(name=f"W{i}", unavailabilities=[]) for i in range(50)]
        allocation = _request(1, 2)
        candidates_list = [Candidate(entity=w, score=1.0 - i / 100) for i, w in enumerate(workers)]
        cap = 5
        algo = BacktrackingAssignmentAlgorithm[_Worker, _Request](top_k_candidates=cap)

        result = algo.run(
            allocations=[allocation],
            entities=workers,
            candidates={id(allocation): candidates_list},
            rules=[],
        )

        # First top-K candidate is picked; the rest don't enter consideration.
        assigned = result.assignments[0].assigned_entities
        assert len(assigned) == 1
        assert assigned[0] in workers[:cap]

    def test_fills_allocation_when_required_count_exceeds_top_k(self) -> None:
        """An allocation whose required_count exceeds the cap is still filled."""
        workers = [_Worker(name=f"W{i}", unavailabilities=[]) for i in range(5)]
        allocation = _request(1, 2, required_count=4)
        candidates_list = [Candidate(entity=w, score=1.0 - i / 100) for i, w in enumerate(workers)]
        # The cap (3) is below required_count (4). Measuring feasibility against
        # the truncated pool used to drop this allocation even though five
        # genuine candidates can fill it.
        algo = BacktrackingAssignmentAlgorithm[_Worker, _Request](top_k_candidates=3)

        result = algo.run(
            allocations=[allocation],
            entities=workers,
            candidates={id(allocation): candidates_list},
            rules=[],
        )

        assert len(result.assignments) == 1
        assigned = result.assignments[0].assigned_entities
        assert len(assigned) == 4
        # The cap widens only as far as required_count, so the four
        # highest-scored candidates fill the slot and the lowest-scored stays out.
        assert {w.name for w in assigned} == {w.name for w in workers[:4]}

    def test_agrees_with_load_balancing_when_pool_exceeds_cap(self) -> None:
        """Backtracking and load balancing agree on feasibility above the cap."""
        workers = [_Worker(name=f"W{i}", unavailabilities=[]) for i in range(5)]
        allocation = _request(1, 2, required_count=4)
        candidates_list = [Candidate(entity=w, score=1.0 - i / 100) for i, w in enumerate(workers)]
        candidate_map = {id(allocation): candidates_list}

        backtracking = BacktrackingAssignmentAlgorithm[_Worker, _Request](top_k_candidates=3).run(
            allocations=[allocation],
            entities=workers,
            candidates=candidate_map,
            rules=[],
        )
        load_balancing = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[allocation],
            entities=workers,
            candidates=candidate_map,
            rules=[],
        )

        assert len(backtracking.assignments) == len(load_balancing.assignments) == 1
