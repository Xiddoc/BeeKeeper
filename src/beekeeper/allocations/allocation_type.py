from typing import TypeVar

from beekeeper.data_structures.abstract_enum import AbstractEnum


class AllocationType(AbstractEnum):
    pass


TAllocationType = TypeVar("TAllocationType", bound=AllocationType)
