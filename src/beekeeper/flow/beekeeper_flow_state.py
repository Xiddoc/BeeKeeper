from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


@dataclass
class BeeKeeperFlowState[TEntity: Entity[Any], TAllocationRequest: AllocationRequest[Any, Any]]:
    entities: Iterable[TEntity]
    allocations: Iterable[TAllocationRequest]
    preliminary_rules: Iterable[PreliminaryRule[TEntity, TAllocationRequest]]
    stateful_rules: Iterable[StatefulRule[TEntity, TAllocationRequest]]
