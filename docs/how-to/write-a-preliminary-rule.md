# Write a Preliminary Rule

```python
from beekeeper import HardPreliminaryRule


class RoleEligibilityRule(HardPreliminaryRule[MyWorker, MyRequest]):
    def check(self, entity: MyWorker, allocation: MyRequest) -> bool:
        return entity.role in allocation.allowed_roles
```

`HardPreliminaryRule[TEntity, TAllocReq]` only requires `check(entity, allocation) -> bool`. A `False` prunes the candidate from the allocation in stage 2.

Preliminary rules don't see the in-progress schedule. Use them for facts that don't change as more allocations are planned: licensing, role eligibility, qualifications, exemptions, geographic feasibility.

Both `entity` and `allocation` are typed as your concrete subclasses — IDE autocomplete and mypy enforcement work without `isinstance` casts.

For preference scoring instead of binary checks, see [Write a Soft Rule](write-a-soft-rule.md).
