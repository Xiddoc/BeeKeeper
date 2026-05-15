import math
from datetime import UTC, datetime
from enum import auto

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    HardPreliminaryRule,
    SoftPreliminaryRule,
    Unavailability,
)
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.candidate import Candidate
from beekeeper.flow.flow_stages.run_preliminary_rules import RunPreliminaryRules


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


class _RejectByName(HardPreliminaryRule[_Worker, _Request]):
    def __init__(self, banned: str) -> None:
        self._banned = banned

    def check(self, entity: _Worker, allocation: _Request) -> bool:
        return entity.name != self._banned


class _ScoreByLength(SoftPreliminaryRule[_Worker, _Request]):
    """Score: 1 / (len(name) or 1) — longer names get lower scores."""

    def score(self, entity: _Worker, allocation: _Request) -> float:
        return 1.0 / (len(entity.name) or 1)


def test_hard_rule_failure_prunes_candidate() -> None:
    keeper = _Worker(name="Alice", unavailabilities=[])
    rejected = _Worker(name="Bob", unavailabilities=[])
    allocation = _request()
    state: BeeKeeperFlowState[_Worker, _Request] = BeeKeeperFlowState(
        entities=[keeper, rejected],
        allocations=[allocation],
        preliminary_rules=[_RejectByName(banned="Bob")],
        stateful_rules=[],
        candidate_map={id(allocation): [Candidate(entity=keeper), Candidate(entity=rejected)]},
    )

    RunPreliminaryRules[_Worker, _Request]().run_stage(state)

    survivors = state.candidate_map[id(allocation)]
    assert [c.entity for c in survivors] == [keeper]


def test_soft_rule_updates_candidate_score() -> None:
    short = _Worker(name="Al", unavailabilities=[])  # 1/2 = 0.5
    long = _Worker(name="Reginald", unavailabilities=[])  # 1/8 = 0.125
    allocation = _request()
    state: BeeKeeperFlowState[_Worker, _Request] = BeeKeeperFlowState(
        entities=[short, long],
        allocations=[allocation],
        preliminary_rules=[_ScoreByLength()],
        stateful_rules=[],
        candidate_map={id(allocation): [Candidate(entity=short), Candidate(entity=long)]},
    )

    RunPreliminaryRules[_Worker, _Request]().run_stage(state)

    by_name = {c.entity.name: c.score for c in state.candidate_map[id(allocation)]}
    assert math.isclose(by_name["Al"], 0.5)
    assert math.isclose(by_name["Reginald"], 0.125)


def test_geometric_mean_combines_multiple_soft_rules() -> None:
    class _Score04(SoftPreliminaryRule[_Worker, _Request]):
        def score(self, entity: _Worker, allocation: _Request) -> float:
            return 0.4

    class _Score09(SoftPreliminaryRule[_Worker, _Request]):
        def score(self, entity: _Worker, allocation: _Request) -> float:
            return 0.9

    worker = _Worker(name="W", unavailabilities=[])
    allocation = _request()
    state: BeeKeeperFlowState[_Worker, _Request] = BeeKeeperFlowState(
        entities=[worker],
        allocations=[allocation],
        preliminary_rules=[_Score04(), _Score09()],
        stateful_rules=[],
        candidate_map={id(allocation): [Candidate(entity=worker)]},
    )

    RunPreliminaryRules[_Worker, _Request]().run_stage(state)

    # geometric mean of [0.4, 0.9] = sqrt(0.36) = 0.6
    survivor_score = state.candidate_map[id(allocation)][0].score
    assert abs(survivor_score - 0.6) < 1e-9


def test_zero_score_short_circuits_geometric_mean_to_zero() -> None:
    """A soft rule that scores 0 collapses the aggregate to 0 without invoking log(0)."""

    class _ZeroScore(SoftPreliminaryRule[_Worker, _Request]):
        def score(self, entity: _Worker, allocation: _Request) -> float:
            return 0.0

    worker = _Worker(name="W", unavailabilities=[])
    allocation = _request()
    state: BeeKeeperFlowState[_Worker, _Request] = BeeKeeperFlowState(
        entities=[worker],
        allocations=[allocation],
        preliminary_rules=[_ZeroScore()],
        stateful_rules=[],
        candidate_map={id(allocation): [Candidate(entity=worker)]},
    )

    RunPreliminaryRules[_Worker, _Request]().run_stage(state)

    assert state.candidate_map[id(allocation)][0].score == 0.0


def test_no_rules_leaves_score_neutral() -> None:
    worker = _Worker(name="W", unavailabilities=[])
    allocation = _request()
    state: BeeKeeperFlowState[_Worker, _Request] = BeeKeeperFlowState(
        entities=[worker],
        allocations=[allocation],
        preliminary_rules=[],
        stateful_rules=[],
        candidate_map={id(allocation): [Candidate(entity=worker)]},
    )

    RunPreliminaryRules[_Worker, _Request]().run_stage(state)

    assert state.candidate_map[id(allocation)][0].score == 1.0
