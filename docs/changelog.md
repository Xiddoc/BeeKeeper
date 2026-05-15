# Changelog

## Unreleased

The 0.1.0 → 0.2.0 (forthcoming) refactor. Public API breaks called out at the top of each section.

### Type system

- **All framework classes are now PEP 695 generic.** `Entity[TUnavailability]`, `AllocationRequest[TAllocationType, TEntity]`, `Unavailability[T: date = datetime]`, `DateRange[T: date = datetime]`, plus every adapter, rule, algorithm, flow stage, and the `BeeKeeper` itself. Domain code parameterizes once at the call site (`BeeKeeper[McWorker, McRequest](...)`) and the types flow through the whole pipeline.
- **Module-level `TEntity` / `TAllocationType` / `TAllocationRequest` TypeVars are removed.** Each generic class declares its own.
- **Bound class:** `Entity[Any]` and `AllocationRequest[Any, Any]` are used as PEP 695 bounds (the inner `[Any]` accommodates mypy's `[type-arg]` rule on generic-class bounds). At call sites, parameterize concretely.

### `Assignment` (breaking)

Switched from inheritance to **composition**: `Assignment` now has `allocation: TAllocationRequest` and `assigned_entities: tuple[TEntity, ...]` rather than extending `AllocationRequest`. `planned.allocation_type` becomes `planned.allocation.allocation_type`. Also switched from pydantic `BaseModel` to a frozen `@dataclass`.

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
- `StatefulRule.is_compatible(entity, allocation: Assignment, state)` is replaced by `StatefulRule.evaluate(entity, allocation: TAllocationRequest, state)`. The rule receives the allocation being considered, not an already-planned allocation.

### Multi-entity allocations

- `AllocationRequest.requested_entity: TEntity | None` becomes `requested_entities: tuple[TEntity, ...]` with `required_count: int = 1`.

### Flow stages

- `AssignPossibleEntitiesToAllocations` and `RunPreliminaryRules` are no longer stubs. Stage 1 builds a candidate map keyed by `id(allocation)`; stage 2 prunes hard-rule failures and aggregates soft scores via geometric mean.
- `BeeKeeperFlowState` carries `candidate_map: dict[int, list[Candidate[TEntity]]]`.
- `Algorithm.run` signature widens: `candidates` and the now-correct `Iterable[TAllocationRequest]` for allocations.

### JSON adapters

- `JsonEntityInputAdapter` and `JsonAllocationInputAdapter` graduate to core (`beekeeper.adapters.inputs.json_*`). Strict-only — `extra="forbid"` is now set on the framework's `BaseModel` base classes; subclasses inherit. No leniency knob is exposed; users who want lenient parsing implement their own adapter.

### Built-ins

New: `AvailabilityRule`, `RequestedEntityRule`, `GreedyAssignmentAlgorithm`, `ConsoleOutputAdapter`. Available under `beekeeper.rules.builtins`, `beekeeper.algorithm.implementations.greedy`, `beekeeper.adapters.outputs.console`.

### McDonald's example

Now runs end-to-end: `python -m mcdonalds.main mcdonalds/workers.json mcdonalds/allocations.json` prints three planned allocations. JSON fixtures replaced the hand-rolled faker adapter; `allowed_ranks` field added; `McRankRule` added. Integration test in `tests/test_mcdonalds_example.py`.

### Docs

A full mkdocs-material site under `docs/`, built locally via `uv run mkdocs serve` and deployed to GitHub Pages on push to `master` via `.github/workflows/docs.yml`.

**One-time setup**: enable Pages on the repo under *Settings → Pages → Build and deployment → Source: GitHub Actions*. Until that's done, the docs workflow will fail at the deploy step (the build step will still pass).

### Algorithm implementations

The reference algorithms move under a new `beekeeper.algorithm.implementations.*` subpackage to make room for additional implementations and to keep the top-level `beekeeper.algorithm.` namespace for the abstract bases.

* `beekeeper.algorithm.implementations.greedy.GreedyAssignmentAlgorithm` — baseline (was previously at `beekeeper.algorithm.greedy`).
* `beekeeper.algorithm.implementations.backtracking.BacktrackingAssignmentAlgorithm` — depth-first search that finds complete solutions where greedy gets stuck.
* `beekeeper.algorithm.implementations.load_balancing.LoadBalancingAssignmentAlgorithm` — greedy with a per-entity load penalty so work disperses across the pool.
* `beekeeper.algorithm.implementations.or_tools.OrToolsAssignmentAlgorithm` — Google OR-Tools CP-SAT-backed global optimizer. Optional dep: `pip install 'beekeeper[ortools]'` or `uv sync --extra ortools`.

### AssignmentState indexing (perf, internal)

`AssignmentState` now maintains a per-entity index alongside the flat allocation list, making `get_assignments_done_by(entity)` O(k) instead of O(n). Stateful rules and load-balancing both benefit; `LoadBalancingAssignmentAlgorithm` dropped its workaround side-dict.

### Oversubscribed benchmark fixtures

Three new fixtures under `examples/mcdonalds/` exercise the worker-scarce regime — many more allocations than workers, every allocation `required_count=1`. Generated by the same script as the worker-rich fixtures (regenerate with `cd examples && uv run python -m mcdonalds.scripts.generate_large_fixtures`):

* `workers_oversub_3x.json` / `allocations_oversub_3x.json` — 50 workers, 150 allocations (3:1).
* `workers_oversub_6x.json` / `allocations_oversub_6x.json` — 50 workers, 300 allocations (6:1).
* `workers_oversub_10x.json` / `allocations_oversub_10x.json` — 50 workers, 500 allocations (10:1).

Benchmark suite parametrization extends to `4 algorithms × 6 fixture sizes = 24 cases`. The oversubscribed fixtures expose load-distribution behavior — under 10x oversubscription every worker who isn't rank-locked-out absorbs multiple allocations.

### `GreedyAssignmentAlgorithm` removed (breaking)

The greedy reference algorithm is deleted. `LoadBalancingAssignmentAlgorithm` is now the default reference — it does the same work but with a `score / (1 + load)` penalty so assignments disperse across the entity pool instead of concentrating on the highest-scored handful.

The two algorithms had identical wall-clock performance on every fixture (the AssignmentState per-entity index made the load lookup O(1)), and load-balancing's distribution properties on the oversubscribed fixtures were dramatically better (Gini ~0.13 vs ~0.97 on `oversub_10x`). Keeping a strictly worse algorithm as a footgun wasn't worth the API surface.

Callers using `beekeeper.algorithm.implementations.greedy.GreedyAssignmentAlgorithm` should switch to `beekeeper.algorithm.implementations.load_balancing.LoadBalancingAssignmentAlgorithm`. The constructor signature is identical.

### Algorithm chain (breaking)

`BeeKeeper(algorithm=...)` now accepts either a single algorithm or a sequence to try in order. When an algorithm raises `IncompleteSolutionError`, the next one in the sequence runs from scratch.

```python
BeeKeeper[McWorker, McRequest](
    algorithm=[BacktrackingAssignmentAlgorithm(), GreedyAssignmentAlgorithm()],
    ...
)
```

`BacktrackingAssignmentAlgorithm` and `OrToolsAssignmentAlgorithm` raise `IncompleteSolutionError` instead of silently falling back / silently returning empty. Greedy and load-balancing never raise. Putting one of them last in the chain guarantees a result.

The previously-bundled hardcoded backtracking → greedy fallback is removed in favor of the explicit chain.

### `Inavailability` → `Unavailability` (breaking)

The `Inavailability` class — which wasn't a real English word — is renamed to `Unavailability` throughout. The module also moves from `beekeeper.inavailabilities.inavailability` to `beekeeper.unavailabilities.unavailability`, and the `Entity.inavailabilities` field is renamed to `Entity.unavailabilities`. The type parameter on `Entity` follows suit: `Entity[TUnavailability: Unavailability[Any]]`.

Callers must update:

- the import (`from beekeeper import Unavailability`),
- subclass declarations (`class MyUnavailability(Unavailability): ...`),
- the field name on `Entity` subclasses (`unavailabilities: list[...]`),
- and the JSON key in any persisted entity payloads (`"unavailabilities"`).

No backwards-compatibility alias is shipped — this is an alpha (v0.1.0), and the misspelling is the whole reason for the rename.

### API renames (breaking)

A coherent batch of renames that drop awkward prefixes, replace overloaded vocabulary, and surface the public abstract bases consistently:

- `BaseAlgorithm` → `Algorithm`. The `Base` prefix was the only one on a public abstract base; every sibling (`PreliminaryRule`, `StatefulRule`, `EntityInputAdapter`, …) uses the bare name. The class also now inherits from `abc.ABC`, so `@abstractmethod` is actually enforced (previously the decorator was silently ignored and instantiation crashed downstream).
- `State` → `AssignmentState`. The bare name was generic to the point of unhelpful at call sites (`state: State[...]` doesn't say what kind of state).
- `MixedInputAdapter` → `CompositeInputAdapter`. "Mixed" suggested mixed contents; the class actually composes two sub-adapters.
- `PlannedAllocation` → `Assignment`. Resolves a three-way overload of "allocation" in the codebase (`AllocationRequest`, planned result, verb). The field rename `Assignment.request` → `Assignment.allocation` follows from the new name. `AssignmentState` method/attribute renames for symmetry: `add_allocation` → `add_assignment`, `remove_allocation` → `remove_assignment`, `planned_allocations` → `assignments`, `get_allocations_done_by` → `get_assignments_done_by`.

Module files renamed via `git mv` so blame history is preserved:

- `beekeeper.algorithm.base_algorithm` → `beekeeper.algorithm.algorithm`
- `beekeeper.adapters.inputs.mixed_input_adapter` → `beekeeper.adapters.inputs.composite_input_adapter`
- `beekeeper.allocations.planned_allocation` → `beekeeper.allocations.assignment`

### Top-level re-exports

The canonical concrete implementations now re-export from the package root, matching the way users actually want to import them:

- `LoadBalancingAssignmentAlgorithm`, `BacktrackingAssignmentAlgorithm`, `OrToolsAssignmentAlgorithm` (was: `from beekeeper.algorithm.implementations.* import …`)
- `AvailabilityRule`, `RequestedEntityRule` (was: `from beekeeper.rules.builtins import …`)
- `ConsoleOutputAdapter` (was: `from beekeeper.adapters.outputs.console import …`)
- `AbstractEnum` (was: `from beekeeper.data_structures.abstract_enum import …`)

The submodule paths still work, so existing imports don't break. The top-level paths are the recommended way going forward.

### API ergonomics

A batch of additive type-system + observability tweaks. Nothing in this section breaks existing call sites.

- **`AnyEntity` / `AnyRequest` type aliases.** PEP 695 `type` statements re-exported from the top level: `type AnyEntity = Entity[Any]`, `type AnyRequest = AllocationRequest[Any, Any, Any]`. Use as `[TEntity: AnyEntity, TRequest: AnyRequest]` instead of the verbose `[TEntity: Entity[Any], TRequest: AllocationRequest[Any, Any, Any]]` boilerplate.
- **`IncompleteSolutionError` is now generic.** Parameterized over the same TypeVars as the algorithm that raises it (`IncompleteSolutionError[TEntity, TAllocationRequest]`). `partial_state` is typed `AssignmentState[TEntity, TAllocationRequest] | None` instead of `Any`, so callers who catch and inspect the partial state get type-checked field access.
- **`BeeKeeper.__init__` has `@overload` signatures.** Two valid call shapes are now distinguished at the type-checker level: `algorithm=` required (default pipeline) vs. `stages=` required (custom pipeline). The previous single-signature version typechecked `BeeKeeper(input_adapter=...)` cleanly and then raised at runtime; the overloads catch that mistake statically.
- **`output_adapters` is now `Sequence[OutputAdapter[...]]`** (was `Iterable[...]`). Tightens the type so mypy rejects singleton mistakes and one-shot iterators at the call site.
- **Algorithm chain observability: `on_incomplete_solution=` callback.** Receives `(algorithm, exception)` once per fall-through event in the chain. Useful for production telemetry when a primary algorithm silently degrades to its fallback. Default `None` (no-op).
- **`AllocationRequest` has a third TypeVar `TDate: date = datetime`.** The contained `date_range: DateRange[TDate]` follows. Existing call sites are unchanged thanks to the PEP 696 default; domains that want whole-day allocations can parameterize as `AllocationRequest[MyType, MyEntity, date]`.
