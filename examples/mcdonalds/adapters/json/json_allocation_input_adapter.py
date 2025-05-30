import json
from collections.abc import Iterable
from pathlib import Path

from beekeeper import AllocationInputAdapter, AllocationRequest


class JsonAllocationInputAdapter[TAllocationRequest: AllocationRequest](AllocationInputAdapter):
    def __init__(self, allocation_input_file: str | Path, allocation_type: type[TAllocationRequest]) -> None:
        self.allocation_input_file = Path(allocation_input_file)
        self.allocation_type = allocation_type

    def get_allocations(self) -> Iterable[TAllocationRequest]:
        with self.allocation_input_file.open("r") as f:
            json_allocations = json.load(f)

        return [self.allocation_type.model_validate(item) for item in json_allocations]
