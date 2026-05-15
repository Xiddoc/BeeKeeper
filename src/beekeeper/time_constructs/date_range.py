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
        # Plain ``date`` has no ``tzinfo`` attribute, so ``getattr`` defaults
        # to ``None`` on both sides and the comparison passes. For aware
        # datetimes, the tzinfo objects themselves must compare equal — not
        # merely "both non-None" — otherwise a range mixing e.g. US/Eastern
        # and Asia/Tokyo would slip through with an ambiguous duration.
        start_tz = getattr(self.start_date, "tzinfo", None)
        end_tz = getattr(self.end_date, "tzinfo", None)
        if start_tz != end_tz:
            msg = f"start_date and end_date must share the same tzinfo (got start={start_tz!r}, end={end_tz!r})"
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

        Computed on the calendar-day component so that datetime ranges
        which straddle midnight count every calendar day they touch.
        For example, ``2025-01-05 23:59`` → ``2025-01-07 00:01`` yields
        3 (Jan 5, 6, 7), not 2 (which is what ``timedelta.days`` would
        truncate to after subtracting the sub-day remainder).
        """
        start = self.start_date.date() if isinstance(self.start_date, datetime) else self.start_date
        end = self.end_date.date() if isinstance(self.end_date, datetime) else self.end_date
        return (end - start).days + 1

    @property
    def days(self) -> int:
        """Elapsed days between start and end, matching stdlib semantics.

        A same-day range yields 0; consecutive days yield 1; Jan 5 to
        Jan 10 yields 5. For the count of *on-duty* days, use
        :attr:`inclusive_day_count`.
        """
        return (self.end_date - self.start_date).days
