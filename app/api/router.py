"""Central API router."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.analysis import router as analysis_router

api_router = APIRouter()

api_router.include_router(analysis_router, prefix="/analyze", tags=["Analysis"])


@api_router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    }
