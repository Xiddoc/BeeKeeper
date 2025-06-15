from mcdonalds.entities.entity_properties import McDonaldsInavailability, McJobPosition

from beekeeper import Entity


class McWorker(Entity[McDonaldsInavailability]):
    name: str
    rank: McJobPosition
