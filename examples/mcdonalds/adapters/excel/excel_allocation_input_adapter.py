from beekeeper import AllocationInputAdapter, AllocationRequest


class ExcelAllocationInputAdapter(AllocationInputAdapter):
    def get_allocations(self) -> list[AllocationRequest]:
        return []
