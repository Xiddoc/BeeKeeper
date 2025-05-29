from collections.abc import Iterable

from beekeeper import AllocationRequest, Entity, InputAdapter, OutputAdapter
from beekeeper.algorithm.algorithm_state import State
from beekeeper.algorithm.base_algorithm import BaseAlgorithm
from beekeeper.rules.base_rule import BaseRule
from beekeeper.rules.preliminary_rule import PreliminaryRule
from beekeeper.rules.stateful_rule import StatefulRule


class BeeKeeper:
    """
    Just buzzing along...
                            🐝 ~ ~ ~
                                        Don't mind me...
    """

    def __init__(
        self,
        *,
        algorithm: BaseAlgorithm,
        rules: Iterable[BaseRule],
        input_adapter: InputAdapter,
        output_adapters: Iterable[OutputAdapter] | None = None,
    ) -> None:
        if output_adapters is None:
            output_adapters: list[OutputAdapter] = []

        self._algorithm = algorithm
        self._rules = rules
        self._input_adapter = input_adapter
        self._output_adapters = output_adapters

    def execute(self) -> None:
        entities = self._input_adapter.get_entities()
        allocations = self._input_adapter.get_allocations()

        preliminary_rules = [rule for rule in self._rules if isinstance(rule, PreliminaryRule)]
        stateful_rules = [rule for rule in self._rules if isinstance(rule, StatefulRule)]
        self._run_preliminary_rules(preliminary_rules, entities, allocations)

        output_state = self._algorithm.run(allocations=allocations, entities=entities, rules=stateful_rules)

        self._dispatch_output_to_ouput_handlers(output_state)

    def _run_preliminary_rules(
        self,
        preliminary_rules: Iterable[PreliminaryRule],
        entities: Iterable[Entity],
        allocations: Iterable[AllocationRequest],
    ) -> None:
        """
        Runs the preliminary rules in a single pass with no "complex" computation/algorithm needed.
        Preliminary rules can be run before the algorithm, since they have no dynamic properties
        that only could be calculated during processing.

        Args:
            preliminary_rules: The rules to run.
            entities: The entities which will be used in the allocations.
            allocations: The allocations to allocate.

        Returns:
            Unknown  # TODO
        """
        raise NotImplementedError

    def _dispatch_output_to_ouput_handlers(self, output_state: State) -> None:
        """
        Calls on each of the output handlers with the output of the algorithm.

        Args:
            output_state: The output of the algorithm- the final state of the assigned allocations.

        Returns:
            None
        """
        for output_adapter in self._output_adapters:
            output_adapter.handle_output(output_state)
