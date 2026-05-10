from datetime import datetime

from beekeeper import Inavailability
from beekeeper.data_structures.abstract_enum import AbstractEnum


class Rank(AbstractEnum):
    pass


class McJobPosition(Rank):
    CASHIER = "CASHIER"
    COOK = "COOK"
    MANAGER = "MANAGER"


class McDonaldsInavailability(Inavailability[datetime]):
    is_paid_leave: bool
