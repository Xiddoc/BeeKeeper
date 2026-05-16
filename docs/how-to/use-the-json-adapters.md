# Use the JSON Adapters

```python
from pathlib import Path
from beekeeper import JsonAllocationInputAdapter, JsonEntityInputAdapter

entity_adapter = JsonEntityInputAdapter(file=Path("workers.json"), entity_type=MyWorker)
allocation_adapter = JsonAllocationInputAdapter(file=Path("requests.json"), allocation_type=MyRequest)
```

Each adapter takes a `file: Path` and a `*_type: type[...]` and produces an `Iterable` of validated, typed instances when you call `get_entities()` / `get_allocations()`. The JSON file must be an array of objects matching the type's pydantic schema.

## Strict-only, on purpose

Both adapters reject unknown JSON fields. The framework's `Entity`, `AllocationRequest`, `Unavailability`, and `DateRange` base classes set `model_config = ConfigDict(extra="forbid")`, and your domain subclasses inherit it. A JSON object with a field your model doesn't declare raises `ValidationError`.

This is deliberate. Silent field drops are the source of an entire category of "the schema looks right but the data isn't being read" bugs. If your data legitimately has fields you want to ignore — old data, third-party feeds, exploratory work — write your own `EntityInputAdapter` / `AllocationInputAdapter` subclass with whatever leniency makes sense for your case. The framework doesn't ship a knob.

## Enums and dates

JSON enum values are matched against your enum's `value` (e.g. `"CASHIER"` matches `McJobPosition.CASHIER = "CASHIER"`). String-valued enums are recommended over `auto()` so fixtures stay readable.

Datetime fields accept ISO 8601 strings. Both timezone-naive and timezone-aware are accepted, but `DateRange` validates that `start_date` and `end_date` agree on which.
