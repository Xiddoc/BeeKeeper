from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


@dataclass
class BeeKeeperFlowState[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]:
    """In-flight state passed between flow stages.

    The pipeline materializes the input adapter's iterables into lists at
    construction time so every stage can iterate them freely. Stage 1 fills
    ``candidate_map`` with the entities that could plausibly take each
    allocation; stage 2 prunes that map and decorates each remaining
    candidate with a score; the algorithm in stage 3 consumes the pruned,
    scored map alongside the raw allocations and entities.

    ``candidate_map`` is keyed by ``id(allocation)`` because allocation
    requests aren't required to be hashable in general — using object
    identity sidesteps the requirement and stays stable for the lifetime
    of one ``BeeKeeper.execute()`` call.
    """

    entities: list[TEntity]
    allocations: list[TAllocationRequest]
    preliminary_rules: Iterable[PreliminaryRule[TEntity, TAllocationRequest]]
    stateful_rules: Iterable[StatefulRule[TEntity, TAllocationRequest]]
    candidate_map: dict[int, list[Candidate[TEntity]]] = field(default_factory=dict)
