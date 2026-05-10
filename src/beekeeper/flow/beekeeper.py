from collections.abc import Iterable
from typing import Any

from beekeeper.adapters.inputs.input_adapter import InputAdapter
from beekeeper.adapters.outputs.output_adapter import OutputAdapter
from beekeeper.algorithm.base_algorithm import BaseAlgorithm
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.assign_possible_entities_to_allocations import AssignPossibleEntitiesToAllocations
from beekeeper.flow.flow_stages.run_algorithm_and_dispatch_results import RunAlgorithmAndDispatchResults
from beekeeper.flow.flow_stages.run_preliminary_rules import RunPreliminaryRules
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


class BeeKeeper[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]:
    """
    Just buzzing along...
                            🐝 ~ ~ ~
                                        Don't mind me...
    """

    def __init__(
        self,
        *,
        algorithm: BaseAlgorithm[TEntity, TAllocationRequest],
        input_adapter: InputAdapter[TEntity, TAllocationRequest],
        preliminary_rules: Iterable[PreliminaryRule[TEntity, TAllocationRequest]] = (),
        stateful_rules: Iterable[StatefulRule[TEntity, TAllocationRequest]] = (),
        output_adapters: Iterable[OutputAdapter[TEntity, TAllocationRequest]] | None = None,
    ) -> None:
        resolved_output_adapters: Iterable[OutputAdapter[TEntity, TAllocationRequest]] = output_adapters or []

        self._preliminary_rules = preliminary_rules
        self._stateful_rules = stateful_rules
        self._input_adapter = input_adapter
        self._stages: list[
            AssignPossibleEntitiesToAllocations[TEntity, TAllocationRequest]
            | RunPreliminaryRules[TEntity, TAllocationRequest]
            | RunAlgorithmAndDispatchResults[TEntity, TAllocationRequest]
        ] = [
            AssignPossibleEntitiesToAllocations(),
            RunPreliminaryRules(),
            RunAlgorithmAndDispatchResults(algorithm=algorithm, output_adapters=resolved_output_adapters),
        ]

    def execute(self) -> None:
        state: BeeKeeperFlowState[TEntity, TAllocationRequest] = BeeKeeperFlowState(
            entities=self._input_adapter.get_entities(),
            allocations=self._input_adapter.get_allocations(),
            preliminary_rules=self._preliminary_rules,
            stateful_rules=self._stateful_rules,
        )

        for stage in self._stages:
            state = stage.run_stage(state)
