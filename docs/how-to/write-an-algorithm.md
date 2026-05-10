# Write an Algorithm

The bundled `LoadBalancingAssignmentAlgorithm` is a short reference. Copy it as a starting point for your own:

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
            # The bundled load-balancing reference sorts by score / (1 + load) so
            # already-assigned entities are scored down. A pure-greedy variant
            # would just sort by `c.score` instead.
            ranked = sorted(
                candidates.get(id(allocation), []),
                key=lambda c: c.score / (1 + len(state.get_allocations_done_by(c.entity))),
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

Three reference implementations live under `beekeeper.algorithm.implementations.*`. Pick the one closest to what your domain needs and copy or wrap; or write a fresh implementation against the same `BaseAlgorithm` contract.

| Module | Class | Use when |
| --- | --- | --- |
| `load_balancing` | `LoadBalancingAssignmentAlgorithm` | Default reference. Picks the highest-scored compatible candidates with a per-entity load penalty (`score / (1 + load)`) so work disperses across the pool. Deterministic. Never raises. |
| `backtracking` | `BacktrackingAssignmentAlgorithm` | Stateful rules + constrained candidate pools. Tries alternative orderings to find a complete assignment; raises `IncompleteSolutionError` if it can't, so a chain like `[backtracking, load_balancing]` falls back gracefully. Has a configurable top-K cap and iteration budget. |
| `or_tools` | `OrToolsAssignmentAlgorithm` | Globally optimal under the modeled constraints. Heaviest dep (~50 MB); requires the optional `ortools` extra (`uv sync --extra ortools` in the repo, `uv add 'beekeeper[ortools]'` from another project, or `pip install 'beekeeper[ortools]'`). Stateful rules are *not* encoded into the CP-SAT formulation — use backtracking if you need them. Raises `IncompleteSolutionError` on `INFEASIBLE` / `MODEL_INVALID`. |

See [The Algorithm Contract](../concepts/algorithm-contract.md) for what your `run(...)` is allowed to assume and required to return.
