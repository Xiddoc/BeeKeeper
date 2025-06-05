import json
from collections.abc import Iterable
from pathlib import Path
from typing import Generic, Self, TypeVar

from pydantic import BaseModel, ConfigDict

from beekeeper import AllocationInputAdapter, AllocationRequest

TAllocationRequest = TypeVar("TAllocationRequest", bound=AllocationRequest)


class AllocationRequests(BaseModel, Generic[TAllocationRequest]):
    model_config = ConfigDict(use_enum_values=True)

    requests: list[TAllocationRequest]


class JsonAllocationInputAdapter(AllocationInputAdapter, BaseModel, Generic[TAllocationRequest]):
    file: Path
    allocation_type: type[TAllocationRequest]

    @classmethod
    def create(cls, file: Path, allocation_type: type[TAllocationRequest]) -> Self:
        return cls(file=file, allocation_type=allocation_type)

    def get_allocations(self) -> Iterable[TAllocationRequest]:
        file_contents = self.file.read_text()
        data = json.loads(file_contents)

        allocation_requests = AllocationRequests[self.allocation_type].model_validate({"requests": data})
        return allocation_requests.requests
