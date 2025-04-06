from abc import ABC, abstractmethod


class EntityInputAdapter(ABC):
    @abstractmethod
    def get_entities(self):
        pass
