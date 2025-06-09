from argparse import ArgumentParser

from mcdonalds.adapters.json_allocation_input_adapter import JsonAllocationInputAdapter
from mcdonalds.allocations.allocation_request import McDonaldsAllocationRequest
from mcdonalds.entities.mcworkers_input import McWorkerEntityInputAdapter
from pydantic import BaseModel, FilePath

from beekeeper import BeeKeeper, InputAdapter, MixedInputAdapter


class McDonaldsBeekeeperInputs(BaseModel):
    allocations_input_file: FilePath


def _create_cli_args_input_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("allocations_input_file")
    return parser


def _get_beekeeper_inputs_from_cli_args() -> McDonaldsBeekeeperInputs:
    cli_args = _create_cli_args_input_parser().parse_args()
    return McDonaldsBeekeeperInputs(**vars(cli_args))


def _create_input_adapter(beekeeper_cli_args: McDonaldsBeekeeperInputs) -> InputAdapter:
    allocation_input_adapter = JsonAllocationInputAdapter.create(
        file=beekeeper_cli_args.allocations_input_file, allocation_type=McDonaldsAllocationRequest
    )

    entity_adapter = McWorkerEntityInputAdapter()

    return MixedInputAdapter(entity_adapter=entity_adapter, allocation_adapter=allocation_input_adapter)


def main() -> None:
    beekeeper_cli_args = _get_beekeeper_inputs_from_cli_args()
    input_adapter = _create_input_adapter(beekeeper_cli_args)
    BeeKeeper(input_adapter=input_adapter)


if __name__ == "__main__":
    main()
