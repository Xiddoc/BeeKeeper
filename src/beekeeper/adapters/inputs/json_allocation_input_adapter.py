from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pydantic import TypeAdapter

from beekeeper.adapters.inputs.allocation_input_adapter import AllocationInputAdapter
from beekeeper.allocations.allocation_request import AnyRequest


@dataclass
class JsonAllocationInputAdapter[TAllocationRequest: AnyRequest](
    AllocationInputAdapter[TAllocationRequest],
):
    """
    Strict JSON-backed adapter that loads allocation requests from a file.

    The file must contain a JSON array of objects matching
    ``allocation_type``'s schema. Validation is strict: any field not
    declared on the target allocation (or its nested types) will raise. This
    is enforced at the framework level — the framework's
    ``AllocationRequest`` base class sets
    ``model_config = ConfigDict(extra="forbid")``, which subclasses inherit
    unless they explicitly opt out.

    Want lenient parsing? Implement your own ``AllocationInputAdapter``
    subclass — the core only ships strict, well-defined, Pydantic-backed
    adapters.
    """

    file: Path
    allocation_type: type[TAllocationRequest]

    def get_allocations(self) -> Iterable[TAllocationRequest]:
        adapter: TypeAdapter[list[TAllocationRequest]] = TypeAdapter(list[self.allocation_type])  # type: ignore[name-defined]
        return adapter.validate_json(self.file.read_text())
