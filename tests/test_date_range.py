from datetime import UTC, date, datetime

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
    with pytest.raises(ValueError, match="timezone-naive or both timezone-aware"):
        DateRange(
            start_date=datetime(2025, 1, 1, tzinfo=UTC),
            end_date=datetime(2025, 1, 5),  # noqa: DTZ001 — intentionally naive for the mixed-tz test
        )


def test_accepts_plain_date_range() -> None:
    span: DateRange[date] = DateRange(start_date=date(2025, 1, 1), end_date=date(2025, 1, 7))
    assert span.inclusive_day_count == 7
    assert span.days == 6
