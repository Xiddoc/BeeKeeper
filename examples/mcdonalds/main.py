from argparse import ArgumentParser

from mcdonalds.allocations.allocation_request import McDonaldsAllocationRequest
from mcdonalds.entities.mcdonalds_employee import McWorker
from mcdonalds.rules.mc_rank_rule import McRankRule
from pydantic import BaseModel, FilePath

from beekeeper import BeeKeeper, MixedInputAdapter
from beekeeper.adapters.inputs.json_allocation_input_adapter import JsonAllocationInputAdapter
from beekeeper.adapters.inputs.json_entity_input_adapter import JsonEntityInputAdapter
from beekeeper.adapters.outputs.console import ConsoleOutputAdapter
from beekeeper.algorithm.implementations.greedy import GreedyAssignmentAlgorithm
from beekeeper.rules.builtins import AvailabilityRule, RequestedEntityRule


class McDonaldsBeeKeeperInputs(BaseModel):
    allocations_input_file: FilePath
    workers_input_file: FilePath


def _create_cli_args_input_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("workers_input_file")
    parser.add_argument("allocations_input_file")
    return parser


def _get_beekeeper_inputs_from_cli_args() -> McDonaldsBeeKeeperInputs:
    cli_args = _create_cli_args_input_parser().parse_args()
    return McDonaldsBeeKeeperInputs(**vars(cli_args))


def run(inputs: McDonaldsBeeKeeperInputs) -> None:
    """Wire and execute a BeeKeeper for the McDonald's example.

    Split out from ``main`` so tests can drive the pipeline programmatically
    without going through argparse.
    """
    input_adapter = MixedInputAdapter(
        entity_adapter=JsonEntityInputAdapter(file=inputs.workers_input_file, entity_type=McWorker),
        allocation_adapter=JsonAllocationInputAdapter(
            file=inputs.allocations_input_file,
            allocation_type=McDonaldsAllocationRequest,
        ),
    )

    BeeKeeper[McWorker, McDonaldsAllocationRequest](
        input_adapter=input_adapter,
        algorithm=GreedyAssignmentAlgorithm[McWorker, McDonaldsAllocationRequest](),
        preliminary_rules=[
            McRankRule(),
            AvailabilityRule[McWorker, McDonaldsAllocationRequest](),
            RequestedEntityRule[McWorker, McDonaldsAllocationRequest](),
        ],
        output_adapters=[ConsoleOutputAdapter[McWorker, McDonaldsAllocationRequest]()],
    ).execute()


def main() -> None:
    inputs = _get_beekeeper_inputs_from_cli_args()
    run(inputs)


if __name__ == "__main__":
    main()
