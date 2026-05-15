# Define an Allocation

```python
from beekeeper import AllocationRequest, AllocationType


class MyTaskKind(AllocationType):
    PREP = "PREP"
    SERVE = "SERVE"
    CLEAN = "CLEAN"


class MyRequest(AllocationRequest[MyTaskKind, MyWorker]):
    allowed_roles: frozenset[str] = frozenset()
```

Two subclassing steps:

1. **`AllocationType`** is an empty `AbstractEnum` — extend it with your domain's task vocabulary. String values are recommended over `auto()` so JSON fixtures stay human-readable.
2. **`AllocationRequest[YourTaskKind, YourEntity]`** is the allocation shape. Add domain fields the rules and algorithm will key off (e.g. `allowed_roles`, `min_seniority`, `required_skills`).

The two parameters carry through: `MyRequest.allocation_type` is typed as `MyTaskKind`, and `MyRequest.requested_entities` is `tuple[MyWorker, ...]`. The framework's `required_count: int = 1` field is inherited; override the default if your domain's slots typically need more than one entity.
