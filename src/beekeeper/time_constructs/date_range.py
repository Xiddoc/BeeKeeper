from datetime import datetime

from pydantic import BaseModel


class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime

    @property
    def days(self) -> int:
        """
        This counts the amount of days where you are ACTIVE on duty.
        For example, a start and end date which are the same day will result in 1.
        """
        return (self.end_date - self.start_date).days + 1
