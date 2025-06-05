from collections.abc import Iterable

from pydantic import BaseModel

from beekeeper import AllocationRequest, Entity
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


class BeeKeeperFlowState(BaseModel):
    entities: Iterable[Entity]
    allocations: Iterable[AllocationRequest]
    preliminary_rules: Iterable[PreliminaryRule]
    stateful_rules: Iterable[StatefulRule]
