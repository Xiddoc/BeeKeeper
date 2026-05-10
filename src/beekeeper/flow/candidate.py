from dataclasses import dataclass
from typing import Any

from beekeeper.entities.entity import Entity


@dataclass(frozen=True)
class Candidate[TEntity: Entity[Any]]:
    """An entity being considered for an allocation, paired with its current score.

    Score starts at 1.0 (neutral) and is multiplied by each soft rule's score
    during the preliminary pass. Hard-rule failures cause the candidate to be
    pruned from the map entirely rather than recorded with a score of 0.
    """

    entity: TEntity
    score: float = 1.0
