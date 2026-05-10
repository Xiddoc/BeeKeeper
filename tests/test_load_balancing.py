from datetime import UTC, datetime
from enum import auto

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    Inavailability,
)
from beekeeper.algorithm.implementations.load_balancing import LoadBalancingAssignmentAlgorithm
from beekeeper.flow.candidate import Candidate


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


def test_disperses_load_across_equally_scored_workers() -> None:
    """Two workers, both score 1.0, three allocations — load balancing distributes."""
    a = _Worker(name="A", inavailabilities=[])
    b = _Worker(name="B", inavailabilities=[])
    requests = [_request(1, 2), _request(3, 4), _request(5, 6)]

    candidates = {id(r): [Candidate(entity=a, score=1.0), Candidate(entity=b, score=1.0)] for r in requests}

    result = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=requests,
        entities=[a, b],
        candidates=candidates,
        rules=[],
    )

    # All three allocations are filled.
    assert len(result.planned_allocations) == 3
    # Load distributes: each worker gets at least one allocation.
    a_count = sum(1 for p in result.planned_allocations if a in p.assigned_entities)
    b_count = sum(1 for p in result.planned_allocations if b in p.assigned_entities)
    assert a_count >= 1
    assert b_count >= 1


def test_high_score_still_wins_against_load_penalty() -> None:
    """Score difference can outweigh the load penalty."""
    overworked = _Worker(name="overworked", inavailabilities=[])
    fresh = _Worker(name="fresh", inavailabilities=[])
    requests = [_request(1, 2), _request(3, 4)]

    # First allocation has only `overworked` as candidate (so it has load=1 going into the second).
    # Second allocation: overworked scores 0.95, fresh scores 0.4.
    # Adjusted: overworked = 0.95/(1+1)=0.475; fresh = 0.4/(1+0)=0.4.
    # Overworked still wins.
    candidates = {
        id(requests[0]): [Candidate(entity=overworked, score=1.0)],
        id(requests[1]): [
            Candidate(entity=overworked, score=0.95),
            Candidate(entity=fresh, score=0.4),
        ],
    }

    result = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=requests,
        entities=[overworked, fresh],
        candidates=candidates,
        rules=[],
    )

    assert result.planned_allocations[1].assigned_entities == (overworked,)


def test_load_penalty_picks_fresh_entity_at_close_scores() -> None:
    """When base scores are similar, prior load tips the balance."""
    busy = _Worker(name="busy", inavailabilities=[])
    fresh = _Worker(name="fresh", inavailabilities=[])
    requests = [_request(1, 2), _request(3, 4)]

    # First: only busy is a candidate; busy gets one assignment.
    # Second: both are candidates with the SAME raw score.
    # Adjusted: busy = 0.8/(1+1)=0.4; fresh = 0.8/(1+0)=0.8 — fresh wins.
    candidates = {
        id(requests[0]): [Candidate(entity=busy, score=0.8)],
        id(requests[1]): [
            Candidate(entity=busy, score=0.8),
            Candidate(entity=fresh, score=0.8),
        ],
    }

    result = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=requests,
        entities=[busy, fresh],
        candidates=candidates,
        rules=[],
    )

    assert result.planned_allocations[1].assigned_entities == (fresh,)


def test_first_allocation_behaves_like_greedy() -> None:
    """With no prior load, the algorithm picks the highest-scored candidate."""
    a = _Worker(name="A", inavailabilities=[])
    b = _Worker(name="B", inavailabilities=[])
    request = _request(1, 2)
    candidates = {id(request): [Candidate(entity=a, score=0.3), Candidate(entity=b, score=0.9)]}

    result = LoadBalancingAssignmentAlgorithm[_Worker, _Request]().run(
        allocations=[request],
        entities=[a, b],
        candidates=candidates,
        rules=[],
    )

    assert result.planned_allocations[0].assigned_entities == (b,)
