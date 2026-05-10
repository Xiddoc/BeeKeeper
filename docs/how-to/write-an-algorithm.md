# Write an Algorithm

The bundled `GreedyAssignmentAlgorithm` is a 30-line reference. Copy it as a starting point for your own:

```python
from collections.abc import Iterable, Mapping
from typing import Any
from beekeeper import BaseAlgorithm, PlannedAllocation, State, StatefulRule
from beekeeper.flow.candidate import Candidate


class MyAlgorithm[TEntity: Entity[Any], TAllocReq: AllocationRequest[Any, Any]](
    BaseAlgorithm[TEntity, TAllocReq],
):
    def run(self, allocations, entities, candidates, rules):
        state: State[TEntity, TAllocReq] = State()
        rules_list = list(rules)

        for allocation in allocations:
            ranked = sorted(
                candidates.get(id(allocation), []),
                key=lambda c: c.score,
                reverse=True,
            )
            chosen = []
            for c in ranked:
                if len(chosen) >= allocation.required_count:
                    break
                if all(r.evaluate(c.entity, allocation, state).compatible for r in rules_list):
                    chosen.append(c.entity)
            if len(chosen) == allocation.required_count:
                state.add_allocation(
                    PlannedAllocation(request=allocation, assigned_entities=tuple(chosen))
                )
        return state
```

## The bundled greedy reference

Live at `beekeeper.algorithm.implementations.greedy.GreedyAssignmentAlgorithm`. Picks the highest-scored compatible candidates per allocation in input order, fills `required_count`, skips allocations that can't be filled.

It's a baseline — no backtracking, no global optimization. For nontrivial scheduling, write your own that exploits domain structure.

See [The Algorithm Contract](../concepts/algorithm-contract.md) for what your `run(...)` is allowed to assume and required to return.
