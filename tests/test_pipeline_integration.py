"""Integration tests for the full BeeKeeper pipeline.

Each test sets up a complete (entity, allocation, rule, algorithm, output)
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
    Assignment,
    AssignmentState,
    DateRange,
    Entity,
    EntityInputAdapter,
    HardPreliminaryRule,
    InputAdapter,
    OutputAdapter,
    SoftPreliminaryRule,
    Unavailability,
)
from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.adapters.inputs.composite_input_adapter import CompositeInputAdapter
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


class _Worker(Entity[Unavailability]):
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
    """Output adapter that just stores the AssignmentState for assertions."""

    def __init__(self) -> None:
        self.captured: AssignmentState[_Worker, _Request] | None = None

    def handle_output(self, output_state: AssignmentState[_Worker, _Request]) -> None:
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
    return CompositeInputAdapter(
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
        worker = _Worker(name="solo", unavailabilities=[])
        allocation = _request(1, 2)
        bk, sink = _bk([worker], [allocation])
        bk.execute()
        assert sink.captured is not None
        assert len(sink.captured.assignments) == 1
        assert sink.captured.assignments[0].assigned_entities == (worker,)

    def test_no_workers_produces_no_assignments(self) -> None:
        allocation = _request(1, 2)
        bk, sink = _bk([], [allocation])
        bk.execute()
        assert sink.captured is not None
        assert sink.captured.assignments == []

    def test_no_allocations_produces_no_assignments(self) -> None:
        worker = _Worker(name="solo", unavailabilities=[])
        bk, sink = _bk([worker], [])
        bk.execute()
        assert sink.captured is not None
        assert sink.captured.assignments == []


# --------------------------- rule combinations ------------------------------


class _MinimumSkillRule(HardPreliminaryRule[_Worker, _Request]):
    def check(self, entity: _Worker, allocation: _Request) -> bool:
        return entity.skill_level >= allocation.minimum_skill


class _PreferHigherSkill(SoftPreliminaryRule[_Worker, _Request]):
    def score(self, entity: _Worker, allocation: _Request) -> float:
        return min(entity.skill_level / 10.0, 1.0)


class TestRuleCombinations:
    def test_hard_rule_filters_unsuitable_workers(self) -> None:
        unskilled = _Worker(name="A", unavailabilities=[], skill_level=1)
        skilled = _Worker(name="B", unavailabilities=[], skill_level=5)
        allocation = _request(1, 2, minimum_skill=3)

        bk, sink = _bk([unskilled, skilled], [allocation], preliminary_rules=[_MinimumSkillRule()])
        bk.execute()

        assert sink.captured is not None
        planned = sink.captured.assignments
        assert len(planned) == 1
        assert planned[0].assigned_entities == (skilled,)

    def test_soft_rule_picks_highest_scored(self) -> None:
        low = _Worker(name="low", unavailabilities=[], skill_level=2)
        high = _Worker(name="high", unavailabilities=[], skill_level=9)
        allocation = _request(1, 2)

        bk, sink = _bk([low, high], [allocation], preliminary_rules=[_PreferHigherSkill()])
        bk.execute()

        assert sink.captured is not None
        assert sink.captured.assignments[0].assigned_entities == (high,)

    def test_mixed_hard_and_soft_rules(self) -> None:
        unskilled = _Worker(name="unskilled", unavailabilities=[], skill_level=1)
        ok = _Worker(name="ok", unavailabilities=[], skill_level=4)
        best = _Worker(name="best", unavailabilities=[], skill_level=9)
        allocation = _request(1, 2, minimum_skill=3)

        bk, sink = _bk(
            [unskilled, ok, best],
            [allocation],
            preliminary_rules=[_MinimumSkillRule(), _PreferHigherSkill()],
        )
        bk.execute()

        assert sink.captured is not None
        # unskilled fails the hard rule; best beats ok on the soft rule.
        assert sink.captured.assignments[0].assigned_entities == (best,)


# --------------------------- multi-entity & availability --------------------


class TestMultiEntityAndAvailability:
    def test_multi_entity_allocation_filled(self) -> None:
        a = _Worker(name="a", unavailabilities=[])
        b = _Worker(name="b", unavailabilities=[])
        allocation = _request(1, 2, required_count=2)

        bk, sink = _bk([a, b], [allocation])
        bk.execute()

        assert sink.captured is not None
        planned = sink.captured.assignments
        assert len(planned) == 1
        assigned_names = {e.name for e in planned[0].assigned_entities}
        assert assigned_names == {"a", "b"}

    def test_multi_entity_allocation_unfulfillable_is_skipped(self) -> None:
        only_one = _Worker(name="solo", unavailabilities=[])
        allocation = _request(1, 2, required_count=2)

        bk, sink = _bk([only_one], [allocation])
        bk.execute()

        assert sink.captured is not None
        assert sink.captured.assignments == []

    def test_availability_rule_excludes_partial_overlap(self) -> None:
        worker = _Worker(
            name="A",
            unavailabilities=[
                Unavailability(
                    start_date=datetime(2025, 1, 3, tzinfo=UTC),
                    end_date=datetime(2025, 1, 4, tzinfo=UTC),
                    reason="appointment",
                ),
            ],
        )
        allocation = _request(1, 5)

        bk, sink = _bk([worker], [allocation], preliminary_rules=[AvailabilityRule[_Worker, _Request]()])
        bk.execute()

        assert sink.captured is not None
        # Stage-1 lets partial overlap through, but AvailabilityRule rejects it.
        assert sink.captured.assignments == []

    def test_requested_entities_restricts_assignment(self) -> None:
        chosen = _Worker(name="chosen", unavailabilities=[])
        unchosen = _Worker(name="unchosen", unavailabilities=[])
        allocation = _request(1, 2, requested_entities=(chosen,))

        bk, sink = _bk([chosen, unchosen], [allocation])
        bk.execute()

        assert sink.captured is not None
        assert sink.captured.assignments[0].assigned_entities == (chosen,)


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
        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        sink = _CapturingOutput()
        custom_stage = _PassthroughStage()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
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
        assert len(sink.captured.assignments) == 1

    def test_default_pipeline_requires_algorithm(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="algorithm is required"):
            BeeKeeper[_Worker, _Request](
                input_adapter=_adapter([], []),
                # no algorithm, no stages
            )

    def test_custom_post_stage_sees_algorithm_result(self) -> None:
        """A custom stage chained after the algorithm stage must see the
        produced ``AssignmentState`` on ``state.algorithm_result``. Without that field,
        the pluggable-pipeline contract is hollow: downstream stages can only
        consume the result by re-implementing dispatch."""
        from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
        from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage

        class _CapturePostStage(BaseBeeKeeperFlowStage[_Worker, _Request]):
            def __init__(self) -> None:
                self.seen: AssignmentState[_Worker, _Request] | None = None

            def run_stage(self, state: BeeKeeperFlowState[_Worker, _Request]) -> BeeKeeperFlowState[_Worker, _Request]:
                self.seen = state.algorithm_result
                return state

        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        sink = _CapturingOutput()
        post = _CapturePostStage()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
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

        # The post stage observed the same AssignmentState the output adapter received.
        assert post.seen is not None
        assert sink.captured is not None
        assert post.seen is sink.captured
        assert len(post.seen.assignments) == 1
        assert post.seen.assignments[0].assigned_entities == (worker,)

    def test_algorithm_result_defaults_to_none(self) -> None:
        """A pipeline that omits the algorithm stage leaves ``algorithm_result``
        as ``None`` so callers can detect "no algorithm ran yet"."""
        from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
        from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage

        class _Inspect(BaseBeeKeeperFlowStage[_Worker, _Request]):
            def __init__(self) -> None:
                self.observed_result: AssignmentState[_Worker, _Request] | None = "sentinel"  # type: ignore[assignment]

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
        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        sink = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
            algorithm=LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
            output_adapters=[sink],
        ).execute()

        assert sink.captured is not None
        assert len(sink.captured.assignments) == 1

    def test_chain_falls_through_failed_algorithms(self) -> None:
        """An always-failing algorithm at the head; load-balancing after it wins."""
        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        sink = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
            algorithm=[
                _AlwaysFails(),
                LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
            ],
            output_adapters=[sink],
        ).execute()

        assert sink.captured is not None
        assert len(sink.captured.assignments) == 1

    def test_chain_stops_at_first_success(self) -> None:
        """Load-balancing at the head succeeds; the trailing entries never run."""

        class _ShouldNeverRun(_AlwaysFails):
            def run(self, *args, **kwargs):  # type: ignore[no-untyped-def, override]
                raise AssertionError("trailing algorithm ran when it shouldn't have")

        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        sink = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
            algorithm=[
                LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
                _ShouldNeverRun(),
            ],
            output_adapters=[sink],
        ).execute()

        assert sink.captured is not None
        assert len(sink.captured.assignments) == 1

    def test_all_algorithms_failing_propagates_last_error(self) -> None:
        """Every algorithm raises → the *last* error reaches the caller (not the first).

        The chain runs every algorithm in order and keeps the most recent
        ``IncompleteSolutionError`` so a custom fallback's diagnostics, not
        the head's, surface to the caller. Verify by tagging each failure with
        a distinct message and asserting the exception identity matches the
        tail of the chain.
        """
        import pytest

        from beekeeper.algorithm.errors import IncompleteSolutionError

        class _TaggedFailure(_AlwaysFails):
            def __init__(self, tag: str) -> None:
                self._tag = tag

            def run(self, allocations, entities, candidates, rules):  # type: ignore[no-untyped-def]
                raise IncompleteSolutionError(self._tag)

        with pytest.raises(IncompleteSolutionError, match="last") as exc_info:
            BeeKeeper[_Worker, _Request](
                input_adapter=_adapter([_Worker(name="W", unavailabilities=[])], [_request(1, 2)]),
                algorithm=[_TaggedFailure("first"), _TaggedFailure("middle"), _TaggedFailure("last")],
            ).execute()

        assert "first" not in str(exc_info.value)
        assert "middle" not in str(exc_info.value)

    def test_on_incomplete_solution_callback_fires_per_failure(self) -> None:
        """The observability hook receives one (algorithm, exception) call per fallback step."""
        from beekeeper.algorithm.errors import IncompleteSolutionError

        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        sink = _CapturingOutput()
        first = _AlwaysFails()
        second = _AlwaysFails()
        load_balancing = LoadBalancingAssignmentAlgorithm[_Worker, _Request]()
        observed: list[tuple[object, IncompleteSolutionError[_Worker, _Request]]] = []

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
            algorithm=[first, second, load_balancing],
            output_adapters=[sink],
            on_incomplete_solution=lambda algo, exc: observed.append((algo, exc)),
        ).execute()

        # Two failures (first, second); load-balancing succeeds and isn't reported.
        assert [a for a, _ in observed] == [first, second]
        assert all(isinstance(e, IncompleteSolutionError) for _, e in observed)
        assert sink.captured is not None
        assert len(sink.captured.assignments) == 1

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
        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        first = _CapturingOutput()
        second = _CapturingOutput()

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
            algorithm=LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
            output_adapters=[first, second],
        ).execute()

        assert first.captured is not None
        assert second.captured is not None
        assert first.captured.assignments == second.captured.assignments

    def test_no_output_adapters_does_not_raise(self) -> None:
        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)

        BeeKeeper[_Worker, _Request](
            input_adapter=_adapter([worker], [allocation]),
            algorithm=LoadBalancingAssignmentAlgorithm[_Worker, _Request](),
        ).execute()  # no output_adapters; just shouldn't blow up


# --------------------------- planned allocation shape -----------------------


class TestAssignmentShape:
    def test_assignment_carries_request_and_entities(self) -> None:
        worker = _Worker(name="W", unavailabilities=[])
        allocation = _request(1, 2)
        bk, sink = _bk([worker], [allocation])
        bk.execute()

        assert sink.captured is not None
        planned = sink.captured.assignments[0]
        assert isinstance(planned, Assignment)
        assert planned.allocation is allocation
        assert planned.assigned_entities == (worker,)
        # Composition (not inheritance): can't access allocation fields off the planned
        # allocation directly anymore.
        assert hasattr(planned.allocation, "allocation_type")
        assert not hasattr(planned, "allocation_type")
