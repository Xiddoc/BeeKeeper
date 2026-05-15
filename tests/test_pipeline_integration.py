"""Integration tests for the full BeeKeeper pipeline.

Each test sets up a complete (entity, request, rule, algorithm, output)
graph and exercises ``BeeKeeper.execute()`` end-to-end. The tests are
deliberately oriented around pipeline configurations — empty rules,
hard-only rules, soft-only rules, mixed rules, multi-entity allocations,
custom flow stages, edge cases — rather than individual class behavior
(which is covered by the per-module unit tests).
"""

from datetime import UTC, datetime
from enum import auto

from beekeeper import (
    AllocationRequest,
    AllocationType,
    DateRange,
    Entity,
    EntityInputAdapter,
    HardPreliminaryRule,
    Inavailability,
    InputAdapter,
    OutputAdapter,
    PlannedAllocation,
    SoftPreliminaryRule,
    State,
)
from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.mixed_input_adapter import MixedInputAdapter
from beekeeper.algorithm.implementations.load_balancing import LoadBalancingAssignmentAlgorithm
from beekeeper.flow.beekeeper import BeeKeeper
from beekeeper.flow.flow_stages.assign_possible_entities_to_allocations import (
    AssignPossibleEntitiesToAllocations,
)
from beekeeper.flow.flow_stages.run_algorithm_and_dispatch_results import (
    RunAlgorithmAndDispatchResults,
)
from beekeeper.flow.flow_stages.run_preliminary_rules import RunPreliminaryRules
from beekeeper.rules.builtins import AvailabilityRule


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Inavailability]):
    name: str
    skill_level: int = 1


class _Request(AllocationRequest[_Task, _Worker]):
    minimum_skill: int = 0


class _StaticEntities(EntityInputAdapter[_Worker]):
    def __init__(self, entities: list[_Worker]) -> None:
        self._entities = entities

    def get_entities(self) -> list[_Worker]:
        return self._entities


class _StaticAllocations(AllocationInputAdapter[_Request]):
    def __init__(self, allocations: list[_Request]) -> None:
        self._allocations = allocations

    def get_allocations(self) -> list[_Request]:
        return self._allocations


class _CapturingOutput(OutputAdapter[_Worker, _Request]):
    """Output adapter that just stores the State for assertions."""

    def __init__(self) -> None:
        self.captured: State[_Worker, _Request] | None = None

    def handle_output(self, output_state: State[_Worker, _Request]) -> None:
        self.captured = output_state


def _request(start: int, end: int, **kwargs: object) -> _Request:
    return _Request(
        allocation_type=_Task.SHIFT,
        date_range=DateRange(
            start_date=datetime(2025, 1, start, tzinfo=UTC),
            end_date=datetime(2025, 1, end, tzinfo=UTC),
        ),
        **kwargs,  # type: ignore[arg-type]
    )


def _adapter(workers: list[_Worker], requests: list[_Request]) -> InputAdapter[_Worker, _Request]:
    return MixedInputAdapter(
        entity_adapter=_StaticEntities(workers),
        allocation_adapter=_StaticAllocations(requests),
    )


def _bk(
    workers: list[_Worker],
    requests: list[_Request],
    *,
    preliminary_rules: list[HardPreliminaryRule[_Worker, _Request] | SoftPreliminaryRule[_Worker, _Request]]
    | None = None,
    output: _CapturingOutput | None = None,
) -> tuple[BeeKeeper[_Worker, _Request], _CapturingOutput]:
    sink = output or _CapturingOutput()
    bk = BeeKeeper[_Worker, _Request](
        input_adapter=_adapter(workers, requests),
        algorithm=LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
        preliminary_rules=preliminary_rules or [],
        output_adapters=[sink],
    )
    return bk, sink


# --------------------------- minimal happy-path -----------------------------


class TestMinimalPipeline:
    def test_no_rules_assigns_first_compatible_candidate(self) -> None:
        worker = _Worker(name="solo", inavailabilities=[])
        request = _request(1, 2)
        bk, sink = _bk([worker], [request])
        bk.execute()
        assert sink.captured is not None
        assert len(sink.captured.planned_allocations) == 1
        assert sink.captured.planned_allocations[0].assigned_entities == (worker,)

    def test_no_workers_produces_no_planned_allocations(self) -> None:
        request = _request(1, 2)
        bk, sink = _bk([], [request])
        bk.execute()
        assert sink.captured is not None
        assert sink.captured.planned_allocations == []

    def test_no_allocations_produces_no_planned_allocations(self) -> None:
        worker = _Worker(name="solo", inavailabilities=[])
        bk, sink = _bk([worker], [])
        bk.execute()
        assert sink.captured is not None
        assert sink.captured.planned_allocations == []


# --------------------------- rule combinations ------------------------------


class _MinimumSkillRule(HardPreliminaryRule[_Worker, _Request]):
    def check(self, entity: _Worker, allocation: _Request) -> bool:
        return entity.skill_level >= allocation.minimum_skill


class _PreferHigherSkill(SoftPreliminaryRule[_Worker, _Request]):
    def score(self, entity: _Worker, allocation: _Request) -> float:
        return min(entity.skill_level / 10.0, 1.0)


class TestRuleCombinations:
    def test_hard_rule_filters_unsuitable_workers(self) -> None:
        unskilled = _Worker(name="A", inavailabilities=[], skill_level=1)
        skilled = _Worker(name="B", inavailabilities=[], skill_level=5)
        request = _request(1, 2, minimum_skill=3)

        bk, sink = _bk([unskilled, skilled], [request], preliminary_rules=[_MinimumSkillRule()])
        bk.execute()

        assert sink.captured is not None
        planned = sink.captured.planned_allocations
        assert len(planned) == 1
        assert planned[0].assigned_entities == (skilled,)

    def test_soft_rule_picks_highest_scored(self) -> None:
        low = _Worker(name="low", inavailabilities=[], skill_level=2)
        high = _Worker(name="high", inavailabilities=[], skill_level=9)
        request = _request(1, 2)

        bk, sink = _bk([low, high], [request], preliminary_rules=[_PreferHigherSkill()])
        bk.execute()

        assert sink.captured is not None
        assert sink.captured.planned_allocations[0].assigned_entities == (high,)

    def test_mixed_hard_and_soft_rules(self) -> None:
        unskilled = _Worker(name="unskilled", inavailabilities=[], skill_level=1)
        ok = _Worker(name="ok", inavailabilities=[], skill_level=4)
        best = _Worker(name="best", inavailabilities=[], skill_level=9)
        request = _request(1, 2, minimum_skill=3)

        bk, sink = _bk(
            [unskilled, ok, best],
            [request],
            preliminary_rules=[_MinimumSkillRule(), _PreferHigherSkill()],
        )
        bk.execute()

        assert sink.captured is not None
        # unskilled fails the hard rule; best beats ok on the soft rule.
        assert sink.captured.planned_allocations[0].assigned_entities == (best,)


# --------------------------- multi-entity & availability --------------------


class TestMultiEntityAndAvailability:
    def test_multi_entity_allocation_filled(self) -> None:
        a = _Worker(name="a", inavailabilities=[])
        b = _Worker(name="b", inavailabilities=[])
        request = _request(1, 2, required_count=2)

        bk, sink = _bk([a, b], [request])
        bk.execute()

        assert sink.captured is not None
        planned = sink.captured.planned_allocations
        assert len(planned) == 1
        assigned_names = {e.name for e in planned[0].assigned_entities}
        assert assigned_names == {"a", "b"}

    def test_multi_entity_allocation_unfulfillable_is_skipped(self) -> None:
        only_one = _Worker(name="solo", inavailabilities=[])
        request = _request(1, 2, required_count=2)

        bk, sink = _bk([only_one], [request])
        bk.execute()

        assert sink.captured is not None
        assert sink.captured.planned_allocations == []

    def test_availability_rule_excludes_partial_overlap(self) -> None:
        worker = _Worker(
            name="A",
            inavailabilities=[
                Inavailability(
                    start_date=datetime(2025, 1, 3, tzinfo=UTC),
                    end_date=datetime(2025, 1, 4, tzinfo=UTC),
                    reason="appointment",
                ),
            ],
        )
        request = _request(1, 5)

        bk, sink = _bk([worker], [request], preliminary_rules=[AvailabilityRule[_Worker, _Request]()])
        bk.execute()

        assert sink.captured is not None
        # Stage-1 lets partial overlap through, but AvailabilityRule rejects it.
        assert sink.captured.planned_allocations == []

    def test_requested_entities_restricts_assignment(self) -> None:
        chosen = _Worker(name="chosen", inavailabilities=[])
        unchosen = _Worker(name="unchosen", inavailabilities=[])
        request = _request(1, 2, requested_entities=(chosen,))

        bk, sink = _bk([chosen, unchosen], [request])
        bk.execute()

        assert sink.captured is not None
        assert sink.captured.planned_allocations[0].assigned_entities == (chosen,)


# --------------------------- pluggable pipeline -----------------------------


class _PassthroughStage(AssignPossibleEntitiesToAllocations[_Worker, _Request]):
    """Wraps stage 1 and notes that a custom stage list was used."""

    def __init__(self) -> None:
        self.invoked = False

    def run_stage(self, state):  # type: ignore[no-untyped-def]
        self.invoked = True
        return super().run_stage(state)


class TestPluggablePipeline:
    def test_user_supplied_stages_are_used(self) -> None:
        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        sink = _CapturingOutput()
        custom_stage = _PassthroughStage()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [request]),
            stages=[
                custom_stage,
                RunPreliminaryRules[_Worker, _Request](),
                RunAlgorithmAndDispatchResults(
                    algorithms=[LoadBalancingAssignmentAlgorithm[_Worker, _Request]()],
                    output_adapters=[sink],
                ),
            ],
        ).execute()

        assert custom_stage.invoked is True
        assert sink.captured is not None
        assert len(sink.captured.planned_allocations) == 1

    def test_default_pipeline_requires_algorithm(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="algorithm is required"):
            BeeKeeper[_Worker, _Request](
                input_adapter=_adapter([], []),
                # no algorithm, no stages
            )

    def test_custom_post_stage_sees_algorithm_result(self) -> None:
        """A custom stage chained after the algorithm stage must see the
        produced ``State`` on ``state.algorithm_result``. Without that field,
        the pluggable-pipeline contract is hollow: downstream stages can only
        consume the result by re-implementing dispatch."""
        from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
        from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage

        class _CapturePostStage(BaseBeeKeeperFlowStage[_Worker, _Request]):
            def __init__(self) -> None:
                self.seen: State[_Worker, _Request] | None = None

            def run_stage(self, state: BeeKeeperFlowState[_Worker, _Request]) -> BeeKeeperFlowState[_Worker, _Request]:
                self.seen = state.algorithm_result
                return state

        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        sink = _CapturingOutput()
        post = _CapturePostStage()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [request]),
            stages=[
                AssignPossibleEntitiesToAllocations[_Worker, _Request](),
                RunPreliminaryRules[_Worker, _Request](),
                RunAlgorithmAndDispatchResults(
                    algorithms=[LoadBalancingAssignmentAlgorithm[_Worker, _Request]()],
                    output_adapters=[sink],
                ),
                post,
            ],
        ).execute()

        # The post stage observed the same State the output adapter received.
        assert post.seen is not None
        assert sink.captured is not None
        assert post.seen is sink.captured
        assert len(post.seen.planned_allocations) == 1
        assert post.seen.planned_allocations[0].assigned_entities == (worker,)

    def test_algorithm_result_defaults_to_none(self) -> None:
        """A pipeline that omits the algorithm stage leaves ``algorithm_result``
        as ``None`` so callers can detect "no algorithm ran yet"."""
        from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
        from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage

        class _Inspect(BaseBeeKeeperFlowStage[_Worker, _Request]):
            def __init__(self) -> None:
                self.observed_result: State[_Worker, _Request] | None = "sentinel"  # type: ignore[assignment]

            def run_stage(self, state: BeeKeeperFlowState[_Worker, _Request]) -> BeeKeeperFlowState[_Worker, _Request]:
                self.observed_result = state.algorithm_result
                return state

        inspect = _Inspect()
        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([], []),
            stages=[inspect],
        ).execute()

        assert inspect.observed_result is None


# --------------------------- algorithm chain --------------------------------


class _AlwaysFails(LoadBalancingAssignmentAlgorithm[_Worker, _Request]):
    """Test double: a marker algorithm that always reports failure."""

    def run(self, allocations, entities, candidates, rules):  # type: ignore[no-untyped-def]
        from beekeeper.algorithm.errors import IncompleteSolutionError

        raise IncompleteSolutionError("test double — always fails")


class TestAlgorithmChain:
    def test_single_algorithm_works_unchanged(self) -> None:
        """Passing a bare algorithm (not a list) is the common path."""
        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        sink = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [request]),
            algorithm=LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
            output_adapters=[sink],
        ).execute()

        assert sink.captured is not None
        assert len(sink.captured.planned_allocations) == 1

    def test_chain_falls_through_failed_algorithms(self) -> None:
        """An always-failing algorithm at the head; load-balancing after it wins."""
        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        sink = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [request]),
            algorithm=[
                _AlwaysFails(),
                LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
            ],
            output_adapters=[sink],
        ).execute()

        assert sink.captured is not None
        assert len(sink.captured.planned_allocations) == 1

    def test_chain_stops_at_first_success(self) -> None:
        """Load-balancing at the head succeeds; the trailing entries never run."""

        class _ShouldNeverRun(_AlwaysFails):
            def run(self, *args, **kwargs):  # type: ignore[no-untyped-def, override]
                raise AssertionError("trailing algorithm ran when it shouldn't have")

        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        sink = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [request]),
            algorithm=[
                LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
                _ShouldNeverRun(),
            ],
            output_adapters=[sink],
        ).execute()

        assert sink.captured is not None
        assert len(sink.captured.planned_allocations) == 1

    def test_all_algorithms_failing_propagates_last_error(self) -> None:
        """Every algorithm raises → the last error reaches the caller."""
        import pytest

        from beekeeper.algorithm.errors import IncompleteSolutionError

        with pytest.raises(IncompleteSolutionError):
            BeeKeeper[_Worker, _Request](
                input_adapter=_adapter([_Worker(name="W", inavailabilities=[])], [_request(1, 2)]),
                algorithm=[_AlwaysFails(), _AlwaysFails()],
            ).execute()

    def test_empty_chain_rejected(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="must not be empty"):
            BeeKeeper[_Worker, _Request](
                input_adapter=_adapter([], []),
                algorithm=[],
            )

    def test_stage_rejects_empty_algorithms_directly(self) -> None:
        """Constructing the stage with an empty algorithm sequence raises ValueError.

        ``BeeKeeper`` normalizes algorithm input before this stage sees it, so the
        guard here is a defense-in-depth check for callers that wire stages
        manually. This test exercises it directly.
        """
        import pytest

        with pytest.raises(ValueError, match="at least one algorithm"):
            RunAlgorithmAndDispatchResults[_Worker, _Request](algorithms=[], output_adapters=[])


# --------------------------- output adapter handling ------------------------


class TestOutputAdapterDispatch:
    def test_multiple_output_adapters_all_receive_state(self) -> None:
        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        first = _CapturingOutput()
        second = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [request]),
            algorithm=LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
            output_adapters=[first, second],
        ).execute()

        assert first.captured is not None
        assert second.captured is not None
        assert first.captured.planned_allocations == second.captured.planned_allocations

    def test_no_output_adapters_does_not_raise(self) -> None:
        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [request]),
            algorithm=LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
        ).execute()  # no output_adapters; just shouldn't blow up


# --------------------------- planned allocation shape -----------------------


class TestPlannedAllocationShape:
    def test_planned_allocation_carries_request_and_entities(self) -> None:
        worker = _Worker(name="W", inavailabilities=[])
        request = _request(1, 2)
        bk, sink = _bk([worker], [request])
        bk.execute()

        assert sink.captured is not None
        planned = sink.captured.planned_allocations[0]
        assert isinstance(planned, PlannedAllocation)
        assert planned.request is request
        assert planned.assigned_entities == (worker,)
        # Composition (not inheritance): can't access request fields off the planned
        # allocation directly anymore.
        assert hasattr(planned.request, "allocation_type")
        assert not hasattr(planned, "allocation_type")
