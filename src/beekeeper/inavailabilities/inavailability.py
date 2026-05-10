from datetime import date

from beekeeper.time_constructs.date_range import DateRange


class Inavailability[T: date](DateRange[T]):
    reason: str
