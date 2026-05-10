from datetime import date, datetime

from beekeeper.time_constructs.date_range import DateRange


class Inavailability[T: date = datetime](DateRange[T]):
    reason: str
