from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper import AllocationRequest, Entity
from beekeeper.flow.beekeeper_flow_state import BeekeeperFlowState
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


class BaseBeekeeperFlowStage(ABC):

    @abstractmethod
    def run_stage(self, state: BeekeeperFlowState) -> BeekeeperFlowState:
        """
        Handles a single "stage" of the happy flow.
        These stages are split into individual operations on the data so we can add new stages if we'd like,
        and in addition it cleans the code; as opposed to having one big class with several hundred lines of functions.
        """
