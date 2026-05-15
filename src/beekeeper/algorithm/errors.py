from __future__ import annotations

from typing import TYPE_CHECKING

from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity

if TYPE_CHECKING:
    from beekeeper.algorithm.algorithm_state import AssignmentState


class IncompleteSolutionError[TEntity: AnyEntity, TAllocationRequest: AnyRequest](Exception):
    """Raised by an algorithm that couldn't produce a result it considers complete.

    What "complete" means is the algorithm's call:

    * ``BacktrackingAssignmentAlgorithm`` raises when its search exhausts the
      candidate space (or the iteration budget) without filling every
      feasible allocation.
    * ``OrToolsAssignmentAlgorithm`` raises when CP-SAT reports
      ``INFEASIBLE`` or ``MODEL_INVALID``.
    * ``LoadBalancingAssignmentAlgorithm`` never raises — it returns whatever
      schedule it could fill, which by its semantics is always "complete"
      for what it's trying to do.

    The framework's flow uses this exception to walk through an algorithm
    chain (passed to ``BeeKeeper(algorithm=[...])``): if an algorithm raises,
    the next one in the chain runs from scratch. Putting load-balancing
    last in the chain guarantees the chain always produces a result.

    The optional ``partial_state`` is whatever the algorithm had built up
    when it gave up. It's primarily for inspection/debugging — the chain
    runner doesn't pass it forward to the next algorithm. May be ``None``
    if the algorithm had nothing meaningful to return.

    Parameterized over the same TypeVars as the algorithm that raises it
    so callers who catch and inspect ``partial_state`` get type-checked
    field access rather than ``Any``.
    """

    def __init__(
        self,
        reason: str,
        *,
        partial_state: AssignmentState[TEntity, TAllocationRequest] | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.partial_state: AssignmentState[TEntity, TAllocationRequest] | None = partial_state
