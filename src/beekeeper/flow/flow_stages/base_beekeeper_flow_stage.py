from abc import ABC, abstractmethod

from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState


class BaseBeeKeeperFlowStage(ABC):
    @abstractmethod
    def run_stage(self, state: BeeKeeperFlowState) -> BeeKeeperFlowState:
        """
        Handles a single "stage" of the happy flow.
        These stages are split into individual operations on the data so we can add new stages if we'd like,
        and in addition it cleans the code; as opposed to having one big class with several hundred lines of functions.
        """
