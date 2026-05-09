# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Beekeeper ("Manage the Bee-sy with ease.") is a Python 3.13 library for assigning entities (people/resources) to allocation requests over date ranges, given constraints like rank, location, exemptions, and inavailabilities. It is packaged as a library; there is no CLI entry point yet (the `[project.scripts]` block in `pyproject.toml` is commented out).

Dependencies are managed with **uv** (`uv.lock` is committed). Runtime dep is `pydantic>=2.11.1`; dev deps are `mypy` and `ruff`.

## Common commands

```bash
uv sync                       # install/refresh the venv from uv.lock
uv run mypy src               # strict type-check (examples/ is excluded)
uv run ruff check             # lint
uv run ruff format            # format
```

There is **no test suite** in this repo yet — no `tests/` directory and no test runner configured.

## Tooling configuration to be aware of

- **mypy** runs in `strict` mode with the `pydantic.mypy` plugin and `disallow_untyped_defs`. `examples/` is excluded; the rest of the codebase must type-check cleanly.
- **ruff** uses `select = ["ALL"]` (every rule) with a small ignore list in `pyproject.toml`. New code is expected to satisfy the full rule set out of the box. Line length is 120; target is `py313`.
- Python `3.13` is required (`.python-version`, `requires-python = ">=3.13"`). Modern syntax like PEP 604 unions is fine; `UP007` (forced `X | Y`) is intentionally ignored, so `Optional[T]` is also accepted.

## Architecture

The library is built around an **adapter pattern**: callers integrate Beekeeper by implementing input/output adapters for their data source, then (eventually) running an allocation flow.

### Public surface

`beekeeper/__init__.py` re-exports the entire public API. Anything not in that `__all__` is internal. Key exports:

- Adapters: `InputAdapter`, `EntityInputAdapter`, `AllocationInputAdapter`, `MixedInputAdapter`, `OutputAdapter`
- Domain models: `Entity`, `AllocationRequest`, `PlannedAllocation`, `Inavailability`, `DateRange`
- Domain enums (abstract — see below): `AllocationType`, `Rank`, `Location`, `Exemption`

### Adapter layer (`src/beekeeper/adapters/`)

- `EntityInputAdapter.get_entities() -> Iterable[Entity]`
- `AllocationInputAdapter.get_allocations() -> Iterable[AllocationRequest]`
- `InputAdapter` is the **multiple-inheritance union** of the two — implement it when one source provides both. Use `MixedInputAdapter` (a dataclass that composes two separate adapters) when entities and allocations come from different sources.
- `OutputAdapter.handle_output()` is the (currently unparameterized) sink for results.

A worked example lives under `examples/mcdonalds/` showing concrete adapters (`ExcelEntityInputAdapter`, `ExcelAllocationInputAdapter`). Examples are intentionally excluded from mypy.

### Domain model (`src/beekeeper/entities/`, `allocations/`, `inavailabilities/`, `time_constructs/`)

- `Entity` (dataclass): a resource with `inavailabilities`, `exemptions`, and a `rank`.
- `AllocationRequest` (dataclass): a slot to fill — has `allocation_type`, `date_range`, `location`, `allowed_ranks`, `prohibited_exemptions`, and an optional pre-`requested_entity`.
- `PlannedAllocation` extends `AllocationRequest` with `assigned_entity` — represents the result of a successful allocation.
- `Inavailability` is a `DateRange` subclass (a period an entity is unavailable).
- `DateRange` is a **pydantic `BaseModel`** with `start_date`, `end_date`, and a `days` property that counts inclusively (same-day range = 1 day).

### `AbstractEnum` pattern (`src/beekeeper/data_structures/abstract_enum.py`)

`Rank`, `Location`, `Exemption`, and `AllocationType` are all empty subclasses of `AbstractEnum` (an `Enum` whose metaclass also mixes in `ABCMeta`). They are **deliberately empty** — consuming applications subclass them and supply their own concrete members for that domain. Do not add concrete enum members to the library itself; they belong in caller code or in `examples/`.

### Flow layer (`src/beekeeper/flow/`)

Currently a placeholder package with only `__init__.py`. The allocation/orchestration logic that consumes adapters and produces `PlannedAllocation`s has not been implemented yet — expect this to be the next major area of work.
