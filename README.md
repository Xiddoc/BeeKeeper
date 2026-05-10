# 🐝 BeeKeeper

> Manage the Bee-sy with ease.

<p align="center">
  <a href="https://github.com/Xiddoc/Beekeeper/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Xiddoc/Beekeeper/ci.yml?branch=master&style=for-the-badge&logo=githubactions&label=CI" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.13+-blue?style=for-the-badge&logo=python" alt="Python 3.13+">
  <a href="https://xiddoc.github.io/Beekeeper/"><img src="https://img.shields.io/badge/docs-mkdocs--material-blue?style=for-the-badge&logo=materialformkdocs&logoColor=white" alt="Docs"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL3.0-green?style=for-the-badge" alt="License: GPL3.0"></a>
</p>

BeeKeeper is a **Python 3.13+ framework** for assigning entities (workers, vehicles, anything assignable) to allocation requests over date ranges, subject to a rules pipeline and an algorithm you supply. PEP 695 generics flow through every layer — input adapters, rules, algorithm, output adapters — so domain types like `BeeKeeper[McWorker, McRequest]` give you static type-checking and IDE autocomplete end-to-end.

## Install

```bash
git clone https://github.com/Xiddoc/Beekeeper.git
cd Beekeeper
uv sync
```

For the OR-Tools-backed assignment algorithm, add the optional extra:

```bash
uv sync --extra ortools
```

See [Optional extras](https://xiddoc.github.io/Beekeeper/#optional-extras) in the docs for the full set of install paths.

## 30-line quickstart

```python
from beekeeper import BeeKeeper, MixedInputAdapter
from beekeeper.adapters.outputs.console import ConsoleOutputAdapter
from beekeeper.algorithm.greedy import GreedyAssignmentAlgorithm
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule

from my_app.adapters import ExcelEntityAdapter, ExcelAllocationAdapter
from my_app.rules import MustHaveLicenseRule
from my_app.entities import MyWorker
from my_app.allocations import MyRequest

bk = BeeKeeper[MyWorker, MyRequest](
    input_adapter=MixedInputAdapter(
        entity_adapter=ExcelEntityAdapter("staff.xlsx"),
        allocation_adapter=ExcelAllocationAdapter("requests.xlsx"),
    ),
    algorithm=GreedyAssignmentAlgorithm[MyWorker, MyRequest](),
    preliminary_rules=[
        MustHaveLicenseRule(),
        AvailabilityRule[MyWorker, MyRequest](),
        RequestedEntityRule[MyWorker, MyRequest](),
    ],
    output_adapters=[ConsoleOutputAdapter[MyWorker, MyRequest]()],
)
bk.execute()
```

A complete worked example lives at [`examples/mcdonalds/`](examples/mcdonalds), and runs end-to-end with `python -m mcdonalds.main mcdonalds/workers.json mcdonalds/allocations.json`.

## Documentation

Full docs at **[xiddoc.github.io/Beekeeper](https://xiddoc.github.io/Beekeeper/)** — concepts, how-to recipes, the McDonald's walkthrough, and an auto-generated API reference.

Or build locally:

```bash
uv run mkdocs serve
```

## Development

```bash
uv sync --all-groups            # install dev deps
uv run ruff check               # lint
uv run ruff format              # format
uv run mypy src                 # type-check
uv run pytest                   # tests
uv run mkdocs build --strict    # docs
uv run pre-commit install       # one-time
```

CI runs all of these on every push and pull request.

## License

[GPL-3.0-or-later](LICENSE).
