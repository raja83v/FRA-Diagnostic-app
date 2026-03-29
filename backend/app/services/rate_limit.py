"""
Database-backed rate limiting helpers for authentication endpoints.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.auth_rate_limit import AuthRateLimitEvent


def check_rate_limit(
    db: Session,
    *,
    bucket: str,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    """Persist and enforce a sliding-window limit using the shared database."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=window_seconds)

    (
        db.query(AuthRateLimitEvent)
        .filter(AuthRateLimitEvent.bucket == bucket)
        .filter(AuthRateLimitEvent.key == key)
        .filter(AuthRateLimitEvent.created_at < window_start)
        .delete(synchronize_session=False)
    )

    attempts = (
        db.query(func.count(AuthRateLimitEvent.id))
        .filter(AuthRateLimitEvent.bucket == bucket)
        .filter(AuthRateLimitEvent.key == key)
        .filter(AuthRateLimitEvent.created_at >= window_start)
        .scalar()
    )

    if attempts >= limit:
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait and try again.",
        )

    db.add(AuthRateLimitEvent(bucket=bucket, key=key, created_at=now))
    db.commit()