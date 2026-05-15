from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class DateRange[T: date = datetime](BaseModel):
    model_config = ConfigDict(extra="forbid")

    """A date or datetime range, inclusive on both ends.

    Generic over `T: date`, which admits both `date` (whole-day shifts)
    and `datetime` (time-of-day granularity) since `datetime` is a `date`
    subclass. Domain code that wants to be explicit can subclass with a
    concrete parameter, e.g. `class Shift(DateRange[date]): ...`.
    """

    start_date: T
    end_date: T

    @model_validator(mode="after")
    def _validate(self) -> Self:
        # `tzinfo` is the marker for "is this aware?". Plain `date` objects don't
        # have the attribute at all (getattr returns None), so they read as naive
        # — which is the right answer: a `date` carries no tz information.
        # This shape lets us collapse the "both datetimes?" + "tz-consistent?"
        # checks into a single comparison without a dead AND-branch.
        start_aware = getattr(self.start_date, "tzinfo", None) is not None
        end_aware = getattr(self.end_date, "tzinfo", None) is not None
        if start_aware != end_aware:
            msg = "start_date and end_date must both be timezone-naive or both timezone-aware"
            raise ValueError(msg)

        if self.end_date < self.start_date:
            msg = f"end_date ({self.end_date}) must be on or after start_date ({self.start_date})"
            raise ValueError(msg)
        return self

    @property
    def inclusive_day_count(self) -> int:
        """Number of days the entity is on duty, inclusive on both ends.

        A same-day range yields 1 (the entity works that day). A range
        from Jan 5 to Jan 10 yields 6 (Jan 5, 6, 7, 8, 9, 10).
        """
        return (self.end_date - self.start_date).days + 1

    @property
    def days(self) -> int:
        """Elapsed days between start and end, matching stdlib semantics.

        A same-day range yields 0; consecutive days yield 1; Jan 5 to
        Jan 10 yields 5. For the count of *on-duty* days, use
        :attr:`inclusive_day_count`.
        """
        return (self.end_date - self.start_date).days
