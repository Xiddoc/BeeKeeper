from collections.abc import Iterable
from pathlib import Path
from typing import Generic

from pydantic import BaseModel, ConfigDict, TypeAdapter

from beekeeper import EntityInputAdapter
from beekeeper.entities.entity import TEntity


class JsonEntityInputAdapter(EntityInputAdapter, BaseModel, Generic[TEntity]):
    file: Path
    entity_type: type[TEntity]

    def get_entities(self) -> Iterable[TEntity]:
        adapter = TypeAdapter(list[TEntity], config=ConfigDict(use_enum_values=True))
        return adapter.validate_json(self.file.read_text())
