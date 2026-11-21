from dataclasses import dataclass

from app.config import ATTENDANCE_THRESHOLD_PERCENT


@dataclass(frozen=True)
class SkipAdvice:
    can_skip: int | None
    reachable: bool
    best_possible_percent: float | None


def _ceil_percent(total: int, percent: int) -> int:
    return -(-total * percent // 100)


def skip_advice(
    held: int, attended: int, planned: int, threshold: int = ATTENDANCE_THRESHOLD_PERCENT
) -> SkipAdvice:
    """Mirror of the can_skip / best_possible_percent columns of the attendance views."""
    total = max(planned, held)
    if total == 0:
        return SkipAdvice(can_skip=None, reachable=True, best_possible_percent=None)
    can_skip = total - _ceil_percent(total, threshold) - (held - attended)
    remaining = max(planned - held, 0)
    best = round((attended + remaining) * 100 / total, 2)
    return SkipAdvice(can_skip=can_skip, reachable=can_skip >= 0, best_possible_percent=best)
