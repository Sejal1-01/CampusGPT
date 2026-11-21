from typing import Any

TOLERANCE = 0.01


def _normalise(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return round(float(value), 2)
    text = str(value).strip()
    try:
        return round(float(text), 2)
    except ValueError:
        return text.lower()


def _equal(left: Any, right: Any) -> bool:
    if isinstance(left, float) and isinstance(right, float):
        return abs(left - right) <= TOLERANCE + 1e-9
    return left == right


def _sort_key(value: Any) -> tuple[int, Any]:
    if value is None:
        return (0, 0)
    return (1, value) if isinstance(value, float) else (2, str(value))


def _columns(rows: list[list[Any]]) -> list[list[Any]]:
    if not rows:
        return []
    return [[_normalise(row[index]) for row in rows] for index in range(len(rows[0]))]


def _same(left: list[Any], right: list[Any], ordered: bool) -> bool:
    if len(left) != len(right):
        return False
    if not ordered:
        left, right = sorted(left, key=_sort_key), sorted(right, key=_sort_key)
    return all(_equal(a, b) for a, b in zip(left, right, strict=True))


def _match_columns(gold: list[list[Any]], generated: list[list[Any]], ordered: bool) -> bool:
    used: set[int] = set()
    for gold_column in gold:
        found = next(
            (
                index
                for index, column in enumerate(generated)
                if index not in used and _same(gold_column, column, ordered)
            ),
            None,
        )
        if found is None:
            return False
        used.add(found)
    return True


def results_match(
    gold_rows: list[list[Any]], generated_rows: list[list[Any]], ordered: bool
) -> bool:
    """Execution match: every gold column appears among the generated columns (extra columns allowed)."""
    if not gold_rows:
        return not generated_rows
    if len(gold_rows) == 1 and len(generated_rows) > 1:
        return _match_columns(_columns(gold_rows), _columns(generated_rows[:1]), True)
    if len(gold_rows) != len(generated_rows):
        return False
    return _match_columns(_columns(gold_rows), _columns(generated_rows), ordered)
