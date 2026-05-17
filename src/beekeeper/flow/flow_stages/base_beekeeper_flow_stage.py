from abc import ABC, abstractmethod

from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState


class BaseBeeKeeperFlowStage[TEntity: AnyEntity, TAllocationRequest: AnyRequest](ABC):
    """
    Abstract base for a single step in ``BeeKeeper.execute()``'s pipeline.

    Subclass and override :meth:`run_stage` to add a custom step. Stages
    are composed into a list and each is handed the shared
    ``BeeKeeperFlowState``; the stage mutates and returns it (or returns a
    replacement of the same type) so the next stage sees the cumulative
    pipeline so far.

    The bundled stages — ``AssignPossibleEntitiesToAllocations``,
    ``RunPreliminaryRules``, ``RunAlgorithmAndDispatchResults`` — are
    concrete subclasses. Replace the default 3-stage list by passing
    ``stages=`` to ``BeeKeeper``.
    """

    @abstractmethod
    def run_stage(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> BeeKeeperFlowState[TEntity, TAllocationRequest]:
        """Run this stage against ``state`` and return the (possibly updated) state."""
