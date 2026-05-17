from collections.abc import Callable, Iterable, Sequence
from typing import overload

from beekeeper.adapters.inputs.input_adapter import InputAdapter
from beekeeper.adapters.outputs.output_adapter import OutputAdapter
from beekeeper.algorithm.algorithm import Algorithm
from beekeeper.algorithm.errors import IncompleteSolutionError
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.assign_possible_entities_to_allocations import AssignPossibleEntitiesToAllocations
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage
from beekeeper.flow.flow_stages.run_algorithm_and_dispatch_results import RunAlgorithmAndDispatchResults
from beekeeper.flow.flow_stages.run_preliminary_rules import RunPreliminaryRules
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


class BeeKeeper[TEntity: AnyEntity, TAllocationRequest: AnyRequest]:
    """
    The framework's orchestrator. Wires inputs, rules, an algorithm, and outputs into a runnable pipeline.

    Construct with either ``algorithm=`` (uses the default 3-stage pipeline)
    or ``stages=`` (you own the wiring). Call :meth:`execute` to run it.
    Type parameters flow through every layer so ``BeeKeeper[McWorker,
    McRequest]`` gives you static-checked domain types end-to-end.

    Just buzzing along...
                            🐝 ~ ~ ~
                                        Don't mind me...
    """

    # Two valid constructor shapes, expressed via @overload so mypy enforces
    # the contract at the call site (the previous single-signature version
    # type-checked ``BeeKeeper(input_adapter=...)`` cleanly and then raised
    # at runtime):
    #
    #   1. Default pipeline — ``algorithm=`` is required, ``stages=`` is
    #      forbidden.
    #   2. Custom stages — ``stages=`` is required, the algorithm-chain
    #      kwargs (algorithm, output_adapters, on_incomplete_solution) are
    #      forbidden (the user owns wiring those into their own stages).
    @overload
    def __init__(
        self,
        *,
        input_adapter: InputAdapter[TEntity, TAllocationRequest],
        algorithm: Algorithm[TEntity, TAllocationRequest] | Sequence[Algorithm[TEntity, TAllocationRequest]],
        preliminary_rules: Iterable[PreliminaryRule[TEntity, TAllocationRequest]] = (),
        stateful_rules: Iterable[StatefulRule[TEntity, TAllocationRequest]] = (),
        output_adapters: Sequence[OutputAdapter[TEntity, TAllocationRequest]] = (),
        on_incomplete_solution: Callable[
            [Algorithm[TEntity, TAllocationRequest], IncompleteSolutionError[TEntity, TAllocationRequest]], None
        ]
        | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        input_adapter: InputAdapter[TEntity, TAllocationRequest],
        stages: Sequence[BaseBeeKeeperFlowStage[TEntity, TAllocationRequest]],
        preliminary_rules: Iterable[PreliminaryRule[TEntity, TAllocationRequest]] = (),
        stateful_rules: Iterable[StatefulRule[TEntity, TAllocationRequest]] = (),
    ) -> None: ...

    def __init__(
        self,
        *,
        input_adapter: InputAdapter[TEntity, TAllocationRequest],
        algorithm: (
            Algorithm[TEntity, TAllocationRequest] | Sequence[Algorithm[TEntity, TAllocationRequest]] | None
        ) = None,
        preliminary_rules: Iterable[PreliminaryRule[TEntity, TAllocationRequest]] = (),
        stateful_rules: Iterable[StatefulRule[TEntity, TAllocationRequest]] = (),
        output_adapters: Sequence[OutputAdapter[TEntity, TAllocationRequest]] = (),
        stages: Sequence[BaseBeeKeeperFlowStage[TEntity, TAllocationRequest]] | None = None,
        on_incomplete_solution: Callable[
            [Algorithm[TEntity, TAllocationRequest], IncompleteSolutionError[TEntity, TAllocationRequest]], None
        ]
        | None = None,
    ) -> None:
        if stages is None:
            if algorithm is None:
                msg = "algorithm is required when stages are not supplied (the default pipeline needs one)"
                raise ValueError(msg)

            algorithms_chain = self._normalize_algorithm_chain(algorithm)
            stages = [
                AssignPossibleEntitiesToAllocations(),
                RunPreliminaryRules(),
                RunAlgorithmAndDispatchResults(
                    algorithms=algorithms_chain,
                    output_adapters=output_adapters,
                    on_incomplete_solution=on_incomplete_solution,
                ),
            ]

        self._preliminary_rules = preliminary_rules
        self._stateful_rules = stateful_rules
        self._input_adapter = input_adapter
        self._stages: Sequence[BaseBeeKeeperFlowStage[TEntity, TAllocationRequest]] = stages

    @staticmethod
    def _normalize_algorithm_chain(
        algorithm: (Algorithm[TEntity, TAllocationRequest] | Sequence[Algorithm[TEntity, TAllocationRequest]]),
    ) -> list[Algorithm[TEntity, TAllocationRequest]]:
        """
        Accept either a single algorithm or a sequence; always return a list.

        A user who passes one algorithm gets a one-element chain. A user who
        passes a sequence (list, tuple, etc.) gets that chain. An empty
        sequence raises — the framework needs at least one algorithm to
        produce a schedule.
        """
        if isinstance(algorithm, Algorithm):
            return [algorithm]
        chain = list(algorithm)
        if not chain:
            msg = "algorithm sequence must not be empty"
            raise ValueError(msg)
        return chain

    def execute(self) -> None:
        state: BeeKeeperFlowState[TEntity, TAllocationRequest] = BeeKeeperFlowState(
            entities=list(self._input_adapter.get_entities()),
            allocations=list(self._input_adapter.get_allocations()),
            preliminary_rules=self._preliminary_rules,
            stateful_rules=self._stateful_rules,
        )

        for stage in self._stages:
            state = stage.run_stage(state)
