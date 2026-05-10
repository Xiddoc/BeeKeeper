# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

BeeKeeper ("Manage the Bee-sy with ease.") is a Python 3.13 library for assigning **entities** (workers/resources) to **allocation requests** over date ranges, subject to a pluggable **rules** pipeline and a user-supplied **algorithm**. It is packaged as a library; there is no CLI entry point yet (the `[project.scripts]` block in `pyproject.toml` is commented out).

Dependencies are managed with **uv** (`uv.lock` is committed). Runtime dep is `pydantic>=2.11.5`. Dev tools: `mypy`, `ruff`, `pytest`, `pre-commit`. The `examples` dependency group adds `faker`.

## Common commands

```bash
uv sync                         # install/refresh the venv from uv.lock
uv sync --all-groups            # also install dev + examples groups
uv run ruff check               # lint
uv run ruff format              # format
uv run mypy src                 # strict type-check (examples/ excluded)
uv run pytest                   # run tests
uv run pytest tests/test_date_range.py::test_daterange_days_counts_full_span   # single test
uv run pre-commit install       # one-time: enable git hooks
uv run pre-commit run --all-files
```

CI (`.github/workflows/ci.yml`) runs ruff (lint + format check), mypy, and pytest on every push to `master` and every PR.

## Tooling configuration to be aware of

- **mypy** runs in `strict` mode with the `pydantic.mypy` plugin and `disallow_untyped_defs`. `examples/` is excluded; the rest of the codebase must type-check cleanly.
- **ruff** uses `select = ["ALL"]` (every rule) with a curated ignore list in `pyproject.toml`. Per-file relaxations live in `[tool.ruff.lint.per-file-ignores]` — `tests/**` skips `S101`/`ANN`/`PT011`/`SLF001`, `examples/**` skips `ANN`/`ARG`/`D`. New code in `src/` is expected to satisfy the full rule set.
- **pre-commit** wires up ruff (lint + format), mypy, the standard pre-commit-hooks bundle, and `astral-sh/uv-pre-commit` (which keeps `uv.lock` in sync).
- Python `3.13` is required and used (`.python-version`, `requires-python = ">=3.13"`). The codebase uses **PEP 695 type-parameter syntax** (e.g. `class Entity[TInavailability: Inavailability](BaseModel)`); `UP007` is ignored so `Optional[T]` is still accepted alongside `X | None`.
- Distribution is marked `Typing :: Typed` — `src/beekeeper/py.typed` (PEP 561) is shipped via `[tool.setuptools.package-data]`.

## Architecture

BeeKeeper is a **framework**: callers bring data (via input adapters), constraints (rules), and an assignment strategy (algorithm). The library wires the orchestration.

### Public surface

`src/beekeeper/__init__.py` re-exports the public API. Anything not in `__all__` is internal. Key exports today:

- Orchestrator: `BeeKeeper`
- Adapters: `InputAdapter`, `EntityInputAdapter`, `AllocationInputAdapter`, `MixedInputAdapter`, `OutputAdapter`
- Domain models: `Entity`, `AllocationRequest`, `PlannedAllocation`, `Inavailability`, `DateRange`, `AllocationType`

### Pydantic vs. plain classes — the convention

Use **pydantic `BaseModel`** for **data**: things that get validated, serialized, deserialized, or crossed across IO boundaries — `Entity`, `AllocationRequest`, `PlannedAllocation`, `Inavailability`, `DateRange`. Use **plain `@dataclass`** (or vanilla classes) for **services and runtime state**: things that hold dependencies or in-memory state, and whose fields can legitimately be ABCs — `MixedInputAdapter`, `BeeKeeperFlowState`, the flow-stage classes, `BeeKeeper` itself.

Why: pydantic introspects every field type to build a JSON-schema-style validator. ABC-typed fields fail that introspection unless you set `arbitrary_types_allowed=True`, which silently disables validation for those fields anyway — defeating pydantic's purpose. Dataclasses don't do runtime field-type introspection, so they accept ABC-typed fields without ceremony and still inherit cleanly from ABC bases. Keeping the data/service split sidesteps the conflict entirely.

### Internal imports

Inside `src/beekeeper/`, prefer **submodule imports** (`from beekeeper.entities.entity import Entity`) over **top-level package imports** (`from beekeeper import Entity`). The latter creates circular-init hazards: when a submodule imported partway through `beekeeper/__init__.py` reaches back into the still-loading top-level `beekeeper`, names declared further down in `__init__.py` aren't bound yet and the import explodes. Top-level imports are for end users, not for internal wiring.

### Adapter layer (`src/beekeeper/adapters/`)

- `EntityInputAdapter.get_entities() -> Iterable[Entity]` and `AllocationInputAdapter.get_allocations() -> Iterable[AllocationRequest]` — both are ABCs.
- `InputAdapter` is the multiple-inheritance union of the two; implement directly when one source provides both kinds of data.
- `MixedInputAdapter` composes two separate adapters into one (see import-time caveat above).
- `OutputAdapter.handle_output()` is the result sink (currently unparameterized).

A skeleton integration lives under `examples/mcdonalds/` (Excel-backed adapters, currently returning empty iterables). `examples/` is excluded from mypy.

### Domain model

- `Entity[TInavailability: Inavailability]` — pydantic `BaseModel`. Currently exposes only `inavailabilities`. Generic on the inavailability type via PEP 695 syntax. A module-level `TEntity = TypeVar("TEntity", bound=Entity)` is exported for downstream generics.
- `AllocationRequest` — pydantic `BaseModel`, `Generic[TAllocationType, TEntity]`. Fields: `allocation_type`, `date_range`, `requested_entity`. A `TAllocationRequest` TypeVar is exported alongside.
- `PlannedAllocation` extends `AllocationRequest` with the assigned `Entity`.
- `Inavailability` is a `DateRange` subclass (a period an entity is unavailable).
- `DateRange` is a pydantic `BaseModel` with `start_date`, `end_date`, and a `days` property that counts **inclusively** — same-day range = 1 day.
- `AllocationType` is an empty `AbstractEnum` subclass; consumers extend it with their domain's vocabulary.

### `AbstractEnum` pattern (`src/beekeeper/data_structures/abstract_enum.py`)

`AbstractEnum` is an `Enum` whose metaclass also mixes in `ABCMeta`, letting subclasses act as both enum *and* abstract base. Today only `AllocationType` uses it, and it ships with no concrete members — applications subclass it (e.g. `class Shift(AllocationType): MORNING = ...`).

### Rules (`src/beekeeper/rules/`)

- `BaseRule` — empty marker base.
- `PreliminaryRule.is_compatible(entity, allocation) -> bool` — static, stateless compatibility checks (e.g. exemptions, qualifications). Run before the algorithm.
- `StatefulRule.is_compatible(entity, allocation, state) -> bool` — context-aware checks against the in-progress assignment `State` (e.g. consecutive-shift limits, cumulative hour caps). Consulted by the algorithm during assignment.

### Algorithm (`src/beekeeper/algorithm/`)

- `BaseAlgorithm[TEntity, TAllocationType]` — abstract. Implement `run(allocations, entities, rules) -> State` with your assignment strategy. The `State` type lives in `algorithm_state.py`.

### Flow (`src/beekeeper/flow/`)

`BeeKeeper` (in `flow/beekeeper.py`) is the orchestrator. It pulls data through the input adapter into a `BeeKeeperFlowState` and runs three pipeline stages in order:

1. `AssignPossibleEntitiesToAllocations` — narrow each allocation to candidate entities.
2. `RunPreliminaryRules` — drop pairs that fail any `PreliminaryRule`.
3. `RunAlgorithmAndDispatchResults` — invoke the configured `BaseAlgorithm`, then push results through the output adapters.

Several flow stages are currently scaffolded (e.g. `assign_possible_entities_to_allocations.py`'s `run_stage` body is empty / a `pass`), and `mypy` reports ~20 type errors in this area today — expect this to be the active development frontier.
