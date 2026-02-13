"""
ML Model registry model.
Maintains model registry with version information, training date,
performance metrics, and active deployment status.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Training info
    training_date: Mapped[datetime | None] = mapped_column(DateTime)
    training_samples: Mapped[int | None] = mapped_column()
    training_duration_seconds: Mapped[float | None] = mapped_column(Float)

    # Performance metrics (stored as JSON for flexibility)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    # Example: {"accuracy": 0.92, "recall": 0.90, "fpr": 0.08, "auc_roc": 0.93}

    # Individual metric columns for quick querying
    accuracy: Mapped[float | None] = mapped_column(Float)
    recall: Mapped[float | None] = mapped_column(Float)
    false_positive_rate: Mapped[float | None] = mapped_column(Float)
    auc_roc: Mapped[float | None] = mapped_column(Float)

    # Deployment
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    file_path: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"<MLModel(id={self.id}, name={self.name}, version={self.version}, "
            f"active={self.is_active}, accuracy={self.accuracy})>"
        )
