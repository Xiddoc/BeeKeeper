from collections.abc import Iterable
from datetime import datetime

from faker import Faker
from mcdonalds.entities.mcdonalds_employee import McWorker

from beekeeper import EntityInputAdapter, Inavailability

fake = Faker()


class McWorkerEntityInputAdapter(EntityInputAdapter):
    def get_entities(self) -> Iterable[McWorker]:
        return [
            McWorker(
                name=fake.full_name(),
                inavailabilities=[
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-15"),
                        reason="Job interview at Burger King.",
                    )
                ],
            ),
            McWorker(name=fake.full_name(), inavailabilities=[]),
            McWorker(
                name=fake.full_name(),
                inavailabilities=[
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-15"),
                        reason="Travelling with family.",
                    )
                ],
            ),
            McWorker(
                name=fake.full_name(),
                inavailabilities=[
                    Inavailability(
                        start_date=datetime.fromisoformat("2025-01-14"),
                        end_date=datetime.fromisoformat("2025-01-20"),
                        reason="Travelling to Burger King.",
                    )
                ],
            ),
            McWorker(
                name=fake.full_name(),
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
            ),
            McWorker(name=fake.full_name(), inavailabilities=[]),
        ]
