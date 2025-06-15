from collections.abc import Iterable
from pathlib import Path
from typing import Generic

from pydantic import BaseModel, ConfigDict, TypeAdapter

from beekeeper import AllocationInputAdapter
from beekeeper.allocations.allocation_request import TAllocationRequest


class JsonAllocationInputAdapter(AllocationInputAdapter, BaseModel, Generic[TAllocationRequest]):
    file: Path
    allocation_type: type[TAllocationRequest]

    def get_allocations(self) -> Iterable[TAllocationRequest]:
        adapter = TypeAdapter(list[TAllocationRequest], config=ConfigDict(use_enum_values=True))
        return adapter.validate_json(self.file.read_text())
