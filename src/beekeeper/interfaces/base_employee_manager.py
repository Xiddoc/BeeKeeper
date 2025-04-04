from abc import ABC, abstractmethod

from beekeeper.employees.employee import Employee


class BaseEmployeeManager(ABC):
    """
    This is the BeeKeeper's interface to querying employees and their information.

    .. warning::
        BeeKeeper may cache this information for faster queries later.
        Consider implementing the cache hit function to control this behavior.

    """

    @abstractmethod
    def get_all_employees(self) -> list[Employee]:
        """
        Retrieves the information of all the employees.
        This information might be cached later on.
        """

    # noinspection PyMethodMayBeStatic
    def should_refetch_data(self) -> bool:
        """
        Defines if the Employee information should be refetched.
        By default, this data is cached for performance.
        """
        return False
