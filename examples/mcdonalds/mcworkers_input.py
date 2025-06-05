from collections.abc import Iterable
from datetime import datetime

from faker import Faker

from beekeeper import Entity, EntityInputAdapter, Inavailability
from examples.mcdonalds.mcpositions import McJobPositions
from examples.mcdonalds.mcworker import McWorker

fake = Faker()


class McWorkerEntityInputAdapter(EntityInputAdapter):
    def get_entities(self) -> Iterable[Entity]:
        return [
            McWorker(
                name=fake.full_name(),
                rank=McJobPositions.CASHIER,
                inavailabilities=[
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-15"),
                        reason="Job interview at Burger King.",
                    )
                ],
                exemptions=[],
            ),
            McWorker(name=fake.full_name(), rank=McJobPositions.CASHIER, inavailabilities=[], exemptions=[]),
            McWorker(
                name=fake.full_name(),
                rank=McJobPositions.COOK,
                inavailabilities=[
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-15"),
                        reason="Travelling with family.",
                    )
                ],
                exemptions=[],
            ),
            McWorker(
                name=fake.full_name(),
                rank=McJobPositions.COOK,
                inavailabilities=[
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-14"),
                        end_date=datetime.fromisoformat("2025-01-20"),
                        reason="Travelling to Burger King.",
                    )
                ],
                exemptions=[],
            ),
            McWorker(
                name=fake.full_name(),
                rank=McJobPositions.COOK,
                inavailabilities=[
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-13"),
                        reason="Long weekend.",
                    ),
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-16"),
                        end_date=datetime.fromisoformat("2025-01-20"),
                        reason="Another long weekend.",
                    ),
                ],
                exemptions=[],
            ),
            McWorker(name=fake.full_name(), rank=McJobPositions.MANAGER, inavailabilities=[], exemptions=[]),
        ]
