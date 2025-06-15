from abc import ABCMeta
from enum import Enum, EnumMeta


class _AbstractEnumMeta(EnumMeta, ABCMeta):
    pass


class AbstractEnum(Enum, metaclass=_AbstractEnumMeta):
    pass
