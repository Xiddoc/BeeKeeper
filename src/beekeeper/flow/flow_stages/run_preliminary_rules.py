from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class RunPreliminaryRules(BaseBeeKeeperFlowStage):
    """
    Runs the preliminary rules in a single pass with no "complex" computation/algorithm needed.
    Preliminary rules can be run before the algorithm, since they have no dynamic properties
    that only could be calculated during processing.
    """

    def run_stage(self, state: BeeKeeperFlowState) -> BeeKeeperFlowState:
        for entity in state.entities:
            for allocation in state.allocations:
                for rule in state.preliminary_rules:
                    if rule.is_compatible(entity, allocation):
                        pass  # TODO: complete this logic
