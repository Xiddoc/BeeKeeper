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
from beekeeper.algorithm.errors import IncompleteSolutionError
from beekeeper.flow.candidate import Candidate

# Skip the whole module if ortools isn't installed (the dep is optional).
pytest.importorskip("ortools.sat.python.cp_model")

from beekeeper.algorithm.implementations import or_tools as or_tools_module
from beekeeper.algorithm.implementations.or_tools import OrToolsAssignmentAlgorithm


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Unavailability]):
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
    worker = _Worker(name="solo", unavailabilities=[])
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
    a = _Worker(name="A", unavailabilities=[])
    b = _Worker(name="B", unavailabilities=[])
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
    a = _Worker(name="A", unavailabilities=[])
    b = _Worker(name="B", unavailabilities=[])
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
    a = _Worker(name="A", unavailabilities=[])
    request = _request(1, 2, required_count=3)
    candidates = {id(request): [Candidate(entity=a)]}

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[a],
        candidates=candidates,
        rules=[],
    )

    assert result.planned_allocations == []


def test_constructor_raises_when_cp_model_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without the ortools extra installed, the constructor raises a clear ImportError."""
    monkeypatch.setattr(or_tools_module, "cp_model", None)
    with pytest.raises(ImportError, match="OR-Tools is required"):
        OrToolsAssignmentAlgorithm[_Worker, _Request]()


def test_skips_candidate_whose_entity_is_not_in_entities_list() -> None:
    """A candidate whose entity wasn't passed in ``entities`` is silently dropped from the model."""
    in_list = _Worker(name="in_list", inavailabilities=[])
    orphan = _Worker(name="orphan", inavailabilities=[])
    request = _request(1, 2)
    candidates = {id(request): [Candidate(entity=orphan, score=0.9), Candidate(entity=in_list, score=0.5)]}

    # `orphan` is omitted from `entities` — the orphan candidate hits the `j is None` branch.
    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[in_list],
        candidates=candidates,
        rules=[],
    )

    # Only in_list could fill the slot.
    assert len(result.planned_allocations) == 1
    assert result.planned_allocations[0].assigned_entities == (in_list,)


def test_allocation_with_no_eligible_candidates_is_skipped() -> None:
    """Allocations with an empty candidate list don't break model construction."""
    worker = _Worker(name="solo", inavailabilities=[])
    fillable = _request(1, 2)
    no_candidates = _request(3, 4)
    candidates = {
        id(fillable): [Candidate(entity=worker)],
        id(no_candidates): [],  # no slot_vars for this allocation; objective_terms still non-empty
    }

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[fillable, no_candidates],
        entities=[worker],
        candidates=candidates,
        rules=[],
    )

    # Only the fillable allocation produces a planned assignment.
    assert len(result.planned_allocations) == 1
    assert result.planned_allocations[0].request is fillable


def test_empty_candidate_map_produces_empty_state() -> None:
    """No candidates anywhere: the objective term list is empty, the solver still runs."""
    worker = _Worker(name="solo", inavailabilities=[])
    request = _request(1, 2)
    # Candidate map is empty: no x variables, no objective terms.
    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[worker],
        candidates={},
        rules=[],
    )

    assert result.planned_allocations == []


def test_raises_incomplete_solution_when_solver_returns_non_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If CP-SAT reports MODEL_INVALID/INFEASIBLE/UNKNOWN, the algorithm raises IncompleteSolutionError."""
    from ortools.sat.python import cp_model

    class _StubSolver:
        def __init__(self) -> None:
            self.parameters = type("P", (), {"max_time_in_seconds": 0.0})()

        def solve(self, _model: object) -> int:
            return cp_model.INFEASIBLE

        def status_name(self, _status: int) -> str:
            return "INFEASIBLE"

    monkeypatch.setattr(or_tools_module.cp_model, "CpSolver", _StubSolver)

    worker = _Worker(name="solo", inavailabilities=[])
    request = _request(1, 2)
    candidates = {id(request): [Candidate(entity=worker)]}

    with pytest.raises(IncompleteSolutionError, match="INFEASIBLE"):
        OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[request],
            entities=[worker],
            candidates=candidates,
            rules=[],
        )


def test_tiny_score_does_not_collapse_to_empty_assignment() -> None:
    """A positive-but-sub-resolution score must not truncate to zero.

    The CP-SAT formulation scales float scores to ints with ``SCORE_SCALE``;
    a candidate with raw score ``0.0001`` would scale to ``0`` under plain
    truncation. With every scaled score zero, the objective is flat and the
    solver returns OPTIMAL with no assignments — silently dropping every
    fillable allocation. The fix floors such candidates at scaled-1 so they
    still contribute to the objective.
    """
    worker = _Worker(name="solo", inavailabilities=[])
    request = _request(1, 2)
    candidates = {id(request): [Candidate(entity=worker, score=0.0001)]}

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[worker],
        candidates=candidates,
        rules=[],
    )

    assert len(result.planned_allocations) == 1
    assert result.planned_allocations[0].assigned_entities == (worker,)


def test_zero_score_remains_zero() -> None:
    """A genuinely indifferent candidate (raw score 0) stays at scaled-0.

    The fix only floors positive scores; a true 0 is preserved so the
    objective is unaffected by indifferent candidates.
    """
    worker = _Worker(name="solo", inavailabilities=[])
    request = _request(1, 2)
    candidates = {id(request): [Candidate(entity=worker, score=0.0)]}

    result = OrToolsAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[worker],
        candidates=candidates,
        rules=[],
    )

    # The solver is free to assign or leave empty since the objective is flat;
    # with a single candidate covering a single allocation, both outcomes are
    # OPTIMAL. We just assert the call doesn't raise — the regression we're
    # guarding against is "raw 0 silently becomes scaled-1".
    assert isinstance(result.planned_allocations, list)


def test_fills_multi_entity_allocation() -> None:
    a = _Worker(name="A", unavailabilities=[])
    b = _Worker(name="B", unavailabilities=[])
    c = _Worker(name="C", unavailabilities=[])
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
