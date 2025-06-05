from pathlib import Path

from beekeeper import BeeKeeper, MixedInputAdapter
from examples.mcdonalds.adapters.json import JsonAllocationInputAdapter
from examples.mcdonalds.allocations.allocation_request import McDonaldsAllocationRequest
from examples.mcdonalds.mcworkers_input import McWorkerEntityInputAdapter

ALLOCATION_INPUT_FILE = Path("examples") / "mcdonalds" / "allocations.json"


def main() -> None:
    allocation_input_adapter = JsonAllocationInputAdapter.create(
        file=ALLOCATION_INPUT_FILE, allocation_type=McDonaldsAllocationRequest
    )
    print(allocation_input_adapter.get_allocations())
    entity_adapter = McWorkerEntityInputAdapter()
    input_adapter = MixedInputAdapter(entity_adapter=entity_adapter, allocation_adapter=allocation_input_adapter)
    BeeKeeper(input_adapter=input_adapter)


if __name__ == "__main__":
    main()
