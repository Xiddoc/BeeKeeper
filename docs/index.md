# BeeKeeper 🐝

> Manage the Bee-sy with ease.

BeeKeeper is a Python 3.13+ framework for assigning **entities** (workers, vehicles, anything assignable) to **allocation requests** over date ranges, subject to a **rules pipeline** and an **algorithm** you supply. You bring the data and the assignment strategy; BeeKeeper wires the orchestration, the rule pipeline, and the input/output adapters with full PEP 695 generic typing end-to-end.

## Why BeeKeeper

Most scheduling problems share the same shape — *you have things to do, you have people who can do them, and a stack of rules about who can do what when* — but every domain has its own vocabulary, its own constraints, and its own preferences. McDonald's needs to staff cashiers and cooks. A restaurant needs to schedule waiters and a sommelier. An Amazon warehouse needs to fill line positions with people qualified for the equipment. BeeKeeper gives you one orchestration layer that adapts to all of them: subclass `Entity` and `AllocationRequest`, write the rules that matter to your domain, plug in any algorithm, and the framework type-checks the whole pipeline so a `restaurant.run()` and a `warehouse.run()` can sit side by side without leaking each other's types.

## Install

```bash
uv sync                       # install + create venv from uv.lock
```

There is no published PyPI release yet — clone the repo and depend on it via path or git URL.

### Optional extras

The `OrToolsAssignmentAlgorithm` requires Google's OR-Tools, which is heavyweight enough (~50 MB) that it's gated behind an optional extra:

```bash
uv sync --extra ortools       # working in the BeeKeeper repo itself
uv add 'beekeeper[ortools]'   # depending on BeeKeeper from another project
pip install 'beekeeper[ortools]'   # if you prefer pip
```

Without the extra installed, importing `beekeeper.algorithm.implementations.or_tools` succeeds; instantiating `OrToolsAssignmentAlgorithm()` raises `ImportError` with the install hint. The other two bundled algorithms (backtracking and load-balancing) have no extras to enable.

## Quickstart

```python
from beekeeper import (
    AvailabilityRule,
    BeeKeeper,
    CompositeInputAdapter,
    ConsoleOutputAdapter,
    LoadBalancingAssignmentAlgorithm,
    RequestedEntityRule,
)

from my_app.adapters import ExcelEntityAdapter, ExcelAllocationAdapter
from my_app.rules import MustHaveLicenseRule
from my_app.entities import MyWorker
from my_app.allocations import MyRequest

bk = BeeKeeper[MyWorker, MyRequest](
    input_adapter=CompositeInputAdapter(
        entity_adapter=ExcelEntityAdapter("staff.xlsx"),
        allocation_adapter=ExcelAllocationAdapter("requests.xlsx"),
    ),
    algorithm=LoadBalancingAssignmentAlgorithm[MyWorker, MyRequest](),
    preliminary_rules=[
        MustHaveLicenseRule(),
        AvailabilityRule[MyWorker, MyRequest](),
        RequestedEntityRule[MyWorker, MyRequest](),
    ],
    output_adapters=[ConsoleOutputAdapter[MyWorker, MyRequest]()],
)
bk.execute()
```

A complete worked example lives at [`examples/mcdonalds/`](examples/mcdonalds.md).

## Where to next

- **New here?** Read the [Overview](concepts/overview.md) and [Pipeline](concepts/pipeline.md).
- **Building for your domain?** Start with [Define an Entity](how-to/define-an-entity.md), [Define an Allocation](how-to/define-an-allocation.md), [Write a Preliminary Rule](how-to/write-a-preliminary-rule.md).
- **Curious about the type system?** [Type System](concepts/type-system.md).
- **Need the API?** [Reference](reference.md).
