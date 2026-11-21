from dataclasses import dataclass
from datetime import date, timedelta

ODD_TERM_START_MONTH = 7
EVEN_TERM_START_MONTH = 1
TERM_LENGTH_MONTHS = 6


@dataclass(frozen=True)
class Period:
    start: date
    end_exclusive: date


def month_period(today: date) -> Period:
    start = today.replace(day=1)
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    return Period(start, end)


def previous_month_period(today: date) -> Period:
    return month_period(month_period(today).start - timedelta(days=1))


def week_period(today: date) -> Period:
    start = today - timedelta(days=today.weekday())
    return Period(start, start + timedelta(days=7))


def previous_week_period(today: date) -> Period:
    return week_period(today - timedelta(days=7))


def semester_period(today: date) -> Period:
    if today.month >= ODD_TERM_START_MONTH:
        return Period(date(today.year, ODD_TERM_START_MONTH, 1), date(today.year + 1, 1, 1))
    return Period(
        date(today.year, EVEN_TERM_START_MONTH, 1), date(today.year, ODD_TERM_START_MONTH, 1)
    )


def date_ranges_text(today: date) -> str:
    named = {
        "this week": week_period(today),
        "last week": previous_week_period(today),
        "this month": month_period(today),
        "last month": previous_month_period(today),
        "this semester": semester_period(today),
    }
    return "; ".join(
        f"{label} = >= '{period.start}' and < '{period.end_exclusive}'"
        for label, period in named.items()
    )
