from collections.abc import Iterable
from dataclasses import dataclass, field

from beekeeper.algorithm.algorithm_state import AssignmentState
from beekeeper.allocations.allocation_request import AnyRequest
from beekeeper.entities.entity import AnyEntity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


@dataclass
class BeeKeeperFlowState[TEntity: AnyEntity, TAllocationRequest: AnyRequest]:
    """In-flight state passed between flow stages.

    The pipeline materializes the input adapter's iterables into lists at
    construction time so every stage can iterate them freely. Stage 1 fills
    ``candidate_map`` with the entities that could plausibly take each
    allocation; stage 2 prunes that map and decorates each remaining
    candidate with a score; the algorithm in stage 3 consumes the pruned,
    scored map alongside the raw allocations and entities and exposes its
    result via ``algorithm_result`` for any custom downstream stage.

    ``candidate_map`` is keyed by ``id(allocation)`` because allocation
    requests aren't required to be hashable in general — using object
    identity sidesteps the requirement and stays stable for the lifetime
    of one ``BeeKeeper.execute()`` call.

    ``algorithm_result`` is populated by ``RunAlgorithmAndDispatchResults``
    *before* it dispatches to output adapters, so user-supplied stages
    chained after it can inspect the planned allocations. It defaults to
    ``None`` for callers who replace the algorithm stage entirely.
    """

    entities: list[TEntity]
    allocations: list[TAllocationRequest]
    preliminary_rules: Iterable[PreliminaryRule[TEntity, TAllocationRequest]]
    stateful_rules: Iterable[StatefulRule[TEntity, TAllocationRequest]]
    candidate_map: dict[int, list[Candidate[TEntity]]] = field(default_factory=dict)
    algorithm_result: AssignmentState[TEntity, TAllocationRequest] | None = None
