# Write a Stateful Rule

```python
from beekeeper import HardStatefulRule, AssignmentState


class MaxThreeShiftsPerWeek(HardStatefulRule[MyWorker, MyRequest]):
    def check(
        self,
        entity: MyWorker,
        allocation: MyRequest,
        state: AssignmentState[MyWorker, MyRequest],
    ) -> bool:
        return len(state.get_allocations_done_by(entity)) < 3
```

`HardStatefulRule[TEntity, TAllocReq]` requires `check(entity, allocation, state) -> bool`. The `state` is the algorithm's in-progress assignment record — already-planned allocations are queryable via `state.get_allocations_done_by(entity)` or `state.planned_allocations`.

The algorithm is responsible for consulting stateful rules during assignment. The framework doesn't run them for you — they're available to your algorithm (typically one of the bundled implementations like `LoadBalancingAssignmentAlgorithm` or `BacktrackingAssignmentAlgorithm`) via the `rules` argument to `Algorithm.run`.

Use stateful rules for facts that depend on what's already been scheduled: shift count caps, consecutive-day limits, rotation requirements, "this entity already worked the previous shift."
