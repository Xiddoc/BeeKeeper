# The Type System

BeeKeeper is generic end-to-end using PEP 695 syntax. Two TypeVars carry every domain's identity through the framework: **`TEntity`** (the kind of thing being assigned) and **`TAllocationRequest`** (the kind of slot being filled). You declare them once on your concrete subclasses and they flow through every adapter, rule, algorithm, and stage automatically.

## The shape

```python
class McUnavailability(Unavailability[datetime]): ...
class McWorker(Entity[McUnavailability]):
    name: str
    rank: McJobPosition

class McRequest(AllocationRequest[McAllocationType, McWorker]):
    allowed_ranks: frozenset[McJobPosition]

class McRankRule(HardPreliminaryRule[McWorker, McRequest]):
    def check(self, entity: McWorker, allocation: McRequest) -> bool:
        return entity.rank in allocation.allowed_ranks

bk = BeeKeeper[McWorker, McRequest](...)
```

Inside `McRankRule.check`, `entity.rank` autocompletes as `McJobPosition`. Inside a custom algorithm, `state.add_assignment(...)` requires a `Assignment[McRequest, McWorker]`. Inside a `ConsoleOutputAdapter[McWorker, McRequest]`, the planned allocations you iterate carry the right types. **mypy strict** verifies the whole chain.

## Why two TypeVars and not one or three

- **One** (`TEntity` only) wouldn't carry the allocation shape — rules and algorithms wouldn't know what fields the AllocationRequest subclass has.
- **Three** (`TEntity`, `TAllocationType`, `TAllocationRequest`) is what the framework looked like mid-refactor. `TAllocationType` is recoverable from `TAllocationRequest` (it's the enum the allocation carries), so making it a separate parameter just added verbosity without type fidelity.

## The `[Any]` slot in bounds

You'll see a lot of `[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]` in the framework source. Why `[Any]`? Because `Entity` is itself generic over `TUnavailability`, and writing the bound as `[TEntity: Entity]` triggers mypy's `[type-arg]` warning ("missing parameters for generic type"). `Entity[Any]` tells mypy *any parameterization of Entity is acceptable as a bound*, which is what we want — `TEntity` can be `Entity[McUnavailability]`, `Entity[Unavailability]`, or anything else, regardless of which unavailability flavor it picks.

This is purely a syntactic accommodation. At call sites you parameterize concretely (`BeeKeeper[McWorker, McRequest](...)`) and the framework infers `TUnavailability=McUnavailability` from the chain.

## PEP 696 defaults

`DateRange[T: date = datetime]` and `Unavailability[T: date = datetime]` use PEP 696 defaults: bare `DateRange(...)` instances default to `datetime` granularity. Domains that want whole-day shifts subclass with `DateRange[date]`. The default keeps the most-common path frictionless.

## Pydantic vs. plain dataclass

BeeKeeper uses **pydantic `BaseModel`** for *data*: `Entity`, `AllocationRequest`, `Unavailability`, `DateRange`. These travel across IO boundaries (JSON adapters), get validated, get serialized.

It uses **plain `@dataclass`** for *services and runtime state*: `CompositeInputAdapter`, `BeeKeeperFlowState`, `Candidate`, `Assignment`. These hold dependencies or in-flight state, not data. Pydantic doesn't earn its keep here, and its runtime introspection actively conflicts with ABC-typed fields and PEP 695 type parameter resolution.

If you're authoring framework primitives — a custom flow stage, a custom adapter base — follow the same rule. If you're authoring domain data, use `BaseModel`.
