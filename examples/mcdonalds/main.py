from beekeeper import BeeKeeper, MixedInputAdapter
from examples.mcdonalds.mcworkers_input import McWorkerEntityInputAdapter


def main() -> None:
    entity_adapter = McWorkerEntityInputAdapter()
    input_adapter = MixedInputAdapter(entity_adapter, None)
    mcdonalds_manager = BeeKeeper(input_adapter=input_adapter)


if __name__ == "__main__":
    main()
