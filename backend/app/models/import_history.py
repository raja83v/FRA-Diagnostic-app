"""
Import History model.

Tracks every file import attempt — success or failure —
with metadata about parsing, validation, and normalization.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, JSON, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class ImportStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    VALIDATING = "validating"
    NORMALIZING = "normalizing"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ImportHistory(Base):
    __tablename__ = "import_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        SAEnum(ImportStatus), default=ImportStatus.PENDING, nullable=False
    )

    # Result references
    measurement_id: Mapped[str | None] = mapped_column(String(36))
    transformer_id: Mapped[str | None] = mapped_column(String(36))

    # Detection / parsing info
    detected_vendor: Mapped[str | None] = mapped_column(String(100))
    detected_format: Mapped[str | None] = mapped_column(String(50))
    parser_used: Mapped[str | None] = mapped_column(String(100))

    # Data stats
    data_points: Mapped[int | None] = mapped_column(Integer)
    frequency_range: Mapped[str | None] = mapped_column(String(200))

    # Errors & warnings
    warnings_json: Mapped[list | None] = mapped_column(JSON)
    errors_json: Mapped[list | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<ImportHistory(id={self.id}, file={self.original_filename}, "
            f"status={self.status})>"
        )
