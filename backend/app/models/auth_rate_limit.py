"""
Persistent rate limit events for authentication endpoints.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuthRateLimitEvent(Base):
    __tablename__ = "auth_rate_limit_events"
    __table_args__ = (
        Index("ix_auth_rate_limit_bucket_key_created", "bucket", "key", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    bucket: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<AuthRateLimitEvent(bucket={self.bucket}, key={self.key}, created_at={self.created_at})>"