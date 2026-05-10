# Changelog

## Unreleased

The 0.1.0 → 0.2.0 (forthcoming) refactor. Public API breaks called out at the top of each section.

### Type system

- **All framework classes are now PEP 695 generic.** `Entity[TInavailability]`, `AllocationRequest[TAllocationType, TEntity]`, `Inavailability[T: date = datetime]`, `DateRange[T: date = datetime]`, plus every adapter, rule, algorithm, flow stage, and the `BeeKeeper` itself. Domain code parameterizes once at the call site (`BeeKeeper[McWorker, McRequest](...)`) and the types flow through the whole pipeline.
- **Module-level `TEntity` / `TAllocationType` / `TAllocationRequest` TypeVars are removed.** Each generic class declares its own.
- **Bound class:** `Entity[Any]` and `AllocationRequest[Any, Any]` are used as PEP 695 bounds (the inner `[Any]` accommodates mypy's `[type-arg]` rule on generic-class bounds). At call sites, parameterize concretely.

### `PlannedAllocation` (breaking)

Switched from inheritance to **composition**: `PlannedAllocation` now has `request: TAllocationRequest` and `assigned_entities: tuple[TEntity, ...]` rather than extending `AllocationRequest`. `planned.allocation_type` becomes `planned.request.allocation_type`. Also switched from pydantic `BaseModel` to a frozen `@dataclass`.

### `BeeKeeper` constructor (breaking)

- `rules: Iterable[BaseRule]` is replaced by separate `preliminary_rules` and `stateful_rules` kwargs. `BaseRule` is removed.
- `output_adapters` defaults to `()`; passing `None` no longer works.
- New optional `stages=` kwarg. When omitted, the default 3-stage pipeline is built. When supplied, the user owns wiring.
- `algorithm` is now optional when `stages=` is supplied.

### `DateRange` (breaking on `.days`)

- Generic over `T: date = datetime`. Default behavior unchanged for existing call sites.
- Validators added: `end_date >= start_date`, tz-consistency for datetimes.
- `.days` now matches stdlib (`(end - start).days`, exclusive). The previous inclusive semantics moved to `.inclusive_day_count`.

### Rules (breaking)

- `evaluate(...) -> RuleVerdict` is the new abstract method on `PreliminaryRule` / `StatefulRule`.
- New convenience subclasses: `HardPreliminaryRule`, `SoftPreliminaryRule`, `HardStatefulRule`, `SoftStatefulRule`. Each wraps a single-method API (`check` for hard, `score` for soft).
- `StatefulRule.is_compatible(entity, allocation: PlannedAllocation, state)` is replaced by `StatefulRule.evaluate(entity, allocation: TAllocationRequest, state)`. The rule receives the request being considered, not an already-planned allocation.

### Multi-entity allocations

- `AllocationRequest.requested_entity: TEntity | None` becomes `requested_entities: tuple[TEntity, ...]` with `required_count: int = 1`.

### Flow stages

- `AssignPossibleEntitiesToAllocations` and `RunPreliminaryRules` are no longer stubs. Stage 1 builds a candidate map keyed by `id(allocation)`; stage 2 prunes hard-rule failures and aggregates soft scores via geometric mean.
- `BeeKeeperFlowState` carries `candidate_map: dict[int, list[Candidate[TEntity]]]`.
- `BaseAlgorithm.run` signature widens: `candidates` and the now-correct `Iterable[TAllocationRequest]` for allocations.

### JSON adapters

- `JsonEntityInputAdapter` and `JsonAllocationInputAdapter` graduate to core (`beekeeper.adapters.inputs.json_*`). Strict-only — `extra="forbid"` is now set on the framework's `BaseModel` base classes; subclasses inherit. No leniency knob is exposed; users who want lenient parsing implement their own adapter.

### Built-ins

New: `AvailabilityRule`, `RequestedEntityRule`, `GreedyAssignmentAlgorithm`, `ConsoleOutputAdapter`. Available under `beekeeper.rules.builtins`, `beekeeper.algorithm.greedy`, `beekeeper.adapters.outputs.console`.

### McDonald's example

Now runs end-to-end: `python -m mcdonalds.main mcdonalds/workers.json mcdonalds/allocations.json` prints three planned allocations. JSON fixtures replaced the hand-rolled faker adapter; `allowed_ranks` field added; `McRankRule` added. Integration test in `tests/test_mcdonalds_example.py`.
