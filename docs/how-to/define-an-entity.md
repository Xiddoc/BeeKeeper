# Define an Entity

```python
from datetime import datetime
from beekeeper import Entity, Unavailability


class MyUnavailability(Unavailability[datetime]):
    is_paid_leave: bool


class MyWorker(Entity[MyUnavailability]):
    name: str
    role: str
```

Subclass `Unavailability[T]` to add domain-specific absence fields, then subclass `Entity[YourUnavailability]` to add the worker fields you care about.

The `[YourUnavailability]` parameter on `Entity` propagates: an algorithm written against `Entity[MyUnavailability]` will see `MyUnavailability` instances when iterating `entity.unavailabilities`, with their custom fields available statically.

Entity is a pydantic `BaseModel` with `extra="forbid"`, so JSON adapters will reject unknown fields. Domain subclasses inherit that strictness.
