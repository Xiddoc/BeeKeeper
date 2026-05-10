from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter

from beekeeper import EntityInputAdapter
from beekeeper.entities.entity import Entity


class JsonEntityInputAdapter[TEntity: Entity[Any]](EntityInputAdapter[TEntity], BaseModel):
    file: Path
    entity_type: type[TEntity]

    def get_entities(self) -> Iterable[TEntity]:
        adapter = TypeAdapter(list[TEntity], config=ConfigDict(use_enum_values=True))
        return adapter.validate_json(self.file.read_text())
