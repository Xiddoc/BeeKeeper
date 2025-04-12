from collections.abc import Iterable

from beekeeper import InputAdapter, OutputAdapter


class BeeKeeper:
    """
    Just buzzing along...
                            🐝 ~ ~ ~
                                        Don't mind me...
    """

    def __init__(self, input_adapter: InputAdapter, output_adapters: Iterable[OutputAdapter] | None = None) -> None:
        if output_adapters is None:
            output_adapters = []

        self._input_adapter = input_adapter
        self._output_adapters = output_adapters

    def execute(self) -> None: ...

