from datetime import date

from app.services.dates import (
    date_ranges_text,
    month_period,
    previous_month_period,
    previous_week_period,
    semester_period,
    week_period,
)


def test_month_boundaries_including_december() -> None:
    assert month_period(date(2026, 11, 11)).start == date(2026, 11, 1)
    assert month_period(date(2026, 11, 11)).end_exclusive == date(2026, 12, 1)
    assert month_period(date(2026, 12, 31)).end_exclusive == date(2027, 1, 1)


def test_last_month_crosses_year() -> None:
    assert previous_month_period(date(2027, 1, 5)).start == date(2026, 12, 1)


def test_week_starts_monday() -> None:
    assert week_period(date(2026, 11, 11)).start == date(2026, 11, 9)
    assert week_period(date(2026, 11, 9)).start == date(2026, 11, 9)
    assert previous_week_period(date(2026, 11, 11)).start == date(2026, 11, 2)


def test_semester_boundaries() -> None:
    assert semester_period(date(2026, 11, 11)).start == date(2026, 7, 1)
    assert semester_period(date(2026, 7, 1)).start == date(2026, 7, 1)
    assert semester_period(date(2026, 6, 30)).start == date(2026, 1, 1)
    assert semester_period(date(2026, 6, 30)).end_exclusive == date(2026, 7, 1)


def test_ranges_text_mentions_all_periods() -> None:
    text = date_ranges_text(date(2026, 11, 11))
    assert "this month = >= '2026-11-01' and < '2026-12-01'" in text
    assert "this semester" in text
