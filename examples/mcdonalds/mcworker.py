from dataclasses import dataclass

from beekeeper import Entity


@dataclass
class McWorker(Entity):
    name: str
