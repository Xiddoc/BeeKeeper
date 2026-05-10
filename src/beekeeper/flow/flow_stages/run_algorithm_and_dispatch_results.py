from collections.abc import Iterable
from typing import Any

from beekeeper.adapters.outputs.output_adapter import OutputAdapter
from beekeeper.algorithm.base_algorithm import BaseAlgorithm
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class RunAlgorithmAndDispatchResults[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    BaseBeeKeeperFlowStage[TEntity, TAllocationRequest],
):
    """
    Runs the core algorithm which will be doing the allocation sorting.
    After the algorithm completes, it dispatches the results to the output adapters.
    """

    def __init__(
        self,
        algorithm: BaseAlgorithm[TEntity, TAllocationRequest],
        output_adapters: Iterable[OutputAdapter[TEntity, TAllocationRequest]],
    ) -> None:
        self._algorithm = algorithm
        self._output_adapters = output_adapters

    def run_stage(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> BeeKeeperFlowState[TEntity, TAllocationRequest]:
        output_state = self._algorithm.run(
            allocations=state.allocations, entities=state.entities, rules=state.stateful_rules
        )

        for output_adapter in self._output_adapters:
            output_adapter.handle_output(output_state)

        return state
