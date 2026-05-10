# Write an Output Adapter

```python
from beekeeper import OutputAdapter, State


class DatabaseOutputAdapter(OutputAdapter[MyWorker, MyRequest]):
    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def handle_output(self, output_state: State[MyWorker, MyRequest]) -> None:
        for planned in output_state.planned_allocations:
            self._conn.insert_allocation(
                task=planned.request.allocation_type.value,
                start=planned.request.date_range.start_date,
                end=planned.request.date_range.end_date,
                workers=[e.name for e in planned.assigned_entities],
            )
```

`OutputAdapter[TEntity, TAllocReq]` requires `handle_output(state) -> None`. Iterate the `state.planned_allocations` property to read the algorithm's results.

You can configure multiple output adapters on a single `BeeKeeper` — e.g. one to print to console, one to write to a database, one to export JSON. Each one receives the same `state`.

The framework ships `beekeeper.adapters.outputs.console.ConsoleOutputAdapter` for trivial debugging output. Production code should ship a domain-specific adapter.
