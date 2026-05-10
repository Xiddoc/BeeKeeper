from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.entities.entity import Entity


class EntityInputAdapter[TEntity: Entity](ABC):
    @abstractmethod
    def get_entities(self) -> Iterable[TEntity]:
        pass
