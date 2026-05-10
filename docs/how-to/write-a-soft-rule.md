# Write a Soft Rule

```python
from beekeeper import SoftPreliminaryRule


class PreferSeniorWorkers(SoftPreliminaryRule[MyWorker, MyRequest]):
    def score(self, entity: MyWorker, allocation: MyRequest) -> float:
        return min(entity.years_of_service / 10, 1.0)
```

Soft rules return a non-negative `score: float` instead of a `bool`. `compatible` stays `True` — soft rules never veto. The framework aggregates per-rule scores via geometric mean (see [Soft-rules aggregation](../explanations/soft-rules-aggregation.md)) and surfaces the result on each `Candidate`.

A score of `1.0` is neutral. Higher is better. The bundled `GreedyAssignmentAlgorithm` picks highest-scored candidates first.

Both preliminary and stateful soft variants exist — `SoftPreliminaryRule` for static preferences, `SoftStatefulRule` when the score depends on what's already been scheduled (e.g. "prefer the worker who hasn't done this task recently").

For both axes (hard veto *and* soft score) in a single rule — uncommon — subclass `PreliminaryRule` or `StatefulRule` directly and return a `RuleVerdict(compatible=..., score=...)` from `evaluate(...)`.
