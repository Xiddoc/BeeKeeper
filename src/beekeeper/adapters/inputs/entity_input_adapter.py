from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from beekeeper.entities.entity import Entity


class EntityInputAdapter[TEntity: Entity[Any]](ABC):
    @abstractmethod
    def get_entities(self) -> Iterable[TEntity]:
        pass
