from abc import ABC, abstractmethod


class OutputAdapter(ABC):
    @abstractmethod
    def handle_output(self):
        pass
