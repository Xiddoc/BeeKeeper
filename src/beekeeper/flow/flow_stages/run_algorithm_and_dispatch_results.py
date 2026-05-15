from collections.abc import Sequence
from typing import Any

from beekeeper.adapters.outputs.output_adapter import OutputAdapter
from beekeeper.algorithm.algorithm import Algorithm
from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.algorithm.errors import IncompleteSolutionError
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class RunAlgorithmAndDispatchResults[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    BaseBeeKeeperFlowStage[TEntity, TAllocationRequest],
):
    """
    Runs the core algorithm chain and dispatches results to the output adapters.

    Accepts a sequence of algorithms — typically just one, but providing
    several lets a primary algorithm fall back to a simpler one if it can't
    produce a complete solution. Each algorithm is tried in order; if it
    raises ``IncompleteSolutionError``, the next algorithm in the sequence
    runs from scratch. The first non-raising algorithm wins. If every
    algorithm raises, the last error propagates to the caller.

    Putting an always-completing algorithm last in the chain
    (``LoadBalancingAssignmentAlgorithm`` is the one bundled built-in that
    never raises) guarantees the chain produces a result.
    """

    def __init__(
        self,
        algorithms: Sequence[Algorithm[TEntity, TAllocationRequest]],
        output_adapters: Sequence[OutputAdapter[TEntity, TAllocationRequest]],
    ) -> None:
        if not algorithms:
            msg = "RunAlgorithmAndDispatchResults requires at least one algorithm"
            raise ValueError(msg)
        self._algorithms = list(algorithms)
        self._output_adapters = output_adapters

    def run_stage(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> BeeKeeperFlowState[TEntity, TAllocationRequest]:
        output_state = self._run_chain(state)

        # Expose the algorithm's result on the flow state *before* dispatching
        # to output adapters so any user-supplied stage chained after this one
        # can inspect the planned allocations.
        state.algorithm_result = output_state

        for output_adapter in self._output_adapters:
            output_adapter.handle_output(output_state)

        return state

    def _run_chain(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> AssignmentState[TEntity, TAllocationRequest]:
        last_error: IncompleteSolutionError[TEntity, TAllocationRequest] | None = None
        for algorithm in self._algorithms:
            try:
                return algorithm.run(
                    allocations=state.allocations,
                    entities=state.entities,
                    candidates=state.candidate_map,
                    rules=state.stateful_rules,
                )
            except IncompleteSolutionError as exc:
                last_error = exc

        # Every algorithm in the chain raised. Re-raise the last one so the
        # caller can see why the framework couldn't produce a schedule.
        # last_error is guaranteed non-None: __init__ rejects empty sequences
        # so the for loop above ran at least once and either returned or set it.
        if last_error is None:  # pragma: no cover — impossible
            msg = "internal error: empty algorithm chain"
            raise RuntimeError(msg)
        raise last_error
