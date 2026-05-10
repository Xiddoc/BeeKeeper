from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter

from beekeeper import AllocationInputAdapter
from beekeeper.allocations.allocation_request import AllocationRequest


class JsonAllocationInputAdapter[TAllocationRequest: AllocationRequest](
    AllocationInputAdapter[TAllocationRequest], BaseModel
):
    file: Path
    allocation_type: type[TAllocationRequest]

    def get_allocations(self) -> Iterable[TAllocationRequest]:
        adapter = TypeAdapter(list[TAllocationRequest], config=ConfigDict(use_enum_values=True))
        return adapter.validate_json(self.file.read_text())
