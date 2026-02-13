"""
FRA Diagnostic Software - Main Application Entry Point

AI-Driven Frequency Response Analysis for Transformer Diagnostics
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import transformers, measurements, analysis, recommendations
from app.routers import imports as imports_router

# Create all tables (for development; production uses Alembic migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered diagnostic software for analyzing Frequency Response Analysis (FRA) "
        "data from power transformers. Supports multi-vendor data import, ML-based fault "
        "detection, interactive visualization, and maintenance recommendations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(transformers.router)
app.include_router(measurements.router)
app.include_router(analysis.router)
app.include_router(recommendations.router)
app.include_router(imports_router.router)


@app.get("/", tags=["Root"])
def root():
    """Health check / root endpoint."""
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Root"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
