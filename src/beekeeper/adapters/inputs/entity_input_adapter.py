from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.entities.entity import AnyEntity


class EntityInputAdapter[TEntity: AnyEntity](ABC):
    @abstractmethod
    def get_entities(self) -> Iterable[TEntity]:
        pass
