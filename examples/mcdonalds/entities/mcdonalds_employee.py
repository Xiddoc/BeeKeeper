from mcdonalds.entities.entity_properties import McDonaldsUnavailability, McJobPosition

from beekeeper import Entity


class McWorker(Entity[McDonaldsUnavailability]):
    name: str
    rank: McJobPosition
