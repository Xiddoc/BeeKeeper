from abc import ABCMeta
from enum import Enum, EnumMeta


class AbstractEnumMeta(EnumMeta, ABCMeta):
    pass


class AbstractEnum(Enum, metaclass=AbstractEnumMeta):
    pass
