"""Simple SM-2 spaced repetition helpers."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.modules.study.models import ReviewRating
from app.modules.study.schemas import SM2State


def apply_sm2_review(
    state: SM2State,
    rating: ReviewRating,
    *,
    now: datetime | None = None,
) -> tuple[SM2State, datetime]:
    """Return updated SM-2 state and next review datetime."""
    now = now or datetime.now(timezone.utc)
    ease = float(state.ease_factor)
    interval = state.interval_days
    repetitions = state.repetitions

    if rating == ReviewRating.AGAIN:
        repetitions = 0
        interval = 1
        ease = max(1.3, ease - 0.2)
    elif rating == ReviewRating.HARD:
        ease = max(1.3, ease - 0.15)
        if repetitions == 0:
            interval = 1
        else:
            interval = max(1, round(interval * 1.2))
        repetitions += 1
    elif rating == ReviewRating.GOOD:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = max(1, round(interval * ease))
        repetitions += 1
    elif rating == ReviewRating.EASY:
        ease = ease + 0.15
        if repetitions == 0:
            interval = 4
        else:
            interval = max(1, round(interval * ease * 1.3))
        repetitions += 1

    next_review = now + timedelta(days=interval)
    new_state = SM2State(
        interval_days=interval,
        ease_factor=Decimal(str(round(ease, 2))),
        repetitions=repetitions,
    )
    return new_state, next_review
