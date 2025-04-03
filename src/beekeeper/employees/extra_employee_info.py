from pydantic import BaseModel


class ExtraEmployeeInfo(BaseModel):
    """
    Long-lasting properties of an employee, that are unlikely to change.
    First name, last name, ID, personal ID (SSN), etc.

    This information is useless to the core algorithm itself.
    All attributes must be pydantic-validated, as noted with the BaseModel inheritance above.
    """
