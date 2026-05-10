from datetime import UTC, datetime

from beekeeper import DateRange


def test_daterange_days_is_inclusive_for_same_day() -> None:
    same_day = DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=UTC),
        end_date=datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert same_day.days == 1


def test_daterange_days_counts_full_span() -> None:
    span = DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=UTC),
        end_date=datetime(2025, 1, 5, tzinfo=UTC),
    )
    assert span.days == 5
