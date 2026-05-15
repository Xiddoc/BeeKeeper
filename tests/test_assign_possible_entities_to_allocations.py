from datetime import UTC, datetime
from enum import auto

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    Unavailability,
)
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.assign_possible_entities_to_allocations import AssignPossibleEntitiesToAllocations


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Unavailability]):
    name: str = ""


class _Request(AllocationRequest[_Task, _Worker]):
    pass


def _state(entities: list[_Worker], allocations: list[_Request]) -> BeeKeeperFlowState[_Worker, _Request]:
    return BeeKeeperFlowState(
        entities=entities,
        allocations=allocations,
        preliminary_rules=[],
        stateful_rules=[],
    )


def _request(start: datetime, end: datetime, *, requested_entities: tuple[_Worker, ...] = ()) -> _Request:
    return _Request(
        allocation_type=_Task.SHIFT,
        date_range=DateRange(start_date=start, end_date=end),
        requested_entities=requested_entities,
    )


def _inav(start: datetime, end: datetime, reason: str = "out") -> Unavailability:
    return Unavailability(start_date=start, end_date=end, reason=reason)


def test_entity_with_no_unavailability_is_a_candidate() -> None:
    worker = _Worker(unavailabilities=[])
    allocation = _request(datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 1, 2, tzinfo=UTC))
    state = _state([worker], [allocation])

    AssignPossibleEntitiesToAllocations[_Worker, _Request]().run_stage(state)

    assert len(state.candidate_map[id(allocation)]) == 1
    assert state.candidate_map[id(allocation)][0].entity is worker


def test_unavailability_fully_covering_allocation_excludes_entity() -> None:
    worker = _Worker(
        unavailabilities=[_inav(datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 1, 5, tzinfo=UTC))],
    )
    allocation = _request(datetime(2025, 1, 2, tzinfo=UTC), datetime(2025, 1, 4, tzinfo=UTC))
    state = _state([worker], [allocation])

    AssignPossibleEntitiesToAllocations[_Worker, _Request]().run_stage(state)

    assert state.candidate_map[id(allocation)] == []


def test_partial_overlap_does_not_exclude_entity() -> None:
    worker = _Worker(
        unavailabilities=[_inav(datetime(2025, 1, 3, tzinfo=UTC), datetime(2025, 1, 4, tzinfo=UTC))],
    )
    allocation = _request(datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 1, 5, tzinfo=UTC))
    state = _state([worker], [allocation])

    AssignPossibleEntitiesToAllocations[_Worker, _Request]().run_stage(state)

    assert len(state.candidate_map[id(allocation)]) == 1


def test_requested_entities_restricts_candidates() -> None:
    chosen = _Worker(name="chosen", unavailabilities=[])
    other = _Worker(name="other", unavailabilities=[])
    allocation = _request(
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 1, 2, tzinfo=UTC),
        requested_entities=(chosen,),
    )
    state = _state([chosen, other], [allocation])

    AssignPossibleEntitiesToAllocations[_Worker, _Request]().run_stage(state)

    assert [c.entity for c in state.candidate_map[id(allocation)]] == [chosen]


def test_candidates_start_with_neutral_score() -> None:
    worker = _Worker(unavailabilities=[])
    allocation = _request(datetime(2025, 1, 1, tzinfo=UTC), datetime(2025, 1, 2, tzinfo=UTC))
    state = _state([worker], [allocation])

    AssignPossibleEntitiesToAllocations[_Worker, _Request]().run_stage(state)

    assert state.candidate_map[id(allocation)][0].score == 1.0
