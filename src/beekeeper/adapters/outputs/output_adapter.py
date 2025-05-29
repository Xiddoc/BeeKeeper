from abc import ABC, abstractmethod

from beekeeper.algorithm.algorithm_state import State


class OutputAdapter(ABC):
    @abstractmethod
    def handle_output(self, output_state: State) -> None:
        pass
