"""
Database models package.
Import all models here so Alembic and SQLAlchemy can discover them.
"""
from app.models.transformer import Transformer, TransformerCriticality  # noqa: F401
from app.models.measurement import FRAMeasurement, WindingConfig  # noqa: F401
from app.models.fault_analysis import FaultAnalysis, FaultType  # noqa: F401
from app.models.recommendation import (  # noqa: F401
    Recommendation,
    UrgencyLevel,
    RecommendationStatus,
)
from app.models.ml_model import MLModel  # noqa: F401
from app.models.import_history import ImportHistory, ImportStatus  # noqa: F401

__all__ = [
    "Transformer",
    "TransformerCriticality",
    "FRAMeasurement",
    "WindingConfig",
    "FaultAnalysis",
    "FaultType",
    "Recommendation",
    "UrgencyLevel",
    "RecommendationStatus",
    "MLModel",
    "ImportHistory",
    "ImportStatus",
]
