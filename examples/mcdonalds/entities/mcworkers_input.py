from collections.abc import Iterable
from datetime import datetime

from faker import Faker
from mcdonalds.entities.entity_properties import McDonaldsInavailability, McJobPosition
from mcdonalds.entities.mcdonalds_employee import McWorker

from beekeeper import Entity, EntityInputAdapter

fake = Faker()


class McWorkerEntityInputAdapter(EntityInputAdapter):
    def get_entities(self) -> Iterable[McWorker]:
        return [
            McWorker(
                name=fake.full_name(),
                rank=McJobPosition.CASHIER,
                inavailabilities=[
                    McDonaldsInavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-15"),
                        reason="Job interview at Burger King.",
                        is_paid_leave=False,
                    )
                ],
            ),
            McWorker(name=fake.full_name(), rank=McJobPosition.CASHIER, inavailabilities=[]),
            McWorker(
                name=fake.full_name(),
                rank=McJobPosition.COOK,
                inavailabilities=[
                    McDonaldsInavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-15"),
                        reason="Travelling with family.",
                        is_paid_leave=True,
                    )
                ],
            ),
            McWorker(
                name=fake.full_name(),
                rank=McJobPosition.COOK,
                inavailabilities=[
                    McDonaldsInavailability(
                        start_date=datetime.fromisoformat("2025-01-14"),
                        end_date=datetime.fromisoformat("2025-01-20"),
                        reason="Travelling to Burger King.",
                        is_paid_leave=False,
                    )
                ],
            ),
            McWorker(
                name=fake.full_name(),
                rank=McJobPosition.COOK,
                inavailabilities=[
                    McDonaldsInavailability(
                        start_date=datetime.fromisoformat("2025-01-10"),
                        end_date=datetime.fromisoformat("2025-01-13"),
                        reason="Long weekend.",
                        is_paid_leave=True,
                    ),
                    McDonaldsInavailability(
                        start_date=datetime.fromisoformat("2025-01-16"),
                        end_date=datetime.fromisoformat("2025-01-20"),
                        reason="Another long weekend.",
                        is_paid_leave=True,
                    ),
                ],
            ),
            McWorker(name=fake.full_name(), rank=McJobPosition.MANAGER, inavailabilities=[]),
        ]
