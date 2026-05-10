from mcdonalds.allocations.allocation_request import McDonaldsAllocationRequest
from mcdonalds.entities.mcdonalds_employee import McWorker

from beekeeper import HardPreliminaryRule


class McRankRule(HardPreliminaryRule[McWorker, McDonaldsAllocationRequest]):
    """McDonald's-specific rule: an entity can only take an allocation whose
    ``allowed_ranks`` includes the entity's rank.
    """

    def check(self, entity: McWorker, allocation: McDonaldsAllocationRequest) -> bool:
        return entity.rank in allocation.allowed_ranks
