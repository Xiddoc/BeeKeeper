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

## Bundled implementations

Four reference implementations live under `beekeeper.algorithm.implementations.*`. Pick the one closest to what your domain needs and copy or wrap; or write a fresh implementation against the same `BaseAlgorithm` contract.

| Module | Class | Use when |
| --- | --- | --- |
| `greedy` | `GreedyAssignmentAlgorithm` | Baseline. Picks the highest-scored compatible candidates in input order. No backtracking, no global optimization. |
| `backtracking` | `BacktrackingAssignmentAlgorithm` | Stateful rules + constrained candidate pools. Tries alternative orderings when greedy gets stuck; falls back to greedy when no complete solution exists. Has a configurable top-K cap and iteration budget. |
| `load_balancing` | `LoadBalancingAssignmentAlgorithm` | You want work spread across the entity pool, not concentrated on a few high-scorers. Score is divided by `(1 + load)` so previously-assigned entities are scored down. Deterministic. |
| `or_tools` | `OrToolsAssignmentAlgorithm` | Globally optimal under the modeled constraints. Heaviest dep (~50 MB); requires the optional `ortools` extra (`uv sync --extra ortools` in the repo, `uv add 'beekeeper[ortools]'` from another project, or `pip install 'beekeeper[ortools]'`). Stateful rules are *not* encoded into the CP-SAT formulation — use backtracking if you need them. |

See [The Algorithm Contract](../concepts/algorithm-contract.md) for what your `run(...)` is allowed to assume and required to return.
