from collections.abc import Iterable

from beekeeper.adapters.outputs.output_adapter import OutputAdapter
from beekeeper.algorithm.base_algorithm import BaseAlgorithm
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class RunAlgorithmAndDispatchResults(BaseBeeKeeperFlowStage):
    """
    Runs the core algorithm which will be doing the allocation sorting.
    After the algorithm completes, it dispatches the results to the output adapters.
    """

    def __init__(self, algorithm: BaseAlgorithm, output_adapters: Iterable[OutputAdapter]) -> None:
        self._algorithm = algorithm
        self._output_adapters = output_adapters

    def run_stage(self, state: BeeKeeperFlowState) -> BeeKeeperFlowState:
        output_state = self._algorithm.run(
            allocations=state.allocations, entities=state.entities, rules=state.stateful_rules
        )

        for output_adapter in self._output_adapters:
            output_adapter.handle_output(output_state)

        return state
