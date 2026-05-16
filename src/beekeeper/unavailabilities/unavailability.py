from datetime import date, datetime

from beekeeper.time_constructs.date_range import DateRange


class Unavailability[T: date = datetime](DateRange[T]):
    """A date range during which an entity isn't available, plus a short reason.

    Extends ``DateRange`` with a free-form ``reason`` string for diagnostics.
    Domains that need richer metadata (paid/unpaid, source system, etc.)
    subclass and add fields.
    """

    reason: str
