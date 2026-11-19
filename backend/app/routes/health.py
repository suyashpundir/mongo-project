from fastapi import APIRouter
from app.database import db_manager
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """System health check and diagnostic status."""
    is_db_connected = False
    if db_manager.client:
        try:
            await db_manager.client.admin.command('ping')
            is_db_connected = True
        except Exception:
            is_db_connected = False

    return {
        "status": "healthy" if is_db_connected else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_connected": is_db_connected,
        "atlas_vector_search_ready": db_manager.is_atlas_vector_search_ready,
        "ai_engine": "Gemini API" if settings.GEMINI_API_KEY else "Local Semantic Vectorizer"
    }
