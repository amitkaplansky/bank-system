from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from ..database import db_manager

logger = logging.getLogger(__name__)

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    database: str
    version: str = "1.0.0"

@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring
    Returns 200 if service is healthy, 503 if unhealthy
    """
    try:
        # Check database connectivity
        db_healthy = await db_manager.health_check()
        
        if not db_healthy:
            raise HTTPException(
                status_code=503, 
                detail={
                    "status": "unhealthy",
                    "database": "down",
                    "version": "1.0.0"
                }
            )
        
        return HealthResponse(
            status="healthy",
            database="up"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy", 
                "database": "error",
                "version": "1.0.0",
                "error": str(e)
            }
        )