# Define an Entity

```python
from datetime import datetime
from beekeeper import Entity, Inavailability


class MyInavailability(Inavailability[datetime]):
    is_paid_leave: bool


class MyWorker(Entity[MyInavailability]):
    name: str
    role: str
```

Subclass `Inavailability[T]` to add domain-specific absence fields, then subclass `Entity[YourInavailability]` to add the worker fields you care about.

The `[YourInavailability]` parameter on `Entity` propagates: an algorithm written against `Entity[MyInavailability]` will see `MyInavailability` instances when iterating `entity.inavailabilities`, with their custom fields available statically.

Entity is a pydantic `BaseModel` with `extra="forbid"`, so JSON adapters will reject unknown fields. Domain subclasses inherit that strictness.
