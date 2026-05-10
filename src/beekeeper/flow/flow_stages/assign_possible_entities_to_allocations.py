from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class AssignPossibleEntitiesToAllocations[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]](
    BaseBeeKeeperFlowStage[TEntity, TAllocationRequest],
):
    def run_stage(
        self, state: BeeKeeperFlowState[TEntity, TAllocationRequest]
    ) -> BeeKeeperFlowState[TEntity, TAllocationRequest]:
        return state
