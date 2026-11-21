import pytest

from app.services.attendance import skip_advice


@pytest.mark.parametrize(
    ("held", "attended", "planned", "can_skip", "best"),
    [
        (40, 40, 60, 15, 100.0),
        (40, 35, 60, 10, 91.67),
        (40, 30, 60, 5, 83.33),
        (48, 30, 60, -3, 70.0),
        (0, 0, 60, 15, 100.0),
        (60, 45, 60, 0, 75.0),
    ],
)
def test_skip_formula(held: int, attended: int, planned: int, can_skip: int, best: float) -> None:
    advice = skip_advice(held, attended, planned)
    assert advice.can_skip == can_skip
    assert advice.best_possible_percent == best
    assert advice.reachable is (can_skip >= 0)


def test_unreachable_reports_best_percent() -> None:
    advice = skip_advice(held=48, attended=30, planned=60)
    assert advice.reachable is False
    assert advice.best_possible_percent == 70.0


def test_planned_zero_does_not_divide_by_zero() -> None:
    advice = skip_advice(held=0, attended=0, planned=0)
    assert advice.can_skip is None
    assert advice.best_possible_percent is None


def test_held_more_than_planned_uses_held_as_total() -> None:
    advice = skip_advice(held=62, attended=50, planned=60)
    assert advice.can_skip == 62 - 47 - 12
    assert advice.best_possible_percent == round(50 * 100 / 62, 2)
