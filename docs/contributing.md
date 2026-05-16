# Contributing

Contributions welcome — bug reports, fixes, new built-ins, docs improvements, additional examples for novel domains.

## Setup

```bash
git clone https://github.com/Xiddoc/BeeKeeper.git
cd BeeKeeper
uv sync --all-groups
uv run pre-commit install
```

## The quality gates

Every commit must pass:

```bash
uv run ruff check               # lint
uv run ruff format --check      # format
uv run mypy src                 # strict type-check (examples/ excluded)
uv run pytest                   # unit + integration tests
uv run mkdocs build --strict    # docs build cleanly with no broken links
```

CI runs all of these on every push and pull request.

## House style

- **Python 3.13+ only.** Use PEP 695 generics, PEP 696 defaults, `match` statements freely.
- **mypy strict.** No `Any` returns, all public functions annotated. Use the `AnyEntity` / `AnyRequest` type aliases for TypeVar bounds (they wrap the verbose `Entity[Any]` / `AllocationRequest[Any, Any, Any]` form). Call sites parameterize concretely.
- **Pydantic for data, dataclass for services.** See [Type system](concepts/type-system.md). Don't make a service class a `BaseModel` unless you have a *specific* reason.
- **Submodule imports inside `src/`.** `from beekeeper.foo.bar import Baz`, never `from beekeeper import Baz` from another src/ file. Top-level package imports during package init create circular-load hazards.
- **Commits in the imperative.** Match existing log style: `Make the package importable`, not `Made the package importable` or `Makes the package importable`.

## Tests

Add tests for any new behavior. Unit tests live in `tests/`, named `test_<module>.py`. Tests for the McDonald's example go in `tests/test_mcdonalds_example.py`.

Tests can use the public API via `from beekeeper import ...`. Tests for internals can reach into submodules.

## Docs

User-facing docs are markdown under `docs/`. Each page is small and orthogonal — a single concept or recipe. The reference page is auto-generated from class docstrings via mkdocstrings; if you add a public class, write a docstring with at minimum a one-line summary.
