from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from beekeeper import DateRange


def test_inclusive_day_count_for_same_day() -> None:
    same_day = DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=UTC),
        end_date=datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert same_day.inclusive_day_count == 1


def test_inclusive_day_count_for_full_span() -> None:
    span = DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=UTC),
        end_date=datetime(2025, 1, 5, tzinfo=UTC),
    )
    assert span.inclusive_day_count == 5


def test_inclusive_day_count_counts_every_calendar_day_for_midnight_straddle() -> None:
    """
    A datetime range that crosses midnight by minutes still counts the calendar days it touches.

    Regression: ``timedelta.days`` on a ``datetime`` subtraction truncates
    the sub-day remainder, so ``Jan 5 23:59 → Jan 7 00:01`` used to return
    2. The on-duty reading is 3 (Jan 5, 6, 7).
    """
    span = DateRange(
        start_date=datetime(2025, 1, 5, 23, 59, tzinfo=UTC),
        end_date=datetime(2025, 1, 7, 0, 1, tzinfo=UTC),
    )
    assert span.inclusive_day_count == 3


def test_days_uses_stdlib_semantics() -> None:
    same_day = DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=UTC),
        end_date=datetime(2025, 1, 1, tzinfo=UTC),
    )
    span = DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=UTC),
        end_date=datetime(2025, 1, 5, tzinfo=UTC),
    )
    assert same_day.days == 0
    assert span.days == 4


def test_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="end_date.*must be on or after start_date"):
        DateRange(
            start_date=datetime(2025, 1, 5, tzinfo=UTC),
            end_date=datetime(2025, 1, 1, tzinfo=UTC),
        )


def test_rejects_mixed_timezone_awareness() -> None:
    with pytest.raises(ValueError, match="must share the same tzinfo"):
        DateRange(
            start_date=datetime(2025, 1, 1, tzinfo=UTC),
            end_date=datetime(2025, 1, 5),  # noqa: DTZ001 — intentionally naive for the mixed-tz test
        )


def test_rejects_mixed_aware_timezones() -> None:
    """
    Two aware datetimes with different tzinfo objects are rejected.

    Both endpoints being timezone-aware isn't enough — they must share
    the same tzinfo, otherwise the range's duration is ambiguous.
    """
    with pytest.raises(ValueError, match="must share the same tzinfo"):
        DateRange(
            start_date=datetime(2025, 1, 1, tzinfo=ZoneInfo("America/New_York")),
            end_date=datetime(2025, 1, 5, tzinfo=ZoneInfo("Asia/Tokyo")),
        )


def test_accepts_matching_aware_timezones() -> None:
    """Two aware datetimes with equal-but-distinct tzinfo instances pass."""
    span = DateRange(
        start_date=datetime(2025, 1, 1, tzinfo=ZoneInfo("America/New_York")),
        end_date=datetime(2025, 1, 5, tzinfo=ZoneInfo("America/New_York")),
    )
    assert span.inclusive_day_count == 5


def test_accepts_plain_date_range() -> None:
    span: DateRange[date] = DateRange(start_date=date(2025, 1, 1), end_date=date(2025, 1, 7))
    assert span.inclusive_day_count == 7
    assert span.days == 6
