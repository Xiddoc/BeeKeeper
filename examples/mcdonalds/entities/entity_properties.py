from datetime import datetime

from beekeeper import Unavailability
from beekeeper.data_structures.abstract_enum import AbstractEnum


class Rank(AbstractEnum):
    pass


class McJobPosition(Rank):
    CASHIER = "CASHIER"
    COOK = "COOK"
    MANAGER = "MANAGER"


class McDonaldsUnavailability(Unavailability[datetime]):
    is_paid_leave: bool
