from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class RunPreliminaryRules(BaseBeeKeeperFlowStage):
    """
    Runs the preliminary rules in a single pass with no "complex" computation/algorithm needed.
    Preliminary rules can be run before the algorithm, since they have no dynamic properties
    that only could be calculated during processing.
    """

    def run_stage(self, state: BeeKeeperFlowState) -> BeeKeeperFlowState:
        raise NotImplementedError
