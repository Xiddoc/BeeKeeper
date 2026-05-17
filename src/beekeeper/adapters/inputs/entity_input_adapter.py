from abc import ABC, abstractmethod
from collections.abc import Iterable

from beekeeper.entities.entity import AnyEntity


class EntityInputAdapter[TEntity: AnyEntity](ABC):
    """
    Yields the pool of entities (workers, vehicles, …) the pipeline can assign.

    Implementations decide where entities come from — JSON, a DB, an HTTP
    call, an in-memory fixture. The framework iterates the result exactly
    once per ``BeeKeeper.execute()`` call.
    """

    @abstractmethod
    def get_entities(self) -> Iterable[TEntity]:
        pass
