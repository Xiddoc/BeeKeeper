from abc import ABC, abstractmethod
from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState


class BaseBeeKeeperFlowStage[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](ABC):
    @abstractmethod
    def run_stage(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> BeeKeeperFlowState[TEntity, TAllocationRequest]:
        """
        Handles a single "stage" of the happy flow.
        These stages are split into individual operations on the data so we can add new stages if we'd like,
        and in addition it cleans the code; as opposed to having one big class with several hundred lines of functions.
        """
