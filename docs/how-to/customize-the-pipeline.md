# Customize the Pipeline

The default pipeline is three stages: `AssignPossibleEntitiesToAllocations`, `RunPreliminaryRules`, `RunAlgorithmAndDispatchResults`. Replace the whole sequence by passing `stages=` to `BeeKeeper`:

```python
from beekeeper import BeeKeeper
from beekeeper.flow.flow_stages.assign_possible_entities_to_allocations import (
    AssignPossibleEntitiesToAllocations,
)
from beekeeper.flow.flow_stages.run_preliminary_rules import RunPreliminaryRules
from beekeeper.flow.flow_stages.run_algorithm_and_dispatch_results import (
    RunAlgorithmAndDispatchResults,
)
from my_app.stages import LogCandidatesStage


bk = BeeKeeper[MyWorker, MyRequest](
    input_adapter=...,
    stages=[
        AssignPossibleEntitiesToAllocations[MyWorker, MyRequest](),
        LogCandidatesStage(),  # custom stage you wrote
        RunPreliminaryRules[MyWorker, MyRequest](),
        RunAlgorithmAndDispatchResults(algorithms=[...], output_adapters=[...]),
    ],
)
```

When you supply `stages=`, you own the wiring entirely. The `algorithm` and `output_adapters` kwargs at the `BeeKeeper` level become unavailable on the `stages=` overload — `RunAlgorithmAndDispatchResults` takes its `algorithms=` chain and `output_adapters=` directly in its own constructor, as in the snippet above.

## Writing a custom stage

```python
from beekeeper import AnyEntity, AnyRequest
from beekeeper.flow.beekeeper_flow_state import BeeKeeperFlowState
from beekeeper.flow.flow_stages.base_beekeeper_flow_stage import BaseBeeKeeperFlowStage


class LogCandidatesStage[TEntity: AnyEntity, TAllocReq: AnyRequest](
    BaseBeeKeeperFlowStage[TEntity, TAllocReq],
):
    def run_stage(self, state: BeeKeeperFlowState[TEntity, TAllocReq]):
        for alloc_id, candidates in state.candidate_map.items():
            print(f"alloc {alloc_id}: {len(candidates)} candidates")
        return state
```

Each stage takes the in-flight `BeeKeeperFlowState` and returns it (typically the same object, mutated). The state carries `entities`, `allocations`, `preliminary_rules`, `stateful_rules`, and the per-stage-1-built `candidate_map`.
