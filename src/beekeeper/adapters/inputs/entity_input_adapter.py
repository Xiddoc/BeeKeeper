from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.entities.entity import TEntity


class EntityInputAdapter(ABC):
    @abstractmethod
    def get_entities(self) -> Iterable[TEntity]:
        pass
