from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.entities.entity import Entity


class EntityInputAdapter(ABC):

    @abstractmethod
    def get_entities(self) -> Iterable[Entity]:
        pass
