# Rules

A *rule* in BeeKeeper is a constraint: given an (entity, allocation) pair, does the entity belong on this allocation, and how strongly? Rules express the part of your domain that "things have to fit." Two axes split them.

## Two axes

|                  | **Hard** (binary verdict) | **Soft** (preference score) |
| ---              | --- | --- |
| **Preliminary** (no in-progress state) | `HardPreliminaryRule` — implement `check(entity, allocation) -> bool` | `SoftPreliminaryRule` — implement `score(entity, allocation) -> float` |
| **Stateful** (sees the in-progress AssignmentState) | `HardStatefulRule` — implement `check(entity, allocation, state) -> bool` | `SoftStatefulRule` — implement `score(entity, allocation, state) -> float` |

The base `PreliminaryRule` and `StatefulRule` classes have a single abstract method, `evaluate(...) -> RuleVerdict`, that returns both axes at once:

```python
@dataclass(frozen=True)
class RuleVerdict:
    compatible: bool
    score: float = 1.0
```

Author a Hard or Soft subclass when you only need one axis (the common case). Author a `PreliminaryRule` / `StatefulRule` directly only when a single rule needs both — e.g. "incompatible if certification expired, score by certification level otherwise."

## Preliminary vs. stateful

**Preliminary** rules are evaluated once per (allocation, candidate) pair before the algorithm runs. They're for facts that don't change as more allocations are scheduled: "is this worker certified for this task," "does the rank match," "is the worker even on the roster." Their verdicts are aggregated in stage 2 and presented to the algorithm as a pruned, scored candidate map.

**Stateful** rules are evaluated by the algorithm during assignment, with access to the current `AssignmentState[TEntity, TAllocationRequest]` (the planned allocations so far). They're for facts that depend on what's already been scheduled: "this worker has already taken three shifts this week," "this entity worked yesterday and needs the day off," "we already have a manager on this shift."

## Hard vs. soft

**Hard** rules are vetoes. A single `compatible=False` prunes the candidate from consideration. Hard rules express requirements: licensing, certification, role eligibility, hard schedule conflicts.

**Soft** rules express preferences. They never veto — `compatible` stays `True` — but they contribute a score that the algorithm can use to break ties or pick the best of several viable candidates. Soft rules express things like "prefer the worker who hasn't done this task recently," "prefer to keep teams together," "minimize commute time."

## Score aggregation

Across multiple rules, scores are combined with the **geometric mean**. See [Soft-rules aggregation](../explanations/soft-rules-aggregation.md) for the rationale.

A score of `1.0` is neutral — a hard rule that passes contributes `1.0`, so combining hard rules and soft rules in the same pipeline doesn't penalize candidates for the hard checks alone.

## See also

- [Write a Preliminary Rule](../how-to/write-a-preliminary-rule.md)
- [Write a Stateful Rule](../how-to/write-a-stateful-rule.md)
- [Write a Soft Rule](../how-to/write-a-soft-rule.md)
- [Soft-rules aggregation](../explanations/soft-rules-aggregation.md)
