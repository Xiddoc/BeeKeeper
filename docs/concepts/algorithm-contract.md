# The Algorithm Contract

Your algorithm is the meaty part of your scheduler. BeeKeeper handles ingestion, rule evaluation, and dispatch; your `BaseAlgorithm.run` decides who goes where.

## The signature

```python
class MyAlgorithm[TEntity: Entity[Any], TAllocReq: AllocationRequest[Any, Any]](
    BaseAlgorithm[TEntity, TAllocReq],
):
    def run(
        self,
        allocations: Iterable[TAllocReq],
        entities: Iterable[TEntity],
        candidates: Mapping[int, list[Candidate[TEntity]]],
        rules: Iterable[StatefulRule[TEntity, TAllocReq]],
    ) -> State[TEntity, TAllocReq]:
        ...
```

## What you get

- **`allocations`**: the raw allocation requests in input order. The same iterable the input adapter produced.
- **`entities`**: the raw entity list. Useful when an algorithm wants to consider entities outside the candidate map (rare).
- **`candidates`**: the pruned, scored candidate map from stage 2, keyed by `id(allocation)`. *This is what most algorithms iterate over.* Each `Candidate` carries an entity reference and an aggregated score.
- **`rules`**: the stateful rules. You're responsible for consulting these as you assign; the framework doesn't run them for you.

## What you must return

A `State[TEntity, TAllocReq]` carrying every successful assignment. Use `state.add_allocation(PlannedAllocation(request=..., assigned_entities=(...)))` to record an assignment. The state's `planned_allocations` property is what output adapters read.

## What you must guarantee

- **Honor the candidate map.** Don't assign an entity that's not in the candidate list for an allocation. The map represents the framework's pre-pruning of incompatibilities; bypassing it skips your domain's preliminary rules.
- **Honor `required_count`.** If an allocation needs N entities, assign exactly N or skip the allocation entirely. Don't half-fill.
- **Consult stateful rules.** Before adding a `PlannedAllocation`, every stateful rule must evaluate `compatible=True`. The framework does not double-check.

## What you may do (but don't have to)

- **Use the score.** `Candidate.score` is the geometric mean of the soft rules' verdicts. Highest-scored is the algorithm's hint of "best candidate." A simple greedy picks the top-scored. A constraint solver might use it as a heuristic.
- **Iterate allocations in any order.** Input order is one option. Most-constrained-first, by-date, by-priority — your call.
- **Skip allocations.** Allocations that can't be filled (empty candidate list, all candidates fail stateful rules) just don't get a `PlannedAllocation`. The output adapter can compute the diff if needed.
- **Use `state.get_allocations_done_by(entity)`** to look up an entity's existing assignments while deciding the next one — this is what stateful rules typically do.

## A reference implementation

[`GreedyAssignmentAlgorithm`](../how-to/write-an-algorithm.md#bundled-implementations) is a 30-line reference: for each allocation, sort candidates by descending score, pick the top compatible ones until `required_count` is met. It's not optimal — it doesn't backtrack, doesn't optimize globally, doesn't care about anything beyond "fill the count." But it lets every example in this docs site have a runnable algorithm without writing one from scratch, and it's a fine starting point to copy and adapt.

For nontrivial scheduling, the same `BaseAlgorithm` contract is implemented by `BacktrackingAssignmentAlgorithm`, `LoadBalancingAssignmentAlgorithm`, and `OrToolsAssignmentAlgorithm` — see the [bundled implementations table](../how-to/write-an-algorithm.md#bundled-implementations).
