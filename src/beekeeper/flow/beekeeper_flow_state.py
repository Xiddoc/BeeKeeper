from collections.abc import Iterable
from dataclasses import dataclass

from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.entities.entity import Entity
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


@dataclass
class BeeKeeperFlowState:
    entities: Iterable[Entity]
    allocations: Iterable[AllocationRequest]
    preliminary_rules: Iterable[PreliminaryRule]
    stateful_rules: Iterable[StatefulRule]
