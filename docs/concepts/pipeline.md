# The Pipeline

`BeeKeeper.execute()` runs three stages in order. Each one takes a `BeeKeeperFlowState` and returns one — the same object, mutated in place where useful.

```
                  ┌──────────────────────────────────────┐
   InputAdapter   │ stage 1 — AssignPossibleEntitiesTo… │   stage 2 — RunPreliminaryRules
   ─────────────► │ build the candidate map               │   prune by hard rules,
   entities,      │ for each allocation, list the         │   aggregate soft scores
   allocations    │ entities not blocked by an            │   (geometric mean across rules)
                  │ unavailability that fully covers it   │
                  └──────────────────────────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────────────┐
                  │ stage 3 — RunAlgorithmAndDispatch…   │
                  │ algorithm.run(...) → AssignmentState           │
                  │ then output_adapter.handle_output()  │
                  └──────────────────────────────────────┘
```

## What each stage does

### Stage 1 — `AssignPossibleEntitiesToAllocations`

For each allocation, walks the entity list and includes the entity as a candidate **unless** something definitively rules it out:

- The allocation specifies `requested_entities` and this entity isn't in the set.
- The entity has an unavailability whose date range fully covers the allocation's date range.

Partial overlaps **pass through** at this stage. Domain-specific availability semantics (e.g. "any conflict at all disqualifies") belong in a preliminary rule like [`AvailabilityRule`](../how-to/write-a-preliminary-rule.md). This keeps stage 1 cheap and conservative.

Output: `state.candidate_map: dict[int, list[Candidate[TEntity]]]`, keyed by `id(allocation)`. Each `Candidate` starts with a neutral score of `1.0`.

### Stage 2 — `RunPreliminaryRules`

For every (allocation, candidate) pair from stage 1, evaluates every preliminary rule:

- **Compatibility is logical AND.** A single `compatible=False` from any rule prunes the candidate from the allocation's list — no point scoring an entity that's hard-disqualified.
- **Score is the geometric mean** of the per-rule verdict scores. See [Soft-rules aggregation](../explanations/soft-rules-aggregation.md) for why geometric mean and not arithmetic mean or pure product.

Output: an updated `state.candidate_map` — fewer candidates per allocation, each with an aggregated score reflecting how well the surviving candidates fit.

### Stage 3 — `RunAlgorithmAndDispatchResults`

Calls `algorithm.run(allocations, entities, candidates, rules)` with the now-pruned candidate map. The algorithm consults stateful rules as it assigns; its return value is a `AssignmentState[TEntity, TAllocationRequest]` carrying the final list of `PlannedAllocation`s. That state is then passed to every configured output adapter via `handle_output(state)`.

## Customizing the pipeline

The default 3-stage pipeline is built when you instantiate `BeeKeeper(...)` without an explicit `stages` argument. Pass `stages=` to replace it entirely. See [Customize the pipeline](../how-to/customize-the-pipeline.md).
