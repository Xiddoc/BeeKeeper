from typing import Any


class IncompleteSolutionError(Exception):
    """Raised by an algorithm that couldn't produce a result it considers complete.

    What "complete" means is the algorithm's call:

    * ``BacktrackingAssignmentAlgorithm`` raises when its search exhausts the
      candidate space (or the iteration budget) without filling every
      feasible allocation.
    * ``OrToolsAssignmentAlgorithm`` raises when CP-SAT reports
      ``INFEASIBLE`` or ``MODEL_INVALID``.
    * ``GreedyAssignmentAlgorithm`` and ``LoadBalancingAssignmentAlgorithm``
      never raise — they return whatever partial schedule they could fill,
      which by their semantics is always "complete" for what they're trying
      to do.

    The framework's flow uses this exception to walk through an algorithm
    chain (passed to ``BeeKeeper(algorithm=[...])``): if an algorithm raises,
    the next one in the chain runs from scratch. Putting greedy or
    load-balancing last in the chain guarantees the chain always produces
    a result.

    The optional ``partial_state`` is whatever the algorithm had built up
    when it gave up. It's primarily for inspection/debugging — the chain
    runner doesn't pass it forward to the next algorithm. May be ``None``
    if the algorithm had nothing meaningful to return.
    """

    def __init__(self, reason: str, *, partial_state: Any = None) -> None:  # noqa: ANN401 — the State is generic, error stays type-erased
        super().__init__(reason)
        self.reason = reason
        self.partial_state = partial_state
