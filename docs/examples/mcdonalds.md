# McDonald's Walkthrough

A complete worked example lives at [`examples/mcdonalds/`](https://github.com/Xiddoc/BeeKeeper/tree/master/examples/mcdonalds). Three workers, three allocations, all rules wired, runs end-to-end.

## What's defined

```
examples/mcdonalds/
├── allocations/
│   ├── allocation_request.py   — McDonaldsAllocationRequest with allowed_ranks
│   └── allocation_type.py      — McDonaldsAllocationType: CLEANING, COOKING, ...
├── entities/
│   ├── entity_properties.py    — Rank → McJobPosition + McDonaldsInavailability
│   └── mcdonalds_employee.py   — McWorker with name + rank
├── rules/
│   └── mc_rank_rule.py         — McRankRule checks entity.rank in allocation.allowed_ranks
├── allocations.json            — three sample allocations
├── workers.json                — five sample workers
└── main.py                     — wires everything and calls .execute()
```

## Run it

```bash
cd examples/
uv run python -m mcdonalds.main mcdonalds/workers.json mcdonalds/allocations.json
```

Expected output (one `ConsoleOutputAdapter` line per planned allocation):

```text
CLEANING [2025-06-01 00:00:00 -> 2025-06-03 00:00:00]: McWorker(...name='Alice', rank=<McJobPosition.CASHIER: 'CASHIER'>)
SERVING_FOOD [2025-06-10 00:00:00 -> 2025-06-10 00:00:00]: McWorker(...name='Alice'...)
COOKING [2025-06-15 00:00:00 -> 2025-06-15 00:00:00]: McWorker(...name='Carol'...), McWorker(...name='Eve'...)
```

## What it teaches

- **Multi-entity allocations.** The `COOKING` request has `required_count: 2` and gets two cooks assigned.
- **Preliminary rule combination.** `main.py` wires three rules: the domain-specific `McRankRule` plus the framework's `AvailabilityRule` and `RequestedEntityRule`. The greedy algorithm respects all of them.
- **Inavailability filtering.** Bob has a vacation overlapping the CLEANING shift, so he's pruned from candidates. Dave has a wedding on June 15, so he's pruned from COOKING and Eve takes his place.
- **JSON-driven inputs.** Both fixtures are validated strictly by `JsonEntityInputAdapter` / `JsonAllocationInputAdapter`. Try adding a typo to either file and watch the validation error fire.

## Where to extend

Add a `StatefulRule` that prevents the same worker from taking back-to-back allocations. Add a `SoftPreliminaryRule` that prefers more senior workers for managerial tasks. Replace the greedy algorithm with one that minimizes total `inavailability` violations across the schedule. The framework supports all three without changing the core; that's the point.
