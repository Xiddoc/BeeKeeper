from uuid import uuid4

from pydantic import BaseModel, Field

from beekeeper.employees.extra_employee_info import ExtraEmployeeInfo


class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str

    extra_info: ExtraEmployeeInfo = Field(default_factory=ExtraEmployeeInfo)
