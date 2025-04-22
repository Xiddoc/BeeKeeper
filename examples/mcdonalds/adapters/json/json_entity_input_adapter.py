import json
from collections.abc import Iterable
from pathlib import Path

from beekeeper import Entity, EntityInputAdapter


class JsonEntityInputAdapter(EntityInputAdapter):
    def __init__(self, entity_input_file: str | Path) -> None:
        self.entity_input_file = Path(entity_input_file)

    def get_entities(self) -> Iterable[Entity]:
        with self.entity_input_file.open("r") as f:
            json_entities = json.load(f)

        return [Entity(**item) for item in json_entities]
