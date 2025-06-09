import json
from collections.abc import Iterable
from pathlib import Path
from typing import Generic, Self

from pydantic import BaseModel, ConfigDict

from beekeeper import EntityInputAdapter
from beekeeper.entities.entity import TEntity


class Entities(BaseModel, Generic[TEntity]):
    model_config = ConfigDict(use_enum_values=True)

    entities: list[TEntity]


class JsonEntityInputAdapter(EntityInputAdapter, BaseModel, Generic[TEntity]):
    file: Path
    entity_type: type[TEntity]

    @classmethod
    def create(cls, file: Path, entitiy_type: type[TEntity]) -> Self:
        return cls(file=file, entity_type=entitiy_type)

    def get_entities(self) -> Iterable[TEntity]:
        file_contents = self.file.read_text()
        data = json.loads(file_contents)

        all_entities = Entities[self.entity_type].model_validate({"entities": data})
        return all_entities.entities
