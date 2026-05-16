from beekeeper.data_structures.abstract_enum import AbstractEnum


class AllocationType(AbstractEnum):
    """Empty placeholder enum — domains extend it with their own task vocabulary.

    Subclass and add members representing the kinds of allocation a request
    can carry::

        class McAllocType(AllocationType):
            COOKING = "COOKING"
            SERVING_FOOD = "SERVING_FOOD"
    """
