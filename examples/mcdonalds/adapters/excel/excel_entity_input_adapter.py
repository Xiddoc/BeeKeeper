from collections.abc import Iterable

from beekeeper import Entity, EntityInputAdapter


class ExcelEntityInputAdapter(EntityInputAdapter):
    def get_entities(self) -> Iterable[Entity]:
        return []
