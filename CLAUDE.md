# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

BeeKeeper ("Manage the Bee-sy with ease.") is a Python 3.13+ framework for assigning **entities** (workers, vehicles, anything assignable) to **allocation requests** over date ranges, subject to a **rules pipeline** and a **user-supplied algorithm**. Domain code parameterizes once at the call site (`BeeKeeper[McWorker, McRequest](...)`) and the types flow through every adapter, rule, algorithm, and stage via PEP 695 generics.

Dependencies are managed with **uv** (`uv.lock` is committed). Runtime: `pydantic>=2.11.5`. Optional: `ortools` (gated behind `[project.optional-dependencies].ortools`). Dev: `mypy`, `ruff`, `pytest`, `pytest-benchmark`, `pre-commit`, `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`, plus `ortools` so CI exercises the optional algorithm. The `examples` group adds `faker` (used by the fixture generator script).

## Common commands

```bash
uv sync                                # install/refresh the venv from uv.lock
uv sync --all-groups                   # also install dev + examples groups
uv sync --extra ortools                # add the OR-Tools optional extra
uv run ruff check                      # lint
uv run ruff format                     # format
uv run mypy src                        # strict type-check (examples/ excluded)
uv run pytest                          # run unit + integration tests (benchmarks skipped)
uv run pytest --benchmark-only         # run only the perf benchmarks
uv run mkdocs serve                    # local docs preview at 127.0.0.1:8000
uv run mkdocs build --strict           # build docs (CI runs this too)
uv run pre-commit install              # one-time: enable git hooks
uv run pre-commit run --all-files
```

CI runs ruff lint + format check, mypy, pytest, pytest-benchmark, and `mkdocs build --strict` on every push to `master` and every PR (`.github/workflows/ci.yml`). A separate `docs.yml` workflow deploys the built site to GitHub Pages on every push to master.

## Git workflow

`master` is the project's default branch. Branch protection has been removed; direct fast-forward pushes from feature branches are permitted, and the project's preferred merge style is **fast-forward only** (no squash merges, no merge commits) so the per-commit history stays intact on master.

**When merging a feature branch locally instead of via a GitHub PR, delete both the local and the remote branch immediately after merging.** GitHub's "Automatically delete head branches" setting only fires for PR-based merges; direct-merge branches accumulate as orphans on origin until cleaned up. The full pattern:

```bash
git checkout master
git merge --ff-only feature/whatever
git push origin master
git push origin --delete feature/whatever   # only if the branch was pushed to origin
git branch -d feature/whatever              # local cleanup
```

If the feature branch was never pushed to origin (purely local work), skip the `push --delete` line. `git branch -d` (lowercase d) refuses to delete an unmerged branch — if it errors, that's a signal to investigate, not to use `-D`.

## Tooling configuration to be aware of

- **mypy** runs in `strict` mode with the `pydantic.mypy` plugin and `disallow_untyped_defs`. `examples/` is excluded; `src/` and `tests/` must type-check cleanly.
- **ruff** uses `select = ["ALL"]` with a curated ignore list in `pyproject.toml`. Per-file relaxations: `tests/**` skips `S101`/`ANN`/`ARG`/`PT011`/`SLF001`; `examples/**` skips `ANN`/`ARG`/`D`/`DTZ001`. New code in `src/` is expected to satisfy the full rule set out of the box. `[tool.ruff.lint.pylint] max-args = 8` so `BeeKeeper.__init__`'s six kwargs don't trip PLR0913.
- **pre-commit** wires up ruff (lint + format), mypy, the standard pre-commit-hooks bundle, and `astral-sh/uv-pre-commit` (which keeps `uv.lock` in sync).
- **Python 3.13+** required (`.python-version`, `requires-python = ">=3.13"`). The codebase uses **PEP 695 type-parameter syntax** end-to-end (e.g. `class Entity[TUnavailability: Unavailability[Any]](BaseModel)`).
- **PEP 696 defaults** on `DateRange[T: date = datetime]` and `Unavailability[T: date = datetime]` — bare instantiation defaults to datetime.
- Distribution is marked `Typing :: Typed`; `src/beekeeper/py.typed` (PEP 561) is shipped via `[tool.setuptools.package-data]`.

## Architecture

BeeKeeper is a **framework**: callers bring data (via input adapters), constraints (rules), and an assignment strategy (algorithm). The library wires the orchestration through a 3-stage pipeline.

### Public surface

`src/beekeeper/__init__.py` re-exports everything in `__all__`. Anything not in `__all__` is internal. Today's exports:

- **Orchestrator**: `BeeKeeper`, `IncompleteSolutionError`
- **Adapters**: `InputAdapter`, `EntityInputAdapter`, `AllocationInputAdapter`, `MixedInputAdapter`, `JsonEntityInputAdapter`, `JsonAllocationInputAdapter`, `OutputAdapter`
- **Domain models**: `Entity`, `AllocationRequest`, `PlannedAllocation`, `Unavailability`, `DateRange`, `AllocationType`
- **Rules**: `PreliminaryRule`, `HardPreliminaryRule`, `SoftPreliminaryRule`, `StatefulRule`, `HardStatefulRule`, `SoftStatefulRule`, `RuleVerdict`
- **Algorithm primitives**: `Algorithm`, `AssignmentState`

Concrete algorithm implementations and the built-in rules / output adapter live in submodules (not re-exported from the top-level), under `beekeeper.algorithm.implementations.*`, `beekeeper.rules.builtins`, and `beekeeper.adapters.outputs.*`.

### Pydantic vs. plain classes — the convention

Use **pydantic `BaseModel`** for **data**: things that get validated, serialized, deserialized, or crossed across IO boundaries — `Entity`, `AllocationRequest`, `Unavailability`, `DateRange`. Each of these sets `model_config = ConfigDict(extra="forbid")`, which subclasses inherit, so unknown fields in JSON inputs fail loudly.

Use **plain `@dataclass`** (or vanilla classes) for **services and runtime state**: `MixedInputAdapter`, `JsonEntityInputAdapter`, `JsonAllocationInputAdapter`, `BeeKeeperFlowState`, `Candidate`, `PlannedAllocation`, the flow-stage classes, `BeeKeeper` itself.

**Why**: pydantic introspects every field type to build a JSON-schema validator. ABC-typed fields fail that introspection unless you set `arbitrary_types_allowed=True`, which silently disables validation for those fields anyway — defeating pydantic's purpose. Dataclasses don't introspect at runtime, so they accept ABC-typed fields without ceremony and still inherit cleanly from ABC bases. `PlannedAllocation` is also a dataclass for a different reason: with PEP 695 generics, pydantic's bound-resolution rejects subclass-only fields on tuple elements when the class is constructed without explicit parameterization (see commit `bfb8cfb` for context).

### Internal imports

Inside `src/beekeeper/`, prefer **submodule imports** (`from beekeeper.entities.entity import Entity`) over **top-level package imports** (`from beekeeper import Entity`). The latter creates circular-init hazards: when a submodule imported partway through `beekeeper/__init__.py` reaches back into the still-loading top-level `beekeeper`, names declared further down in `__init__.py` aren't bound yet and the import explodes. Top-level imports are for end users, not for internal wiring.

### The `Entity[Any]` bound pattern

Generic classes that take a generic class as a TypeVar bound write the bound with an `[Any]` slot:

```python
class AssignmentState[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]: ...
```

Without the `[Any]`, mypy's `[type-arg]` rule fires on the bound (because `Entity` is itself generic). The `[Any]` accepts any parameterization of `Entity` as a valid bound. At call sites, parameterize concretely (`BeeKeeper[McWorker, McRequest](...)`); the `[Any]` is purely a syntactic accommodation in bound positions.

### Domain model

- **`Entity[TUnavailability: Unavailability[Any]]`** — pydantic `BaseModel`. One field: `unavailabilities: list[TUnavailability]`. The type parameter actually flows through (subclasses see their concrete `Unavailability` subtype).
- **`Unavailability[T: date = datetime]`** — pydantic `BaseModel` extending `DateRange[T]`. Adds `reason: str`. PEP 696 default (`datetime`) keeps the common path frictionless.
- **`DateRange[T: date = datetime]`** — pydantic `BaseModel` with `start_date: T`, `end_date: T`. Validators reject `end < start` and require tz-consistency on datetimes. Two day-count properties: `inclusive_day_count` (same-day → 1, the "active days on duty" reading) and `days` (matches stdlib `(end - start).days`, exclusive).
- **`AllocationType`** — empty `AbstractEnum` subclass; consumers extend with their domain's vocabulary (e.g. `class McAllocType(AllocationType): COOKING = "COOKING"`). String-valued enums recommended over `auto()` so JSON fixtures stay human-readable.
- **`AllocationRequest[TAllocationType: AllocationType, TEntity: Entity[Any]]`** — pydantic `BaseModel`. Fields: `allocation_type: TAllocationType`, `date_range: DateRange[datetime]`, `required_count: int = 1`, `requested_entities: tuple[TEntity, ...] = ()`.
- **`PlannedAllocation[TAllocationRequest, TEntity]`** — frozen `@dataclass` (composition, not inheritance). Fields: `request: TAllocationRequest`, `assigned_entities: tuple[TEntity, ...]`. Callers access `planned.request.allocation_type`, not `planned.allocation_type`.

### `AbstractEnum` pattern (`src/beekeeper/data_structures/abstract_enum.py`)

`AbstractEnum` is an `Enum` whose metaclass also mixes in `ABCMeta`, letting subclasses act as both enum *and* abstract base. Today only `AllocationType` uses it — applications subclass with their concrete members.

### Rules (`src/beekeeper/rules/`)

- **`PreliminaryRule[TEntity, TAllocationRequest]`** and **`StatefulRule[TEntity, TAllocationRequest]`** — abstract bases. Single abstract method `evaluate(...) -> RuleVerdict`. Preliminary rules run before the algorithm with no state; stateful rules run during assignment with the in-progress `AssignmentState`.
- **`RuleVerdict`** — frozen dataclass with `compatible: bool, score: float = 1.0`. A failing `compatible` prunes the candidate; the score contributes to the per-candidate aggregate.
- **`HardPreliminaryRule` / `HardStatefulRule`** — convenience subclasses wrapping `check(...) -> bool`. The verdict's score stays at 1.0 (neutral).
- **`SoftPreliminaryRule` / `SoftStatefulRule`** — convenience subclasses wrapping `score(...) -> float`. The verdict's compatible stays True.
- **Built-ins** in `beekeeper.rules.builtins`: `AvailabilityRule` (rejects entity if any unavailability overlaps the allocation), `RequestedEntityRule` (drops entities not in `allocation.requested_entities` when non-empty). Not re-exported from the top-level — domains import them explicitly.

### Algorithm (`src/beekeeper/algorithm/`)

- **`Algorithm[TEntity, TAllocationRequest]`** — abstract. The `run(allocations, entities, candidates, rules) -> AssignmentState` signature receives the full allocations and entities iterables, the **candidate map** (pruned by stage 2), and the stateful rules.
- **`AssignmentState[TEntity, TAllocationRequest]`** — accumulator for `PlannedAllocation`s. Maintains a per-entity index alongside the flat list, so `get_allocations_done_by(entity)` is O(k) where k is that entity's count. Stateful rules and load-balancing both rely on this.
- **`IncompleteSolutionError`** (in `beekeeper.algorithm.errors`) — raised by an algorithm that can't produce what it considers a complete solution. The flow stage catches it and falls through to the next algorithm in the chain.

#### Bundled implementations (`beekeeper.algorithm.implementations.*`)

| Module | Class | Behavior |
| --- | --- | --- |
| `load_balancing` | `LoadBalancingAssignmentAlgorithm` | Default reference. Highest-scored compatible candidates per allocation, weighted by `score / (1 + load)` so entities with prior assignments are scored down and work disperses across the pool. Never raises. |
| `backtracking` | `BacktrackingAssignmentAlgorithm` | Depth-first search over top-K candidates per allocation. Feasibility filter + iteration cap (default 1M). Raises `IncompleteSolutionError` on failure. |
| `or_tools` | `OrToolsAssignmentAlgorithm` | CP-SAT solver via Google OR-Tools. Time-cap'd (default 500 ms). Optional dep — installing the `ortools` extra is required. Raises `IncompleteSolutionError` on `INFEASIBLE` / `MODEL_INVALID`. |

#### The algorithm chain

`BeeKeeper(algorithm=...)` accepts either a single `Algorithm` or a `Sequence[Algorithm]`. The flow stage tries each in order, catches `IncompleteSolutionError`, falls through. The first non-raising algorithm wins. If all raise, the last error reaches the caller.

```python
BeeKeeper[McWorker, McRequest](
    algorithm=[
        BacktrackingAssignmentAlgorithm(),
        LoadBalancingAssignmentAlgorithm(),  # always succeeds, ends the chain
    ],
    ...
)
```

Putting load-balancing last guarantees the chain produces a result (it never raises).

### Flow (`src/beekeeper/flow/`)

`BeeKeeper.execute()` materializes the input adapter's iterables once and then passes a `BeeKeeperFlowState` through three stages:

1. **`AssignPossibleEntitiesToAllocations`** — for each allocation, walks the entity list and includes the entity unless the allocation specifies `requested_entities` and this entity isn't in the set, or the entity has an unavailability that fully covers the allocation's date range. Partial overlaps pass through. Output: `state.candidate_map: dict[int, list[Candidate[TEntity]]]` keyed by `id(allocation)`.
2. **`RunPreliminaryRules`** — for each (allocation, candidate) pair, evaluates every preliminary rule. Hard-rule failures prune the candidate; surviving candidates' scores become the geometric mean of per-rule scores.
3. **`RunAlgorithmAndDispatchResults`** — walks the algorithm chain and dispatches the resulting `AssignmentState` to every configured `OutputAdapter`.

The pipeline is pluggable: pass `stages=[...]` to `BeeKeeper.__init__` to replace the default 3-stage sequence entirely. When supplying `stages=`, the user owns the wiring and `algorithm`/`output_adapters` become optional.

### Stress fixtures and benchmarks

`examples/mcdonalds/` ships six fixture sizes generated by `examples/mcdonalds/scripts/generate_large_fixtures.py` (deterministic for a fixed seed):

**Worker-rich** (more workers than allocations, mixed `required_count`):

- `workers_large.json` / `allocations_large.json` — 65 workers, 25 allocations
- `workers_xlarge.json` / `allocations_xlarge.json` — 100 workers, 40 allocations
- `workers_xxlarge.json` / `allocations_xxlarge.json` — 200 workers, 80 allocations

**Worker-scarce / oversubscribed** (allocations >> workers, every allocation `n=1`):

- `workers_oversub_3x.json` / `allocations_oversub_3x.json` — 50 workers, 150 allocations (3:1)
- `workers_oversub_6x.json` / `allocations_oversub_6x.json` — 50 workers, 300 allocations (6:1)
- `workers_oversub_10x.json` / `allocations_oversub_10x.json` — 50 workers, 500 allocations (10:1)

The oversubscribed fixtures stress workload distribution: every worker who isn't rank-locked-out picks up multiple allocations. Used to validate that `LoadBalancingAssignmentAlgorithm` actually spreads work and that no algorithm chokes on the larger candidate pools.

`tests/benchmarks/test_algorithm_benchmarks.py` runs each algorithm × each fixture (3 × 6 = 18 parametrized cases). Two budgets: warning at 500 ms (emits a `UserWarning`, doesn't fail), hard ceiling at 1 s (fails). On a developer laptop:

| | large 65/25 | xlarge 100/40 | xxlarge 200/80 | oversub_3x 50/150 | oversub_6x 50/300 | oversub_10x 50/500 |
| --- | --- | --- | --- | --- | --- | --- |
| load_balancing | ~8 ms | ~19 ms | ~72 ms | ~39 ms | ~74 ms | ~120 ms |
| backtracking | ~9 ms | ~19 ms | ~81 ms | ~36 ms | ~91 ms | ~120 ms |
| or_tools | ~55 ms | ~470 ms (warn) | ~700 ms (warn) | ~190 ms | ~400 ms | ~670 ms (warn) |

OR-Tools is order-of-magnitude slower because of its model-build + solver-init costs. Warnings on the larger sizes are expected.

`tests/test_workload_distribution.py` is a separate suite that asserts `LoadBalancingAssignmentAlgorithm` achieves its distribution goals on the oversubscribed fixtures: every allocation filled, no eligible worker idle, Gini coefficient below 0.30, no worker carrying more than 3× the mean load.

### Documentation site

`docs/` contains the source for an mkdocs-material site at https://xiddoc.github.io/BeeKeeper/. Layout: `concepts/`, `how-to/`, `examples/`, `explanations/`, plus `index.md`, `reference.md` (mkdocstrings auto-generated from class docstrings), `contributing.md`, `changelog.md`. Build with `uv run mkdocs build --strict`; serve locally with `uv run mkdocs serve`. The docs deploy on every push to master via `.github/workflows/docs.yml`.

When you add a public class, write at minimum a one-line docstring — `reference.md` is auto-built from those, so a missing docstring shows up as an empty section.

### McDonald's example (`examples/mcdonalds/`)

A complete worked integration. Runs end-to-end:

```bash
cd examples/
uv run python -m mcdonalds.main mcdonalds/workers.json mcdonalds/allocations.json
```

Domain code: `McWorker(Entity[McDonaldsUnavailability])`, `McDonaldsAllocationRequest(AllocationRequest[McDonaldsAllocationType, McWorker])` with an `allowed_ranks: frozenset[McJobPosition]` field, `McRankRule(HardPreliminaryRule[...])`. Inputs come from JSON via `JsonEntityInputAdapter` / `JsonAllocationInputAdapter`. The default pipeline (load-balancing algorithm, three preliminary rules, console output) prints three planned allocations to stdout.

The example is **not installable**. Tests that import from it (`tests/test_mcdonalds_example.py`, `tests/benchmarks/*`) prepend `examples/` to `sys.path` at module load, with a `# noqa: E402` on the `mcdonalds.*` imports that follow.
