from datetime import UTC, datetime
from enum import auto

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    Inavailability,
)
from beekeeper.adapters.outputs.console import ConsoleOutputAdapter
from beekeeper.algorithm.algorithm_state import State
from beekeeper.algorithm.implementations.load_balancing import LoadBalancingAssignmentAlgorithm
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule


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


class TestAvailabilityRule:
    def test_partial_overlap_rejects(self) -> None:
        worker = _Worker(
            name="A",
            inavailabilities=[
                Inavailability(
                    start_date=datetime(2025, 1, 4, tzinfo=UTC),
                    end_date=datetime(2025, 1, 6, tzinfo=UTC),
                    reason="dentist",
                ),
            ],
        )
        request = _request(1, 5)
        assert AvailabilityRule[_Worker, _Request]().check(worker, request) is False

    def test_no_overlap_accepts(self) -> None:
        worker = _Worker(
            name="A",
            inavailabilities=[
                Inavailability(
                    start_date=datetime(2025, 1, 10, tzinfo=UTC),
                    end_date=datetime(2025, 1, 15, tzinfo=UTC),
                    reason="vacation",
                ),
            ],
        )
        request = _request(1, 5)
        assert AvailabilityRule[_Worker, _Request]().check(worker, request) is True


class TestRequestedEntityRule:
    def test_empty_requested_entities_accepts_anyone(self) -> None:
        worker = _Worker(name="A", inavailabilities=[])
        request = _request(1, 2)
        assert RequestedEntityRule[_Worker, _Request]().check(worker, request) is True

    def test_non_empty_requested_entities_restricts(self) -> None:
        chosen = _Worker(name="A", inavailabilities=[])
        other = _Worker(name="B", inavailabilities=[])
        request = _request(1, 2, requested_entities=(chosen,))

        rule = RequestedEntityRule[_Worker, _Request]()
        assert rule.check(chosen, request) is True
        assert rule.check(other, request) is False

    def test_identity_not_structural_equality(self) -> None:
        """A look-alike entity (same field values, different object) is rejected.

        Pydantic's auto-generated ``__eq__`` compares fields, so two
        ``_Worker(name="A", inavailabilities=[])`` instances are
        structurally equal. The rule's contract is "the specific
        entity the caller put in the request", so identity is the
        relevant relation.
        """
        chosen = _Worker(name="A", inavailabilities=[])
        lookalike = _Worker(name="A", inavailabilities=[])
        # Sanity check: the two instances are equal-but-distinct.
        assert chosen == lookalike
        assert chosen is not lookalike

        request = _request(1, 2, requested_entities=(chosen,))
        rule = RequestedEntityRule[_Worker, _Request]()
        assert rule.check(chosen, request) is True
        assert rule.check(lookalike, request) is False


class TestLoadBalancingAssignmentAlgorithm:
    def test_picks_highest_scored_candidate(self) -> None:
        low = _Worker(name="low", inavailabilities=[])
        high = _Worker(name="high", inavailabilities=[])
        request = _request(1, 2)
        candidates = {
            id(request): [Candidate(entity=low, score=0.3), Candidate(entity=high, score=0.9)],
        }

        result = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[request],
            entities=[low, high],
            candidates=candidates,
            rules=[],
        )

        planned = result.planned_allocations
        assert len(planned) == 1
        assert planned[0].assigned_entities == (high,)

    def test_skips_allocation_when_required_count_unmet(self) -> None:
        worker = _Worker(name="solo", inavailabilities=[])
        request = _request(1, 2, required_count=2)
        candidates = {id(request): [Candidate(entity=worker)]}

        result = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[request],
            entities=[worker],
            candidates=candidates,
            rules=[],
        )

        assert result.planned_allocations == []

    def test_fills_multi_entity_allocation(self) -> None:
        a = _Worker(name="a", inavailabilities=[])
        b = _Worker(name="b", inavailabilities=[])
        c = _Worker(name="c", inavailabilities=[])
        request = _request(1, 2, required_count=2)
        candidates = {
            id(request): [
                Candidate(entity=a, score=0.5),
                Candidate(entity=b, score=0.9),
                Candidate(entity=c, score=0.7),
            ],
        }

        result = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
            allocations=[request],
            entities=[a, b, c],
            candidates=candidates,
            rules=[],
        )

        planned = result.planned_allocations
        assert len(planned) == 1
        # Sorted by score desc: b (0.9), c (0.7), a (0.5) — top 2 chosen
        assert planned[0].assigned_entities == (b, c)


class TestConsoleOutputAdapter:
    def test_prints_each_planned_allocation(self, capsys: object) -> None:
        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        state: State[_Worker, _Request] = State()
        state.add_allocation(PlannedAllocation(request=request, assigned_entities=(worker,)))

        ConsoleOutputAdapter[_Worker, _Request]().handle_output(state)

        captured = capsys.readouterr().out  # type: ignore[attr-defined]
        assert "SHIFT" in captured
        assert "W" in captured
