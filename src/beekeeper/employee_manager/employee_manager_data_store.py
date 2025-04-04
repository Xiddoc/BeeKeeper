from typing import Optional

from beekeeper.employees.employee import Employee
from beekeeper.interfaces.base_employee_manager import BaseEmployeeManager


class EmployeeManagerDataStore:
    def __init__(self, employee_manager: BaseEmployeeManager) -> None:
        self.employee_manager = employee_manager
        self._employee_cache: Optional[list[Employee]] = None

    def get_all_employees(self) -> list[Employee]:
        if self._employee_cache is None or self.employee_manager.should_refetch_data():
            return self._forcibly_get_all_employees_and_cache()

        return self._employee_cache

    def _forcibly_get_all_employees_and_cache(self) -> list[Employee]:
        self._employee_cache = self.employee_manager.get_all_employees()
        return self._employee_cache
