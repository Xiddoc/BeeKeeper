# Write an Input Adapter

```python
from beekeeper import EntityInputAdapter


class CsvWorkerAdapter(EntityInputAdapter[MyWorker]):
    def __init__(self, file: Path) -> None:
        self._file = file

    def get_entities(self) -> Iterable[MyWorker]:
        with self._file.open() as f:
            for row in csv.DictReader(f):
                yield MyWorker(name=row["name"], role=row["role"], inavailabilities=[])
```

For allocations, subclass `AllocationInputAdapter[YourRequest]` and implement `get_allocations(self) -> Iterable[YourRequest]`.

Most domains will have one of each. Compose them with `MixedInputAdapter`:

```python
adapter = MixedInputAdapter(
    entity_adapter=CsvWorkerAdapter(Path("staff.csv")),
    allocation_adapter=ApiAllocationAdapter(api_url="..."),
)
```

If both kinds of data come from the same source, subclass `InputAdapter[TEntity, TAllocReq]` directly and implement both methods on one class.

For JSON-from-file, the framework ships [`JsonEntityInputAdapter`](use-the-json-adapters.md) and `JsonAllocationInputAdapter` — strict-only, pydantic-backed, no leniency knob. Use them or write your own.
