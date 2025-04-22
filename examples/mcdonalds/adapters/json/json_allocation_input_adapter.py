import json
from collections.abc import Iterable
from pathlib import Path

from beekeeper import AllocationInputAdapter, AllocationRequest


class JsonAllocationInputAdapter(AllocationInputAdapter):
    def __init__(self, allocation_input_file: str | Path) -> None:
        self.allocation_input_file = Path(allocation_input_file)

    def get_allocations(self) -> Iterable[AllocationRequest]:
        with self.allocation_input_file.open("r") as f:
            json_allocations = json.load(f)

        return [AllocationRequest(**item) for item in json_allocations]
